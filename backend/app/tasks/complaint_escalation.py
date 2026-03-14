"""
Celery Task - Complaint Auto-Escalation

Implements automatic complaint escalation after 48 hours of being unresolved.
Validates Requirement 4.6: Auto-escalation to next admin level after 48 hours.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.worker import celery_app
from app.core.database import SessionLocal
from app.models.models import Complaint, ComplaintStatus, ComplaintEscalationLog


@celery_app.task(name="escalate_unresolved_complaints")
def escalate_unresolved_complaints():
    """
    Celery task to check and escalate unresolved complaints after 48 hours.
    
    Escalation levels:
    - Level 1 (Vendor) → Level 2 (Regional Admin) after 48h
    - Level 2 (Regional Admin) → Level 3 (Super Admin) after another 48h
    
    Only escalates complaints that are not resolved or closed.
    """
    db: Session = SessionLocal()
    escalated_count = 0
    
    try:
        # 48-hour threshold for escalation
        escalation_threshold = datetime.utcnow() - timedelta(hours=48)
        
        # Find complaints that need escalation
        # Exclude resolved and closed complaints
        complaints_to_check = db.query(Complaint).filter(
            Complaint.status.not_in([
                ComplaintStatus.RESOLVED_PENDING_CUSTOMER,
                ComplaintStatus.CLOSED
            ]),
            Complaint.escalation_level < 3  # Max level is 3 (Super Admin)
        ).all()
        
        for complaint in complaints_to_check:
            # Determine the time to check against
            # If there's a previous escalation, check from that time
            # Otherwise, check from creation time
            last_escalation_log = db.query(ComplaintEscalationLog).filter(
                ComplaintEscalationLog.complaint_id == complaint.id
            ).order_by(ComplaintEscalationLog.escalated_at.desc()).first()
            
            reference_time = (
                last_escalation_log.escalated_at 
                if last_escalation_log 
                else complaint.created_at
            )
            
            # Check if 48 hours have passed since reference time
            if reference_time <= escalation_threshold:
                old_level = complaint.escalation_level
                new_level = old_level + 1
                
                # Update complaint escalation level
                complaint.escalation_level = new_level
                
                # Update status based on new level
                if new_level == 2:
                    complaint.status = ComplaintStatus.ESCALATED_TO_REGIONAL
                    reason = "Auto-escalated to Regional Admin after 48 hours without resolution"
                elif new_level == 3:
                    complaint.status = ComplaintStatus.ESCALATED_TO_SUPER
                    reason = "Auto-escalated to Super Admin after 48 hours without resolution"
                else:
                    reason = f"Auto-escalated to level {new_level} after 48 hours without resolution"
                
                # Create escalation log entry
                escalation_log = ComplaintEscalationLog(
                    complaint_id=complaint.id,
                    from_level=old_level,
                    to_level=new_level,
                    reason=reason
                )
                db.add(escalation_log)
                
                escalated_count += 1
                
                # TODO: Send notification to appropriate admin level
                # This would integrate with a notification service
        
        # Commit all changes
        db.commit()
        
        return {
            "success": True,
            "escalated_count": escalated_count,
            "message": f"Successfully escalated {escalated_count} complaint(s)"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": f"Error during complaint escalation: {str(e)}"
        }
    finally:
        db.close()


@celery_app.task(name="check_complaint_escalation_status")
def check_complaint_escalation_status(complaint_id: int):
    """
    Check if a specific complaint needs escalation.
    Can be called on-demand for immediate checking.
    
    Args:
        complaint_id: The ID of the complaint to check
        
    Returns:
        dict: Status information about the complaint
    """
    db: Session = SessionLocal()
    
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        
        if not complaint:
            return {
                "success": False,
                "message": f"Complaint {complaint_id} not found"
            }
        
        # Check if complaint is already resolved or closed
        if complaint.status in [ComplaintStatus.RESOLVED_PENDING_CUSTOMER, ComplaintStatus.CLOSED]:
            return {
                "success": True,
                "needs_escalation": False,
                "message": "Complaint is already resolved or closed"
            }
        
        # Check if already at max escalation level
        if complaint.escalation_level >= 3:
            return {
                "success": True,
                "needs_escalation": False,
                "message": "Complaint is already at maximum escalation level"
            }
        
        # Calculate time since last escalation or creation
        last_escalation_log = db.query(ComplaintEscalationLog).filter(
            ComplaintEscalationLog.complaint_id == complaint.id
        ).order_by(ComplaintEscalationLog.escalated_at.desc()).first()
        
        reference_time = (
            last_escalation_log.escalated_at 
            if last_escalation_log 
            else complaint.created_at
        )
        
        time_elapsed = datetime.utcnow() - reference_time
        hours_elapsed = time_elapsed.total_seconds() / 3600
        
        needs_escalation = hours_elapsed >= 48
        
        return {
            "success": True,
            "complaint_id": complaint_id,
            "current_level": complaint.escalation_level,
            "status": complaint.status.value,
            "hours_elapsed": round(hours_elapsed, 2),
            "needs_escalation": needs_escalation,
            "hours_until_escalation": max(0, 48 - hours_elapsed) if not needs_escalation else 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error checking complaint status: {str(e)}"
        }
    finally:
        db.close()

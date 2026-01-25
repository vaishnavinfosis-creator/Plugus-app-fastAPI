"""
Background Tasks - Complaint Escalation
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Complaint, ComplaintStatus, ComplaintEscalationLog


def escalate_complaints():
    """
    Background task to escalate complaints after 24 hours.
    Level 1 (Vendor) → Level 2 (Regional Admin) → Level 3 (Super Admin)
    """
    db: Session = SessionLocal()
    try:
        escalation_threshold = datetime.utcnow() - timedelta(hours=24)
        
        # Find complaints that need escalation
        complaints_to_escalate = db.query(Complaint).filter(
            Complaint.status.not_in([
                ComplaintStatus.RESOLVED_PENDING_CUSTOMER,
                ComplaintStatus.CLOSED
            ]),
            Complaint.escalation_level < 3,
            Complaint.created_at <= escalation_threshold
        ).all()
        
        for complaint in complaints_to_escalate:
            # Check if last escalation was more than 24h ago
            last_log = db.query(ComplaintEscalationLog).filter(
                ComplaintEscalationLog.complaint_id == complaint.id
            ).order_by(ComplaintEscalationLog.escalated_at.desc()).first()
            
            threshold_time = last_log.escalated_at if last_log else complaint.created_at
            
            if threshold_time <= escalation_threshold:
                old_level = complaint.escalation_level
                new_level = old_level + 1
                
                # Update complaint
                complaint.escalation_level = new_level
                
                # Update status
                if new_level == 2:
                    complaint.status = ComplaintStatus.ESCALATED_TO_REGIONAL
                elif new_level == 3:
                    complaint.status = ComplaintStatus.ESCALATED_TO_SUPER
                
                # Log escalation
                log = ComplaintEscalationLog(
                    complaint_id=complaint.id,
                    from_level=old_level,
                    to_level=new_level,
                    reason="Auto-escalated after 24 hours without resolution"
                )
                db.add(log)
        
        db.commit()
        print(f"Escalated {len(complaints_to_escalate)} complaints")
        
    except Exception as e:
        print(f"Error in complaint escalation: {e}")
        db.rollback()
    finally:
        db.close()


async def run_escalation_task():
    """Run escalation task (to be called periodically)"""
    escalate_complaints()

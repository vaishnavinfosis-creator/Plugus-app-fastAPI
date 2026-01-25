from datetime import datetime, timedelta
from app.worker import celery_app
from app.core.database import SessionLocal
from app import models

@celery_app.task
def escalate_complaints():
    db = SessionLocal()
    try:
        # Escalate OPEN to REGIONAL after 24h
        time_threshold = datetime.utcnow() - timedelta(hours=24)
        open_complaints = db.query(models.Complaint).filter(
            models.Complaint.status == models.ComplaintStatus.OPEN,
            models.Complaint.created_at < time_threshold
        ).all()
        
        for complaint in open_complaints:
            complaint.status = models.ComplaintStatus.ESCALATED_TO_REGIONAL
            log = models.ComplaintEscalationLog(
                complaint_id=complaint.id,
                action="Auto-escalated to Regional Admin"
            )
            db.add(log)
            db.add(complaint)
        
        # Escalate REGIONAL to SUPER after another 24h (total 48h from creation or 24h from escalation?)
        # Prompt says "ESCALATED_TO_REGIONAL (24h auto) -> ESCALATED_TO_SUPER (24h auto)"
        # Assuming 24h after it became REGIONAL.
        # But we don't track when it changed status easily without querying logs.
        # For simplicity, let's say if created > 48h and still REGIONAL.
        
        time_threshold_super = datetime.utcnow() - timedelta(hours=48)
        regional_complaints = db.query(models.Complaint).filter(
            models.Complaint.status == models.ComplaintStatus.ESCALATED_TO_REGIONAL,
            models.Complaint.created_at < time_threshold_super
        ).all()
        
        for complaint in regional_complaints:
            complaint.status = models.ComplaintStatus.ESCALATED_TO_SUPER
            log = models.ComplaintEscalationLog(
                complaint_id=complaint.id,
                action="Auto-escalated to Super Admin"
            )
            db.add(log)
            db.add(complaint)

        db.commit()
    finally:
        db.close()

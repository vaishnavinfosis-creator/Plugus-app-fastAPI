from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core.database import get_db

router = APIRouter()

@router.post("/complaints", response_model=schemas.Complaint)
def create_complaint(
    *,
    db: Session = Depends(get_db),
    complaint_in: schemas.ComplaintCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a complaint.
    """
    booking = db.query(models.Booking).filter(models.Booking.id == complaint_in.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check permissions
    if current_user.role == models.UserRole.CUSTOMER and booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your booking")
    # Add vendor check logic if needed
    
    complaint = models.Complaint(
        booking_id=complaint_in.booking_id,
        description=complaint_in.description,
        status=models.ComplaintStatus.OPEN
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint

@router.put("/complaints/{complaint_id}/resolve", response_model=schemas.Complaint)
def resolve_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Resolve a complaint. Only Customer can close it finally.
    """
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if current_user.role == models.UserRole.CUSTOMER:
         # Customer can close it
         complaint.status = models.ComplaintStatus.CLOSED
    else:
        # Others can mark as resolved pending customer
        complaint.status = models.ComplaintStatus.RESOLVED_PENDING_CUSTOMER
        
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint

from typing import Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core.database import get_db

router = APIRouter()


def send_complaint_notification(complaint_id: int, admin_role: models.UserRole, db: Session):
    """
    Send notification to admins about new complaint.
    This is a placeholder for actual notification service integration.
    In production, this would integrate with email/SMS/push notification service.
    """
    # TODO: Integrate with actual notification service (email, SMS, push notifications)
    # For now, we'll just log the notification
    print(f"Notification: New complaint {complaint_id} assigned to {admin_role}")


@router.post("/", response_model=schemas.ComplaintResponse)
def create_complaint(
    *,
    db: Session = Depends(get_db),
    complaint_in: schemas.ComplaintCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Create a complaint with PENDING status and notify appropriate admins.
    Requirements: 4.1, 4.2, 4.3
    """
    booking = db.query(models.Booking).filter(models.Booking.id == complaint_in.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check permissions - only customer or vendor related to booking can create complaint
    if current_user.role == models.UserRole.CUSTOMER and booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your booking")
    
    if current_user.role == models.UserRole.VENDOR:
        # Check if vendor owns the service
        service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
        if not service or service.vendor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your booking")
    
    # Create complaint with PENDING status (using OPEN as PENDING equivalent)
    complaint = models.Complaint(
        booking_id=complaint_in.booking_id,
        description=complaint_in.description,
        status=models.ComplaintStatus.OPEN,
        escalation_level=1
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    
    # Schedule notification to appropriate admin (vendor first, then regional)
    background_tasks.add_task(send_complaint_notification, complaint.id, models.UserRole.VENDOR, db)
    
    return complaint


@router.get("/", response_model=List[schemas.ComplaintResponse])
def get_user_complaints(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get list of complaints for the current user.
    - Customers see their own complaints
    - Vendors see complaints for their services
    - Admins see all complaints
    Requirements: 4.4
    """
    query = db.query(models.Complaint)
    
    if current_user.role == models.UserRole.CUSTOMER:
        # Get complaints for bookings made by this customer
        query = query.join(models.Booking).filter(models.Booking.customer_id == current_user.id)
    
    elif current_user.role == models.UserRole.VENDOR:
        # Get complaints for bookings of services owned by this vendor
        query = query.join(models.Booking).join(models.Service).filter(
            models.Service.vendor_id == current_user.id
        )
    
    elif current_user.role in [models.UserRole.REGIONAL_ADMIN, models.UserRole.SUPER_ADMIN]:
        # Admins see all complaints (could be filtered by region for regional admins)
        pass
    
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view complaints")
    
    complaints = query.order_by(models.Complaint.created_at.desc()).offset(skip).limit(limit).all()
    return complaints


@router.put("/{complaint_id}/resolve", response_model=schemas.ComplaintResponse)
def resolve_complaint(
    complaint_id: int,
    resolution_notes: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks = None,
) -> Any:
    """
    Resolve a complaint (admin action) or close it (customer action).
    - Admins can mark as RESOLVED_PENDING_CUSTOMER with resolution notes
    - Customers can close their own complaints
    Requirements: 4.5
    """
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Get booking to check permissions
    booking = db.query(models.Booking).filter(models.Booking.id == complaint.booking_id).first()
    
    if current_user.role == models.UserRole.CUSTOMER:
        # Customer can only close their own complaints
        if booking.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your complaint")
        complaint.status = models.ComplaintStatus.CLOSED
        complaint.closed_at = datetime.utcnow()
    
    elif current_user.role in [models.UserRole.VENDOR, models.UserRole.REGIONAL_ADMIN, models.UserRole.SUPER_ADMIN]:
        # Admins can mark as resolved
        complaint.status = models.ComplaintStatus.RESOLVED_PENDING_CUSTOMER
        complaint.resolved_at = datetime.utcnow()
        if resolution_notes:
            complaint.resolution_notes = resolution_notes
        
        # Notify complainant about resolution
        if background_tasks:
            background_tasks.add_task(
                send_complaint_notification, 
                complaint.id, 
                models.UserRole.CUSTOMER, 
                db
            )
    else:
        raise HTTPException(status_code=403, detail="Not authorized to resolve complaints")
    
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint

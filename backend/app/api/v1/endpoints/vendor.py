"""
Vendor API Endpoints
"""
from datetime import datetime, timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.state_machine import BookingStateMachine
from app.models.models import (
    User, UserRole, Vendor, Service, Worker, Booking, BookingStatus,
    BookingStatusHistory, Complaint, Category
)
from app.schemas.schemas import (
    ServiceCreate, ServiceResponse, WorkerCreate, WorkerResponse,
    BookingResponse, BookingDetailResponse, BookingStatusUpdate,
    VendorResponse, RevenueResponse, ComplaintResponse
)
from app.api.deps import get_current_active_user, require_vendor

router = APIRouter()


# ==================== SERVICES ====================

@router.get("/services", response_model=List[ServiceResponse])
def get_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Get vendor's services"""
    vendor = current_user.vendor_profile
    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor profile not found")
    
    return vendor.services


@router.post("/services", response_model=ServiceResponse)
def create_service(
    service_in: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Create new service"""
    vendor = current_user.vendor_profile
    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor profile not found")
    
    # Validate category_id is provided and not null
    if not service_in.category_id:
        raise HTTPException(status_code=400, detail="Category selection is required before creating a service")
    
    # Verify category exists
    category = db.query(Category).filter(Category.id == service_in.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Selected category does not exist")
    
    service = Service(
        vendor_id=vendor.id,
        **service_in.model_dump()
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Delete service"""
    vendor = current_user.vendor_profile
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.vendor_id == vendor.id
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check for active bookings
    active_bookings = db.query(Booking).filter(
        Booking.service_id == service_id,
        Booking.status.not_in([BookingStatus.COMPLETED, BookingStatus.PAYMENT_UPLOADED, BookingStatus.CANCELLED])
    ).count()
    
    if active_bookings > 0:
        raise HTTPException(status_code=400, detail="Cannot delete service with active bookings")
    
    db.delete(service)
    db.commit()
    return {"message": "Service deleted"}


# ==================== WORKERS ====================

@router.get("/workers", response_model=List[WorkerResponse])
def get_workers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Get vendor's workers"""
    vendor = current_user.vendor_profile
    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor profile not found")
    
    return vendor.workers


@router.post("/workers", response_model=WorkerResponse)
def create_worker(
    worker_in: WorkerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Create worker with login credentials"""
    vendor = current_user.vendor_profile
    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor profile not found")
    
    # Check email exists
    existing = db.query(User).filter(User.email == worker_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=worker_in.email,
        hashed_password=get_password_hash(worker_in.password),
        full_name=worker_in.full_name,
        role=UserRole.WORKER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create worker profile
    worker = Worker(
        user_id=user.id,
        vendor_id=vendor.id,
        is_available=True
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


@router.delete("/workers/{worker_id}")
def delete_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Delete worker"""
    vendor = current_user.vendor_profile
    worker = db.query(Worker).filter(
        Worker.id == worker_id,
        Worker.vendor_id == vendor.id
    ).first()
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Check for active tasks
    active_tasks = db.query(Booking).filter(
        Booking.worker_id == worker_id,
        Booking.status.not_in([BookingStatus.COMPLETED, BookingStatus.PAYMENT_UPLOADED, BookingStatus.CANCELLED])
    ).count()
    
    if active_tasks > 0:
        raise HTTPException(status_code=400, detail="Cannot delete worker with active tasks")
    
    # Deactivate user account
    worker.user.is_active = False
    db.commit()
    return {"message": "Worker removed"}


# ==================== ORDERS ====================

@router.get("/orders", response_model=List[BookingResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Get vendor's orders"""
    vendor = current_user.vendor_profile
    if not vendor:
        return []
    
    service_ids = [s.id for s in vendor.services]
    bookings = db.query(Booking).filter(
        Booking.service_id.in_(service_ids)
    ).order_by(Booking.created_at.desc()).all()
    
    return bookings


@router.put("/orders/{booking_id}/accept")
def accept_order(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Accept order"""
    vendor = current_user.vendor_profile
    booking = db.query(Booking).join(Service).filter(
        Booking.id == booking_id,
        Service.vendor_id == vendor.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Validate transition
    is_valid, error = BookingStateMachine.validate_transition(
        booking.status, BookingStatus.VENDOR_ACCEPTED, current_user.role
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    old_status = booking.status
    booking.status = BookingStatus.VENDOR_ACCEPTED
    booking.accepted_at = datetime.utcnow()
    
    # Log status change
    history = BookingStatusHistory(
        booking_id=booking.id,
        old_status=old_status,
        new_status=BookingStatus.VENDOR_ACCEPTED,
        changed_by=current_user.id
    )
    db.add(history)
    db.commit()
    
    return {"message": "Order accepted"}


@router.put("/orders/{booking_id}/assign-worker")
def assign_worker(
    booking_id: int,
    worker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Assign worker to order"""
    vendor = current_user.vendor_profile
    
    # Verify booking belongs to vendor
    booking = db.query(Booking).join(Service).filter(
        Booking.id == booking_id,
        Service.vendor_id == vendor.id
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify worker belongs to vendor
    worker = db.query(Worker).filter(
        Worker.id == worker_id,
        Worker.vendor_id == vendor.id
    ).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Validate transition
    is_valid, error = BookingStateMachine.validate_transition(
        booking.status, BookingStatus.WORKER_ASSIGNED, current_user.role
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    old_status = booking.status
    booking.status = BookingStatus.WORKER_ASSIGNED
    booking.worker_id = worker_id
    
    history = BookingStatusHistory(
        booking_id=booking.id,
        old_status=old_status,
        new_status=BookingStatus.WORKER_ASSIGNED,
        changed_by=current_user.id
    )
    db.add(history)
    db.commit()
    
    return {"message": "Worker assigned"}


# ==================== REVENUE ====================

@router.get("/revenue", response_model=RevenueResponse)
def get_revenue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Get vendor revenue analytics"""
    vendor = current_user.vendor_profile
    if not vendor:
        return RevenueResponse(
            total_orders=0, total_revenue=0,
            daily_orders=0, daily_revenue=0,
            monthly_orders=0, monthly_revenue=0
        )
    
    service_ids = [s.id for s in vendor.services]
    completed_statuses = [BookingStatus.COMPLETED, BookingStatus.PAYMENT_UPLOADED]
    
    # Total
    total = db.query(
        func.count(Booking.id),
        func.coalesce(func.sum(Booking.total_cost), 0)
    ).filter(
        Booking.service_id.in_(service_ids),
        Booking.status.in_(completed_statuses)
    ).first()
    
    # Today
    today = datetime.utcnow().date()
    daily = db.query(
        func.count(Booking.id),
        func.coalesce(func.sum(Booking.total_cost), 0)
    ).filter(
        Booking.service_id.in_(service_ids),
        Booking.status.in_(completed_statuses),
        func.date(Booking.completed_at) == today
    ).first()
    
    # This month
    month_start = today.replace(day=1)
    monthly = db.query(
        func.count(Booking.id),
        func.coalesce(func.sum(Booking.total_cost), 0)
    ).filter(
        Booking.service_id.in_(service_ids),
        Booking.status.in_(completed_statuses),
        func.date(Booking.completed_at) >= month_start
    ).first()
    
    return RevenueResponse(
        total_orders=total[0] or 0,
        total_revenue=float(total[1] or 0),
        daily_orders=daily[0] or 0,
        daily_revenue=float(daily[1] or 0),
        monthly_orders=monthly[0] or 0,
        monthly_revenue=float(monthly[1] or 0)
    )


# ==================== COMPLAINTS ====================

@router.get("/complaints", response_model=List[ComplaintResponse])
def get_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Get complaints for vendor's orders"""
    vendor = current_user.vendor_profile
    if not vendor:
        return []
    
    service_ids = [s.id for s in vendor.services]
    complaints = db.query(Complaint).join(Booking).filter(
        Booking.service_id.in_(service_ids),
        Complaint.escalation_level == 1  # Vendor level
    ).all()
    
    return complaints


@router.put("/complaints/{complaint_id}/resolve")
def resolve_complaint(
    complaint_id: int,
    resolution_notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor)
) -> Any:
    """Resolve complaint at vendor level"""
    vendor = current_user.vendor_profile
    
    complaint = db.query(Complaint).join(Booking).join(Service).filter(
        Complaint.id == complaint_id,
        Service.vendor_id == vendor.id,
        Complaint.escalation_level == 1
    ).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = ComplaintStatus.RESOLVED_PENDING_CUSTOMER
    complaint.resolution_notes = resolution_notes
    complaint.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Complaint resolved, pending customer confirmation"}

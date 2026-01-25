"""
Worker API Endpoints
"""
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.state_machine import BookingStateMachine
from app.models.models import (
    User, Worker, Booking, BookingStatus, BookingStatusHistory, Transaction
)
from app.schemas.schemas import (
    BookingResponse, BookingDetailResponse, WorkerLocationUpdate, BookingComplete
)
from app.api.deps import get_current_active_user, require_worker

router = APIRouter()


# ==================== TASKS ====================

@router.get("/tasks", response_model=List[BookingResponse])
def get_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_worker)
) -> Any:
    """Get worker's assigned tasks"""
    worker = current_user.worker_profile
    if not worker:
        return []
    
    tasks = db.query(Booking).filter(
        Booking.worker_id == worker.id
    ).order_by(Booking.scheduled_time.desc()).all()
    
    return tasks


@router.get("/tasks/active", response_model=List[BookingResponse])
def get_active_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_worker)
) -> Any:
    """Get worker's active tasks"""
    worker = current_user.worker_profile
    if not worker:
        return []
    
    active_statuses = [BookingStatus.WORKER_ASSIGNED, BookingStatus.IN_PROGRESS]
    tasks = db.query(Booking).filter(
        Booking.worker_id == worker.id,
        Booking.status.in_(active_statuses)
    ).order_by(Booking.scheduled_time.asc()).all()
    
    return tasks


@router.get("/tasks/completed", response_model=List[BookingResponse])
def get_completed_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_worker)
) -> Any:
    """Get worker's completed tasks"""
    worker = current_user.worker_profile
    if not worker:
        return []
    
    completed_statuses = [BookingStatus.COMPLETED, BookingStatus.PAYMENT_UPLOADED]
    tasks = db.query(Booking).filter(
        Booking.worker_id == worker.id,
        Booking.status.in_(completed_statuses)
    ).order_by(Booking.completed_at.desc()).all()
    
    return tasks


@router.get("/tasks/{task_id}", response_model=BookingDetailResponse)
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_worker)
) -> Any:
    """Get task details with customer location"""
    worker = current_user.worker_profile
    
    task = db.query(Booking).filter(
        Booking.id == task_id,
        Booking.worker_id == worker.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        **BookingResponse.model_validate(task).model_dump(),
        "service_name": task.service.name,
        "vendor_name": task.service.vendor.business_name,
        "customer_name": task.customer.full_name,
        "worker_name": current_user.full_name,
        "address_text": task.address.address_text if task.address else None,
        "phone_number": task.phone.number if task.phone else None
    }


@router.put("/tasks/{task_id}/start")
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_worker)
) -> Any:
    """Mark task as in progress"""
    worker = current_user.worker_profile
    
    task = db.query(Booking).filter(
        Booking.id == task_id,
        Booking.worker_id == worker.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    is_valid, error = BookingStateMachine.validate_transition(
        task.status, BookingStatus.IN_PROGRESS, current_user.role
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    old_status = task.status
    task.status = BookingStatus.IN_PROGRESS
    worker.is_available = False
    
    history = BookingStatusHistory(
        booking_id=task.id,
        old_status=old_status,
        new_status=BookingStatus.IN_PROGRESS,
        changed_by=current_user.id
    )
    db.add(history)
    db.commit()
    
    return {"message": "Task started"}


@router.put("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    complete_data: BookingComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_worker)
) -> Any:
    """Complete task with additional cost and payment screenshot"""
    worker = current_user.worker_profile
    
    task = db.query(Booking).filter(
        Booking.id == task_id,
        Booking.worker_id == worker.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    is_valid, error = BookingStateMachine.validate_transition(
        task.status, BookingStatus.COMPLETED, current_user.role
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    old_status = task.status
    task.status = BookingStatus.COMPLETED
    task.additional_cost = complete_data.additional_cost
    task.total_cost = task.fixed_charge + complete_data.additional_cost
    task.completed_at = datetime.utcnow()
    
    if complete_data.payment_screenshot_url:
        task.payment_screenshot_url = complete_data.payment_screenshot_url
        task.status = BookingStatus.PAYMENT_UPLOADED
        
        # Create transaction
        transaction = Transaction(
            booking_id=task.id,
            amount=task.total_cost,
            screenshot_url=complete_data.payment_screenshot_url
        )
        db.add(transaction)
    
    worker.is_available = True
    
    history = BookingStatusHistory(
        booking_id=task.id,
        old_status=old_status,
        new_status=task.status,
        changed_by=current_user.id
    )
    db.add(history)
    db.commit()
    
    return {"message": "Task completed", "total_cost": task.total_cost}


# ==================== LOCATION ====================

@router.put("/location")
def update_location(
    location: WorkerLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_worker)
) -> Any:
    """Update worker's current location"""
    worker = current_user.worker_profile
    if not worker:
        raise HTTPException(status_code=400, detail="Worker profile not found")
    
    worker.current_latitude = location.latitude
    worker.current_longitude = location.longitude
    worker.location_updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Location updated"}

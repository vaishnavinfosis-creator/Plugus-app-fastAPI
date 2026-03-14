"""
Payment Receipt API Endpoints
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import uuid
import logging

from app.core.database import get_db
from app.models.models import Booking, BookingStatus, User, UserRole
from app.api.deps import get_current_active_user
from app.core.file_validator import validate_image_upload

logger = logging.getLogger(__name__)

router = APIRouter()

# Payment receipt storage directory
PAYMENT_RECEIPTS_DIR = "uploads/payment_receipts"
os.makedirs(PAYMENT_RECEIPTS_DIR, exist_ok=True)


@router.post("/bookings/{booking_id}/payment-receipt")
async def upload_payment_receipt(
    booking_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Upload payment receipt for a booking
    
    Requirements:
    - File format: JPEG, PNG
    - Max size: 5MB
    - User must be the customer of the booking
    - Booking must exist and be in appropriate status
    """
    # Verify booking exists and belongs to user
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Verify user is the customer
    if booking.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload payment receipts for your own bookings"
        )
    
    # Read file content first for later use
    file_content = await file.read()
    
    # Reset file pointer for validation
    await file.seek(0)
    
    # Validate file (5MB = 5 * 1024 * 1024 bytes)
    validation_result = await validate_image_upload(file, max_size=5 * 1024 * 1024)
    
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result.error_message
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{booking_id}_{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(PAYMENT_RECEIPTS_DIR, unique_filename)
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    # Update booking with payment screenshot URL
    booking.payment_screenshot_url = file_path
    booking.status = BookingStatus.PAYMENT_UPLOADED
    db.commit()
    db.refresh(booking)
    
    logger.info(f"Payment receipt uploaded: booking_id={booking_id}, file={unique_filename}")
    
    return {
        "message": "Payment receipt uploaded successfully",
        "booking_id": booking_id,
        "file_path": file_path,
        "status": booking.status
    }


@router.get("/bookings/{booking_id}/payment-receipt-url")
def get_payment_receipt_url(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get secure temporary URL for payment receipt
    
    URL expires after 24 hours
    Only accessible by customer, vendor, or admin
    """
    # Verify booking exists
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if payment receipt exists
    if not booking.payment_screenshot_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payment receipt found for this booking"
        )
    
    # Verify user has access (customer, vendor worker, or admin)
    has_access = (
        booking.customer_id == current_user.id or
        current_user.role in [UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN] or
        (booking.worker_id and booking.worker.user_id == current_user.id)
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this payment receipt"
        )
    
    # Generate secure URL with expiry
    expiry_time = datetime.utcnow() + timedelta(hours=24)
    secure_token = str(uuid.uuid4())
    
    # In production, store token in Redis/database with expiry
    # For now, return file path with expiry info
    secure_url = f"/api/v1/payments/receipt/{secure_token}"
    
    return {
        "url": secure_url,
        "file_path": booking.payment_screenshot_url,
        "expires_at": expiry_time.isoformat(),
        "booking_id": booking_id
    }


@router.put("/admin/bookings/{booking_id}/verify-payment")
def verify_payment(
    booking_id: int,
    approved: bool,
    notes: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Verify payment receipt (admin only)
    
    Updates booking status to PAYMENT_CONFIRMED or rejects it
    """
    # Check if user is admin
    if current_user.role not in [UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can verify payments"
        )
    
    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if payment receipt exists
    if not booking.payment_screenshot_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No payment receipt to verify"
        )
    
    # Update booking status
    if approved:
        booking.status = BookingStatus.COMPLETED
        message = "Payment verified and booking completed"
    else:
        booking.status = BookingStatus.CREATED
        message = "Payment rejected, booking reverted to created status"
    
    db.commit()
    db.refresh(booking)
    
    logger.info(f"Payment verification: booking_id={booking_id}, approved={approved}, admin_id={current_user.id}")
    
    return {
        "message": message,
        "booking_id": booking_id,
        "status": booking.status,
        "approved": approved,
        "notes": notes
    }


@router.get("/admin/payments/pending")
def get_pending_payments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get all bookings with pending payment verification
    
    Admin only
    """
    # Check if user is admin
    if current_user.role not in [UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access pending payments"
        )
    
    # Get bookings with uploaded payment receipts
    bookings = (
        db.query(Booking)
        .filter(Booking.status == BookingStatus.PAYMENT_UPLOADED)
        .filter(Booking.payment_screenshot_url.isnot(None))
        .order_by(Booking.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return {
        "bookings": [
            {
                "id": b.id,
                "customer_id": b.customer_id,
                "service_id": b.service_id,
                "total_cost": b.total_cost,
                "payment_screenshot_url": b.payment_screenshot_url,
                "created_at": b.created_at.isoformat(),
            }
            for b in bookings
        ],
        "total": len(bookings)
    }

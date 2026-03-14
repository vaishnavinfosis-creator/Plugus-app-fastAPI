"""
Customer API Endpoints
"""
from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.state_machine import BookingStateMachine
from app.models.models import (
    User, UserRole, Category, Vendor, Service, Booking, BookingStatus,
    BookingStatusHistory, Address, PhoneNumber, Review, Complaint, ComplaintStatus
)
from app.schemas.schemas import (
    CategoryResponse, VendorListResponse, ServiceWithVendor,
    BookingCreate, BookingResponse, BookingDetailResponse,
    AddressCreate, AddressResponse, PhoneCreate, PhoneResponse,
    ReviewCreate, ReviewResponse, ComplaintCreate, ComplaintResponse,
    UserResponse
)
from app.api.deps import get_current_active_user, require_customer

router = APIRouter()


# ==================== PROFILE ====================

@router.get("/profile", response_model=UserResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Get customer profile"""
    return current_user


@router.put("/profile")
def update_profile(
    full_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Update customer profile"""
    if full_name is not None:
        current_user.full_name = full_name
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Profile updated successfully",
        "profile": UserResponse.model_validate(current_user)
    }


# ==================== CATEGORIES ====================

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get all active categories"""
    categories = db.query(Category).filter(Category.is_active == True).all()
    return categories


# ==================== VENDORS ====================

@router.get("/vendors", response_model=List[VendorListResponse])
def get_vendors(
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get approved and visible vendors, optionally filtered by category"""
    query = db.query(Vendor).filter(
        Vendor.is_approved == True,
        Vendor.is_visible == True
    )
    
    if category_id:
        # Filter vendors that have services in this category
        vendor_ids = db.query(Service.vendor_id).filter(
            Service.category_id == category_id,
            Service.is_active == True
        ).distinct().all()
        vendor_ids = [v[0] for v in vendor_ids]
        query = query.filter(Vendor.id.in_(vendor_ids))
    
    vendors = query.all()
    
    result = []
    for vendor in vendors:
        service_count = db.query(Service).filter(
            Service.vendor_id == vendor.id,
            Service.is_active == True
        ).count()
        result.append({
            "id": vendor.id,
            "business_name": vendor.business_name,
            "description": vendor.description,
            "service_count": service_count
        })
    
    return result


# ==================== SERVICES ====================

@router.get("/services", response_model=List[ServiceWithVendor])
def get_services(
    vendor_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get services from approved vendors"""
    query = db.query(Service).join(Vendor).filter(
        Vendor.is_approved == True,
        Vendor.is_visible == True,
        Service.is_active == True
    )
    
    if vendor_id:
        query = query.filter(Service.vendor_id == vendor_id)
    if category_id:
        query = query.filter(Service.category_id == category_id)
    
    services = query.all()
    
    result = []
    for service in services:
        result.append({
            "id": service.id,
            "vendor_id": service.vendor_id,
            "vendor_name": service.vendor.business_name,
            "category_id": service.category_id,
            "name": service.name,
            "description": service.description,
            "base_price": service.base_price,
            "duration_minutes": service.duration_minutes,
            "is_active": service.is_active
        })
    
    return result


# ==================== ADDRESSES ====================

@router.get("/addresses", response_model=List[AddressResponse])
def get_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Get user's saved addresses (max 2)"""
    return current_user.addresses


@router.post("/addresses", response_model=AddressResponse)
def create_address(
    address_in: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Add new address (max 2)"""
    # Validate address fields
    if not address_in.label or not address_in.label.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Address label is required"
        )
    if not address_in.address_text or not address_in.address_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Address text is required"
        )
    
    if len(current_user.addresses) >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 2 addresses allowed"
        )
    
    address = Address(
        user_id=current_user.id,
        **address_in.model_dump()
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.put("/addresses/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address_in: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Update an existing address"""
    # Validate address fields
    if not address_in.label or not address_in.label.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Address label is required"
        )
    if not address_in.address_text or not address_in.address_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Address text is required"
        )
    
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    # Update fields
    address.label = address_in.label
    address.address_text = address_in.address_text
    address.latitude = address_in.latitude
    address.longitude = address_in.longitude
    address.is_default = address_in.is_default
    
    db.commit()
    db.refresh(address)
    return address


@router.delete("/addresses/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Delete an address"""
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    db.delete(address)
    db.commit()
    
    return {"message": "Address deleted successfully"}


# ==================== PHONE NUMBERS ====================

@router.get("/phones", response_model=List[PhoneResponse])
def get_phones(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Get user's saved phone numbers (max 2)"""
    return current_user.phone_numbers


@router.post("/phones", response_model=PhoneResponse)
def create_phone(
    phone_in: PhoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Add new phone number (max 2)"""
    # Validate phone number
    import re
    phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 format
    if not phone_in.number or not phone_in.number.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required"
        )
    
    # Basic validation - allow digits, spaces, hyphens, parentheses, and plus sign
    cleaned_number = re.sub(r'[\s\-\(\)]', '', phone_in.number)
    if not re.match(r'^\+?\d{10,15}$', cleaned_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    if len(current_user.phone_numbers) >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 2 phone numbers allowed"
        )
    
    phone = PhoneNumber(
        user_id=current_user.id,
        **phone_in.model_dump()
    )
    db.add(phone)
    db.commit()
    db.refresh(phone)
    return phone


@router.put("/phones/{phone_id}", response_model=PhoneResponse)
def update_phone(
    phone_id: int,
    phone_in: PhoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Update an existing phone number"""
    # Validate phone number
    import re
    if not phone_in.number or not phone_in.number.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required"
        )
    
    # Basic validation - allow digits, spaces, hyphens, parentheses, and plus sign
    cleaned_number = re.sub(r'[\s\-\(\)]', '', phone_in.number)
    if not re.match(r'^\+?\d{10,15}$', cleaned_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    phone = db.query(PhoneNumber).filter(
        PhoneNumber.id == phone_id,
        PhoneNumber.user_id == current_user.id
    ).first()
    
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found"
        )
    
    # Update fields
    phone.number = phone_in.number
    phone.is_default = phone_in.is_default
    
    db.commit()
    db.refresh(phone)
    return phone


@router.delete("/phones/{phone_id}")
def delete_phone(
    phone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Delete a phone number"""
    phone = db.query(PhoneNumber).filter(
        PhoneNumber.id == phone_id,
        PhoneNumber.user_id == current_user.id
    ).first()
    
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found"
        )
    
    db.delete(phone)
    db.commit()
    
    return {"message": "Phone number deleted successfully"}


# ==================== BOOKINGS ====================

@router.post("/bookings", response_model=BookingResponse)
def create_booking(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Create a new booking"""
    # Get service
    service = db.query(Service).filter(Service.id == booking_in.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check vendor is approved and visible
    if not service.vendor.is_approved or not service.vendor.is_visible:
        raise HTTPException(status_code=400, detail="Vendor not available")
    
    booking = Booking(
        customer_id=current_user.id,
        service_id=booking_in.service_id,
        scheduled_time=booking_in.scheduled_time,
        address_id=booking_in.address_id,
        phone_id=booking_in.phone_id,
        customer_latitude=booking_in.customer_latitude,
        customer_longitude=booking_in.customer_longitude,
        fixed_charge=service.base_price,
        total_cost=service.base_price,
        status=BookingStatus.CREATED
    )
    db.add(booking)
    db.commit()
    
    # Log status change
    history = BookingStatusHistory(
        booking_id=booking.id,
        old_status=None,
        new_status=BookingStatus.CREATED,
        changed_by=current_user.id
    )
    db.add(history)
    db.commit()
    db.refresh(booking)
    
    return booking


@router.get("/bookings", response_model=List[BookingResponse])
def get_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Get customer's bookings"""
    bookings = db.query(Booking).filter(
        Booking.customer_id == current_user.id
    ).order_by(Booking.created_at.desc()).all()
    return bookings


@router.get("/bookings/{booking_id}", response_model=BookingDetailResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Get booking details with tracking info"""
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.customer_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {
        **BookingResponse.model_validate(booking).model_dump(),
        "service_name": booking.service.name,
        "vendor_name": booking.service.vendor.business_name,
        "customer_name": current_user.full_name,
        "worker_name": booking.worker.user.full_name if booking.worker else None,
        "address_text": booking.address.address_text if booking.address else None,
        "phone_number": booking.phone.number if booking.phone else None
    }


# ==================== REVIEWS ====================

@router.post("/reviews", response_model=ReviewResponse)
def create_review(
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Submit review for completed booking"""
    booking = db.query(Booking).filter(
        Booking.id == review_in.booking_id,
        Booking.customer_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status not in [BookingStatus.COMPLETED, BookingStatus.PAYMENT_UPLOADED]:
        raise HTTPException(status_code=400, detail="Booking not completed")
    
    if booking.review:
        raise HTTPException(status_code=400, detail="Review already submitted")
    
    review = Review(
        booking_id=review_in.booking_id,
        user_id=current_user.id,
        rating=review_in.rating,
        comment=review_in.comment
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


# ==================== COMPLAINTS ====================

@router.post("/complaints", response_model=ComplaintResponse)
def create_complaint(
    complaint_in: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """File complaint for a booking"""
    booking = db.query(Booking).filter(
        Booking.id == complaint_in.booking_id,
        Booking.customer_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.complaint:
        raise HTTPException(status_code=400, detail="Complaint already filed")
    
    complaint = Complaint(
        booking_id=complaint_in.booking_id,
        description=complaint_in.description,
        status=ComplaintStatus.OPEN,
        escalation_level=1  # Starts with vendor
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.put("/complaints/{complaint_id}/close", response_model=ComplaintResponse)
def close_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
) -> Any:
    """Customer closes resolved complaint"""
    complaint = db.query(Complaint).join(Booking).filter(
        Complaint.id == complaint_id,
        Booking.customer_id == current_user.id
    ).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if complaint.status != ComplaintStatus.RESOLVED_PENDING_CUSTOMER:
        raise HTTPException(status_code=400, detail="Complaint not resolved yet")
    
    complaint.status = ComplaintStatus.CLOSED
    complaint.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(complaint)
    return complaint

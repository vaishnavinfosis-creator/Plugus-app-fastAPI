"""
Pydantic Schemas for API
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from app.models.models import UserRole, BookingStatus, ComplaintStatus


# ==================== AUTH ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.CUSTOMER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== ADDRESS & PHONE ====================

class AddressCreate(BaseModel):
    label: str
    address_text: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False


class AddressResponse(BaseModel):
    id: int
    label: str
    address_text: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool

    class Config:
        from_attributes = True


class PhoneCreate(BaseModel):
    number: str
    is_default: bool = False


class PhoneResponse(BaseModel):
    id: int
    number: str
    is_default: bool

    class Config:
        from_attributes = True


# ==================== CATEGORY ====================

class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    is_default: bool

    class Config:
        from_attributes = True


# ==================== REGION ====================

class RegionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RegionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# ==================== VENDOR ====================

class VendorCreate(BaseModel):
    business_name: str
    description: Optional[str] = None
    region_id: int


class VendorResponse(BaseModel):
    id: int
    business_name: str
    description: Optional[str] = None
    is_approved: bool
    is_visible: bool
    region_id: int

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    id: int
    business_name: str
    description: Optional[str] = None
    service_count: int = 0

    class Config:
        from_attributes = True


# ==================== SERVICE ====================

class ServiceCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    base_price: float = Field(..., gt=0)
    duration_minutes: int = 60


class ServiceResponse(BaseModel):
    id: int
    vendor_id: int
    category_id: int
    name: str
    description: Optional[str] = None
    base_price: float
    duration_minutes: int
    is_active: bool

    class Config:
        from_attributes = True


class ServiceWithVendor(ServiceResponse):
    vendor_name: str


# ==================== WORKER ====================

class WorkerCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class WorkerResponse(BaseModel):
    id: int
    user_id: int
    is_available: bool
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None

    class Config:
        from_attributes = True


class WorkerLocationUpdate(BaseModel):
    latitude: float
    longitude: float


# ==================== BOOKING ====================

class BookingCreate(BaseModel):
    service_id: int
    scheduled_time: datetime
    address_id: Optional[int] = None
    phone_id: Optional[int] = None
    customer_latitude: Optional[float] = None
    customer_longitude: Optional[float] = None


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    notes: Optional[str] = None


class BookingComplete(BaseModel):
    additional_cost: float = 0
    payment_screenshot_url: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    customer_id: int
    service_id: int
    worker_id: Optional[int] = None
    status: BookingStatus
    scheduled_time: datetime
    fixed_charge: float
    additional_cost: float
    total_cost: float
    payment_screenshot_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BookingDetailResponse(BookingResponse):
    service_name: str
    vendor_name: str
    customer_name: Optional[str] = None
    worker_name: Optional[str] = None
    address_text: Optional[str] = None
    phone_number: Optional[str] = None


# ==================== COMPLAINT ====================

class ComplaintCreate(BaseModel):
    booking_id: int
    description: str


class ComplaintResponse(BaseModel):
    id: int
    booking_id: int
    description: str
    status: ComplaintStatus
    escalation_level: int
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== REVIEW ====================

class ReviewCreate(BaseModel):
    booking_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    booking_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== ANALYTICS ====================

class RevenueResponse(BaseModel):
    total_orders: int
    total_revenue: float
    daily_orders: int
    daily_revenue: float
    monthly_orders: int
    monthly_revenue: float


class VendorRevenueResponse(BaseModel):
    vendor_id: int
    vendor_name: str
    total_orders: int
    total_revenue: float


class RegionTrafficResponse(BaseModel):
    region_id: int
    region_name: str
    total_customers: int
    total_vendors: int
    total_bookings: int

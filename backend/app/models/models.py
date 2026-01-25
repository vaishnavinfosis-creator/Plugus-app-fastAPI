"""
Plugus Platform - Database Models
SQLAlchemy 2.0 with PostgreSQL
"""
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


# ==================== ENUMS ====================

class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    WORKER = "WORKER"
    REGIONAL_ADMIN = "REGIONAL_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class BookingStatus(str, enum.Enum):
    CREATED = "CREATED"
    VENDOR_ACCEPTED = "VENDOR_ACCEPTED"
    VENDOR_REJECTED = "VENDOR_REJECTED"
    WORKER_ASSIGNED = "WORKER_ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PAYMENT_UPLOADED = "PAYMENT_UPLOADED"
    CANCELLED = "CANCELLED"


class ComplaintStatus(str, enum.Enum):
    OPEN = "OPEN"
    ESCALATED_TO_REGIONAL = "ESCALATED_TO_REGIONAL"
    ESCALATED_TO_SUPER = "ESCALATED_TO_SUPER"
    RESOLVED_PENDING_CUSTOMER = "RESOLVED_PENDING_CUSTOMER"
    CLOSED = "CLOSED"


# ==================== MODELS ====================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    phone_numbers: Mapped[List["PhoneNumber"]] = relationship("PhoneNumber", back_populates="user", cascade="all, delete-orphan")
    vendor_profile: Mapped[Optional["Vendor"]] = relationship("Vendor", back_populates="user", uselist=False, foreign_keys="Vendor.user_id")
    worker_profile: Mapped[Optional["Worker"]] = relationship("Worker", back_populates="user", uselist=False, foreign_keys="Worker.user_id")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="customer", foreign_keys="Booking.customer_id")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user")


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    admin_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    vendors: Mapped[List["Vendor"]] = relationship("Vendor", back_populates="region")


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)  # "Home", "Office"
    address_text: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="addresses")


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="phone_numbers")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Icon name
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)  # Pre-defined categories
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    services: Mapped[List["Service"]] = relationship("Service", back_populates="category")


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("regions.id"), nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=False)  # Customer visibility
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="vendor_profile", foreign_keys=[user_id])
    region: Mapped["Region"] = relationship("Region", back_populates="vendors")
    services: Mapped[List["Service"]] = relationship("Service", back_populates="vendor", cascade="all, delete-orphan")
    workers: Mapped[List["Worker"]] = relationship("Worker", back_populates="vendor", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="services")
    category: Mapped["Category"] = relationship("Category", back_populates="services")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="service")


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    current_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="worker_profile")
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="workers")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="worker")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    worker_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("workers.id"), nullable=True)
    address_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("addresses.id"), nullable=True)
    phone_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("phone_numbers.id"), nullable=True)
    
    # Status
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.CREATED)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Location (for live location bookings)
    customer_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    customer_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Costs
    fixed_charge: Mapped[float] = mapped_column(Float, nullable=False)
    additional_cost: Mapped[float] = mapped_column(Float, default=0)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Payment
    payment_screenshot_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer: Mapped["User"] = relationship("User", back_populates="bookings", foreign_keys=[customer_id])
    service: Mapped["Service"] = relationship("Service", back_populates="bookings")
    worker: Mapped[Optional["Worker"]] = relationship("Worker", back_populates="bookings")
    address: Mapped[Optional["Address"]] = relationship("Address")
    phone: Mapped[Optional["PhoneNumber"]] = relationship("PhoneNumber")
    status_history: Mapped[List["BookingStatusHistory"]] = relationship("BookingStatusHistory", back_populates="booking", cascade="all, delete-orphan")
    review: Mapped[Optional["Review"]] = relationship("Review", back_populates="booking", uselist=False)
    complaint: Mapped[Optional["Complaint"]] = relationship("Complaint", back_populates="booking", uselist=False)
    transaction: Mapped[Optional["Transaction"]] = relationship("Transaction", back_populates="booking", uselist=False)


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), nullable=False)
    old_status: Mapped[Optional[BookingStatus]] = mapped_column(Enum(BookingStatus), nullable=True)
    new_status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), nullable=False)
    changed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="status_history")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    screenshot_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="transaction")


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(Enum(ComplaintStatus), default=ComplaintStatus.OPEN)
    escalation_level: Mapped[int] = mapped_column(Integer, default=1)  # 1=Vendor, 2=Regional, 3=Super
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="complaint")
    escalation_logs: Mapped[List["ComplaintEscalationLog"]] = relationship("ComplaintEscalationLog", back_populates="complaint", cascade="all, delete-orphan")


class ComplaintEscalationLog(Base):
    __tablename__ = "complaint_escalation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    complaint_id: Mapped[int] = mapped_column(Integer, ForeignKey("complaints.id"), nullable=False)
    from_level: Mapped[int] = mapped_column(Integer, nullable=False)
    to_level: Mapped[int] = mapped_column(Integer, nullable=False)
    escalated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="escalation_logs")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="review")
    user: Mapped["User"] = relationship("User", back_populates="reviews")

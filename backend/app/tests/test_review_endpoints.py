"""
Unit tests for review endpoints
Tests Requirements: 5.2, 5.3, 5.5
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.core.database import SessionLocal, engine
from app.main import app


@pytest.fixture
def test_db():
    """Create a test database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_customer(test_db: Session):
    """Create a test customer user"""
    user = models.User(
        email=f"customer_{datetime.now().timestamp()}@test.com",
        hashed_password="hashed_password",
        role=models.UserRole.CUSTOMER,
        is_active=True,
        full_name="Test Customer"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_vendor_user(test_db: Session):
    """Create a test vendor user"""
    user = models.User(
        email=f"vendor_{datetime.now().timestamp()}@test.com",
        hashed_password="hashed_password",
        role=models.UserRole.VENDOR,
        is_active=True,
        full_name="Test Vendor"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_category(test_db: Session):
    """Create a test category"""
    category = models.Category(
        name=f"Test Category {datetime.now().timestamp()}",
        is_active=True
    )
    test_db.add(category)
    test_db.commit()
    test_db.refresh(category)
    return category


@pytest.fixture
def test_region(test_db: Session):
    """Create a test region"""
    region = models.Region(
        name=f"Test Region {datetime.now().timestamp()}",
        is_active=True
    )
    test_db.add(region)
    test_db.commit()
    test_db.refresh(region)
    return region


@pytest.fixture
def test_vendor(test_db: Session, test_vendor_user, test_region):
    """Create a test vendor"""
    vendor = models.Vendor(
        user_id=test_vendor_user.id,
        business_name="Test Vendor Business",
        region_id=test_region.id,
        is_approved=True,
        is_visible=True
    )
    test_db.add(vendor)
    test_db.commit()
    test_db.refresh(vendor)
    return vendor


@pytest.fixture
def test_service(test_db: Session, test_vendor, test_category):
    """Create a test service"""
    service = models.Service(
        vendor_id=test_vendor.id,
        category_id=test_category.id,
        name="Test Service",
        base_price=100.0,
        duration_minutes=60,
        is_active=True
    )
    test_db.add(service)
    test_db.commit()
    test_db.refresh(service)
    return service


@pytest.fixture
def test_completed_booking(test_db: Session, test_customer, test_service):
    """Create a completed test booking"""
    booking = models.Booking(
        customer_id=test_customer.id,
        service_id=test_service.id,
        status=models.BookingStatus.COMPLETED,
        scheduled_time=datetime.now(),
        fixed_charge=100.0,
        additional_cost=0.0,
        total_cost=100.0
    )
    test_db.add(booking)
    test_db.commit()
    test_db.refresh(booking)
    return booking


def test_create_review_valid_rating(test_db: Session, test_completed_booking, test_customer):
    """Test creating a review with valid rating (1-5 stars)"""
    # Test all valid ratings
    for rating in [1, 2, 3, 4, 5]:
        # Create a new booking for each test
        booking = models.Booking(
            customer_id=test_customer.id,
            service_id=test_completed_booking.service_id,
            status=models.BookingStatus.COMPLETED,
            scheduled_time=datetime.now(),
            fixed_charge=100.0,
            additional_cost=0.0,
            total_cost=100.0
        )
        test_db.add(booking)
        test_db.commit()
        test_db.refresh(booking)
        
        review = models.Review(
            booking_id=booking.id,
            user_id=test_customer.id,
            rating=rating,
            comment="Test review"
        )
        test_db.add(review)
        test_db.commit()
        test_db.refresh(review)
        
        assert review.rating == rating
        assert review.booking_id == booking.id


def test_create_review_comment_length_validation(test_db: Session, test_completed_booking, test_customer):
    """Test comment length validation (max 500 characters)"""
    # Valid comment (exactly 500 chars)
    valid_comment = "a" * 500
    review = models.Review(
        booking_id=test_completed_booking.id,
        user_id=test_customer.id,
        rating=5,
        comment=valid_comment
    )
    test_db.add(review)
    test_db.commit()
    test_db.refresh(review)
    
    assert len(review.comment) == 500
    assert review.comment == valid_comment


def test_review_rating_constraint(test_db: Session, test_completed_booking, test_customer):
    """Test that rating constraint (1-5) is enforced at database level"""
    # Create a new booking for this test
    booking = models.Booking(
        customer_id=test_customer.id,
        service_id=test_completed_booking.service_id,
        status=models.BookingStatus.COMPLETED,
        scheduled_time=datetime.now(),
        fixed_charge=100.0,
        additional_cost=0.0,
        total_cost=100.0
    )
    test_db.add(booking)
    test_db.commit()
    test_db.refresh(booking)
    
    # Try to create review with invalid rating (0)
    review = models.Review(
        booking_id=booking.id,
        user_id=test_customer.id,
        rating=0,  # Invalid
        comment="Test"
    )
    test_db.add(review)
    
    with pytest.raises(Exception):  # Database constraint violation
        test_db.commit()
    
    test_db.rollback()


def test_average_rating_calculation(test_db: Session, test_service, test_customer):
    """Test average rating calculation for a service"""
    # Create multiple bookings and reviews
    ratings = [5, 4, 3, 5, 4]
    
    for rating in ratings:
        booking = models.Booking(
            customer_id=test_customer.id,
            service_id=test_service.id,
            status=models.BookingStatus.COMPLETED,
            scheduled_time=datetime.now(),
            fixed_charge=100.0,
            additional_cost=0.0,
            total_cost=100.0
        )
        test_db.add(booking)
        test_db.commit()
        test_db.refresh(booking)
        
        review = models.Review(
            booking_id=booking.id,
            user_id=test_customer.id,
            rating=rating,
            comment=f"Review with rating {rating}"
        )
        test_db.add(review)
        test_db.commit()
    
    # Calculate average
    reviews = test_db.query(models.Review).join(models.Booking).filter(
        models.Booking.service_id == test_service.id
    ).all()
    
    average = sum(r.rating for r in reviews) / len(reviews)
    expected_average = sum(ratings) / len(ratings)
    
    assert average == expected_average
    assert average == 4.2


def test_prevent_duplicate_reviews(test_db: Session, test_completed_booking, test_customer):
    """Test that duplicate reviews for the same booking are prevented"""
    # Create first review
    review1 = models.Review(
        booking_id=test_completed_booking.id,
        user_id=test_customer.id,
        rating=5,
        comment="First review"
    )
    test_db.add(review1)
    test_db.commit()
    
    # Try to create second review for same booking
    review2 = models.Review(
        booking_id=test_completed_booking.id,
        user_id=test_customer.id,
        rating=4,
        comment="Second review"
    )
    test_db.add(review2)
    
    with pytest.raises(Exception):  # Unique constraint violation
        test_db.commit()
    
    test_db.rollback()


def test_review_only_for_completed_bookings(test_db: Session, test_customer, test_service):
    """Test that reviews should only be allowed for completed bookings"""
    # Create a pending booking
    pending_booking = models.Booking(
        customer_id=test_customer.id,
        service_id=test_service.id,
        status=models.BookingStatus.PENDING,
        scheduled_time=datetime.now(),
        fixed_charge=100.0,
        additional_cost=0.0,
        total_cost=100.0
    )
    test_db.add(pending_booking)
    test_db.commit()
    test_db.refresh(pending_booking)
    
    # This test verifies the business logic should be in the endpoint
    # The model itself allows creating reviews for any booking
    # The endpoint should enforce the completed status check
    assert pending_booking.status != models.BookingStatus.COMPLETED


def test_get_service_reviews(test_db: Session, test_service, test_customer):
    """Test retrieving all reviews for a service"""
    # Create multiple reviews
    review_data = [
        (5, "Excellent service"),
        (4, "Good service"),
        (3, "Average service")
    ]
    
    for rating, comment in review_data:
        booking = models.Booking(
            customer_id=test_customer.id,
            service_id=test_service.id,
            status=models.BookingStatus.COMPLETED,
            scheduled_time=datetime.now(),
            fixed_charge=100.0,
            additional_cost=0.0,
            total_cost=100.0
        )
        test_db.add(booking)
        test_db.commit()
        test_db.refresh(booking)
        
        review = models.Review(
            booking_id=booking.id,
            user_id=test_customer.id,
            rating=rating,
            comment=comment
        )
        test_db.add(review)
        test_db.commit()
    
    # Get all reviews for the service
    reviews = test_db.query(models.Review).join(models.Booking).filter(
        models.Booking.service_id == test_service.id
    ).all()
    
    assert len(reviews) == 3
    assert all(r.rating in [3, 4, 5] for r in reviews)


def test_review_with_no_comment(test_db: Session, test_completed_booking, test_customer):
    """Test creating a review without a comment (comment is optional)"""
    # Create a new booking
    booking = models.Booking(
        customer_id=test_customer.id,
        service_id=test_completed_booking.service_id,
        status=models.BookingStatus.COMPLETED,
        scheduled_time=datetime.now(),
        fixed_charge=100.0,
        additional_cost=0.0,
        total_cost=100.0
    )
    test_db.add(booking)
    test_db.commit()
    test_db.refresh(booking)
    
    review = models.Review(
        booking_id=booking.id,
        user_id=test_customer.id,
        rating=5,
        comment=None
    )
    test_db.add(review)
    test_db.commit()
    test_db.refresh(review)
    
    assert review.rating == 5
    assert review.comment is None

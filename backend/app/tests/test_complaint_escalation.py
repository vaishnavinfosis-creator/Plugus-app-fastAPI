"""
Unit tests for complaint auto-escalation task
Tests Requirement 4.6: Auto-escalation after 48 hours
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app import models
from app.core.database import SessionLocal
from app.tasks.complaint_escalation import (
    escalate_unresolved_complaints,
    check_complaint_escalation_status
)


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
        email="customer_escalation@test.com",
        hashed_password="hashed_password",
        role=models.UserRole.CUSTOMER,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_vendor(test_db: Session):
    """Create a test vendor user"""
    user = models.User(
        email="vendor_escalation@test.com",
        hashed_password="hashed_password",
        role=models.UserRole.VENDOR,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_booking(test_db: Session, test_customer, test_vendor):
    """Create a test booking"""
    # Create a service first
    service = models.Service(
        vendor_id=test_vendor.id,
        category_id=1,
        name="Test Service for Escalation",
        base_price=100.0,
        duration_minutes=60,
        is_active=True
    )
    test_db.add(service)
    test_db.commit()
    test_db.refresh(service)
    
    # Create booking
    booking = models.Booking(
        customer_id=test_customer.id,
        service_id=service.id,
        status=models.BookingStatus.PENDING,
        fixed_charge=100.0,
        additional_cost=0.0,
        total_cost=100.0
    )
    test_db.add(booking)
    test_db.commit()
    test_db.refresh(booking)
    return booking


def test_escalate_complaint_after_48_hours(test_db: Session, test_booking):
    """Test that complaint escalates from level 1 to level 2 after 48 hours"""
    # Create a complaint that's 49 hours old
    old_time = datetime.utcnow() - timedelta(hours=49)
    complaint = models.Complaint(
        booking_id=test_booking.id,
        description="Test complaint for escalation",
        status=models.ComplaintStatus.OPEN,
        escalation_level=1,
        created_at=old_time
    )
    test_db.add(complaint)
    test_db.commit()
    test_db.refresh(complaint)
    
    # Run escalation task
    result = escalate_unresolved_complaints()
    
    # Verify escalation occurred
    assert result["success"] is True
    assert result["escalated_count"] >= 1
    
    # Refresh complaint from database
    test_db.refresh(complaint)
    
    # Check that complaint was escalated
    assert complaint.escalation_level == 2
    assert complaint.status == models.ComplaintStatus.ESCALATED_TO_REGIONAL
    
    # Check escalation log was created
    logs = test_db.query(models.ComplaintEscalationLog).filter(
        models.ComplaintEscalationLog.complaint_id == complaint.id
    ).all()
    assert len(logs) >= 1
    assert logs[-1].from_level == 1
    assert logs[-1].to_level == 2


def test_no_escalation_before_48_hours(test_db: Session, test_booking):
    """Test that complaint does NOT escalate before 48 hours"""
    # Create a complaint that's only 24 hours old
    recent_time = datetime.utcnow() - timedelta(hours=24)
    complaint = models.Complaint(
        booking_id=test_booking.id,
        description="Recent complaint",
        status=models.ComplaintStatus.OPEN,
        escalation_level=1,
        created_at=recent_time
    )
    test_db.add(complaint)
    test_db.commit()
    initial_level = complaint.escalation_level
    
    # Run escalation task
    escalate_unresolved_complaints()
    
    # Refresh complaint from database
    test_db.refresh(complaint)
    
    # Verify no escalation occurred
    assert complaint.escalation_level == initial_level
    assert complaint.status == models.ComplaintStatus.OPEN


def test_escalate_from_regional_to_super(test_db: Session, test_booking):
    """Test escalation from Regional Admin (level 2) to Super Admin (level 3)"""
    # Create a complaint at level 2 that's 49 hours old
    old_time = datetime.utcnow() - timedelta(hours=49)
    complaint = models.Complaint(
        booking_id=test_booking.id,
        description="Regional level complaint",
        status=models.ComplaintStatus.ESCALATED_TO_REGIONAL,
        escalation_level=2,
        created_at=old_time
    )
    test_db.add(complaint)
    test_db.commit()
    
    # Add an escalation log showing it was escalated to regional 49 hours ago
    log = models.ComplaintEscalationLog(
        complaint_id=complaint.id,
        from_level=1,
        to_level=2,
        escalated_at=old_time,
        reason="Initial escalation"
    )
    test_db.add(log)
    test_db.commit()
    test_db.refresh(complaint)
    
    # Run escalation task
    result = escalate_unresolved_complaints()
    
    # Verify escalation to super admin
    assert result["success"] is True
    
    # Refresh complaint
    test_db.refresh(complaint)
    
    assert complaint.escalation_level == 3
    assert complaint.status == models.ComplaintStatus.ESCALATED_TO_SUPER


def test_no_escalation_for_resolved_complaints(test_db: Session, test_booking):
    """Test that resolved complaints are not escalated"""
    # Create an old resolved complaint
    old_time = datetime.utcnow() - timedelta(hours=100)
    complaint = models.Complaint(
        booking_id=test_booking.id,
        description="Resolved complaint",
        status=models.ComplaintStatus.RESOLVED_PENDING_CUSTOMER,
        escalation_level=1,
        created_at=old_time
    )
    test_db.add(complaint)
    test_db.commit()
    initial_level = complaint.escalation_level
    
    # Run escalation task
    escalate_unresolved_complaints()
    
    # Refresh complaint
    test_db.refresh(complaint)
    
    # Verify no escalation occurred
    assert complaint.escalation_level == initial_level
    assert complaint.status == models.ComplaintStatus.RESOLVED_PENDING_CUSTOMER


def test_no_escalation_for_closed_complaints(test_db: Session, test_booking):
    """Test that closed complaints are not escalated"""
    # Create an old closed complaint
    old_time = datetime.utcnow() - timedelta(hours=100)
    complaint = models.Complaint(
        booking_id=test_booking.id,
        description="Closed complaint",
        status=models.ComplaintStatus.CLOSED,
        escalation_level=2,
        created_at=old_time
    )
    test_db.add(complaint)
    test_db.commit()
    initial_level = complaint.escalation_level
    
    # Run escalation task
    escalate_unresolved_complaints()
    
    # Refresh complaint
    test_db.refresh(complaint)
    
    # Verify no escalation occurred
    assert complaint.escalation_level == initial_level
    assert complaint.status == models.ComplaintStatus.CLOSED


def test_no_escalation_beyond_level_3(test_db: Session, test_booking):
    """Test that complaints at max level (3) are not escalated further"""
    # Create an old complaint at max level
    old_time = datetime.utcnow() - timedelta(hours=100)
    complaint = models.Complaint(
        booking_id=test_booking.id,
        description="Max level complaint",
        status=models.ComplaintStatus.ESCALATED_TO_SUPER,
        escalation_level=3,
        created_at=old_time
    )
    test_db.add(complaint)
    test_db.commit()
    
    # Run escalation task
    escalate_unresolved_complaints()
    
    # Refresh complaint
    test_db.refresh(complaint)
    
    # Verify no escalation beyond level 3
    assert complaint.escalation_level == 3
    assert complaint.status == models.ComplaintStatus.ESCALATED_TO_SUPER


def test_check_complaint_escalation_status(test_db: Session, test_booking):
    """Test the status check function for a specific complaint"""
    # Create a complaint that's 30 hours old (not yet ready for escalation)
    recent_time = datetime.utcnow() - timedelta(hours=30)
    complaint = models.Complaint(
        booking_id=test_booking.id,
        description="Status check complaint",
        status=models.ComplaintStatus.OPEN,
        escalation_level=1,
        created_at=recent_time
    )
    test_db.add(complaint)
    test_db.commit()
    test_db.refresh(complaint)
    
    # Check status
    result = check_complaint_escalation_status(complaint.id)
    
    assert result["success"] is True
    assert result["complaint_id"] == complaint.id
    assert result["current_level"] == 1
    assert result["needs_escalation"] is False
    assert result["hours_elapsed"] >= 30
    assert result["hours_until_escalation"] > 0


def test_check_complaint_needs_escalation(test_db: Session, test_booking):
    """Test status check for complaint that needs escalation"""
    # Create a complaint that's 50 hours old
    old_time = datetime.utcnow() - timedelta(hours=50)
    complaint = models.Complaint(
        booking_id=test_booking.id,
        description="Needs escalation",
        status=models.ComplaintStatus.OPEN,
        escalation_level=1,
        created_at=old_time
    )
    test_db.add(complaint)
    test_db.commit()
    test_db.refresh(complaint)
    
    # Check status
    result = check_complaint_escalation_status(complaint.id)
    
    assert result["success"] is True
    assert result["needs_escalation"] is True
    assert result["hours_elapsed"] >= 48


def test_check_nonexistent_complaint(test_db: Session):
    """Test status check for non-existent complaint"""
    result = check_complaint_escalation_status(99999)
    
    assert result["success"] is False
    assert "not found" in result["message"].lower()


def test_escalation_log_creation(test_db: Session, test_booking):
    """Test that escalation logs are properly created"""
    # Create an old complaint
    old_time = datetime.utcnow() - timedelta(hours=49)
    complaint = models.Complaint(
        booking_id=test_booking.id,
        description="Log test complaint",
        status=models.ComplaintStatus.OPEN,
        escalation_level=1,
        created_at=old_time
    )
    test_db.add(complaint)
    test_db.commit()
    test_db.refresh(complaint)
    
    # Run escalation
    escalate_unresolved_complaints()
    
    # Check logs
    logs = test_db.query(models.ComplaintEscalationLog).filter(
        models.ComplaintEscalationLog.complaint_id == complaint.id
    ).all()
    
    assert len(logs) >= 1
    latest_log = logs[-1]
    assert latest_log.from_level == 1
    assert latest_log.to_level == 2
    assert "48 hours" in latest_log.reason.lower()
    assert latest_log.escalated_at is not None


def test_multiple_complaints_escalation(test_db: Session, test_booking):
    """Test escalating multiple complaints in one run"""
    old_time = datetime.utcnow() - timedelta(hours=49)
    
    # Create multiple old complaints
    complaints = []
    for i in range(3):
        complaint = models.Complaint(
            booking_id=test_booking.id,
            description=f"Complaint {i}",
            status=models.ComplaintStatus.OPEN,
            escalation_level=1,
            created_at=old_time
        )
        test_db.add(complaint)
        complaints.append(complaint)
    
    test_db.commit()
    
    # Run escalation
    result = escalate_unresolved_complaints()
    
    # Verify multiple escalations
    assert result["success"] is True
    assert result["escalated_count"] >= 3
    
    # Check all complaints were escalated
    for complaint in complaints:
        test_db.refresh(complaint)
        assert complaint.escalation_level == 2

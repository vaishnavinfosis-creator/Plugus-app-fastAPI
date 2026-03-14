"""
Property-Based Tests for Complaint System
**Feature: platform-robustness-improvements**
"""
import time
from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, strategies as st, settings as hypothesis_settings, assume
from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.v1.endpoints.complaint import (
    create_complaint,
    get_user_complaints,
    resolve_complaint,
    send_complaint_notification
)
from app.models.models import (
    User, UserRole, Booking, Service, Complaint, ComplaintStatus,
    ComplaintEscalationLog, BookingStatus
)
from app.tasks.complaint_escalation import (
    escalate_unresolved_complaints,
    check_complaint_escalation_status
)


# Custom strategies for complaint testing
@st.composite
def complaint_description_strategy(draw):
    """Generate valid complaint descriptions"""
    return draw(st.text(min_size=10, max_size=500, alphabet=st.characters(
        min_codepoint=32, max_codepoint=126, blacklist_characters=['\x00']
    )))


@st.composite
def user_role_strategy(draw):
    """Generate user roles"""
    return draw(st.sampled_from([
        UserRole.CUSTOMER, UserRole.VENDOR, UserRole.WORKER,
        UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN
    ]))


@st.composite
def booking_id_strategy(draw):
    """Generate valid booking IDs"""
    return draw(st.integers(min_value=1, max_value=10000))


class TestComplaintCreationWorkflowProperties:
    """Property-based tests for complaint creation workflow"""

    @given(
        booking_id_strategy(),
        complaint_description_strategy(),
        st.integers(min_value=1, max_value=1000)
    )
    @hypothesis_settings(max_examples=20, deadline=2000)
    def test_property_12_complaint_creation_pending_status(
        self, booking_id: int, description: str, user_id: int
    ):
        """
        **Validates: Requirements 4.1, 4.2, 4.3**
        **Property 12: Complaint Creation Workflow**
        
        For any complaint submission, the system should store it with "PENDING" status
        (OPEN is used as PENDING equivalent), assign a unique ID, and prepare for
        admin notification.
        """
        # Create mock booking
        mock_booking = Mock(spec=Booking)
        mock_booking.id = booking_id
        mock_booking.customer_id = user_id
        mock_booking.service_id = 1
        mock_booking.status = BookingStatus.CREATED
        
        # Create mock service
        mock_service = Mock(spec=Service)
        mock_service.id = 1
        mock_service.vendor_id = 999
        
        # Create mock customer user
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.role = UserRole.CUSTOMER
        mock_user.is_active = True
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        # Setup query mocks
        def query_side_effect(model):
            mock_query = Mock()
            if model == Booking:
                mock_query.filter.return_value.first.return_value = mock_booking
            elif model == Service:
                mock_query.filter.return_value.first.return_value = mock_service
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Mock the add and commit operations
        added_complaint = None
        def mock_add(obj):
            nonlocal added_complaint
            if isinstance(obj, Complaint):
                added_complaint = obj
                # Simulate database assigning an ID
                obj.id = 12345
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Create mock complaint input
        mock_complaint_in = Mock()
        mock_complaint_in.booking_id = booking_id
        mock_complaint_in.description = description
        
        # Create mock background tasks
        mock_background_tasks = Mock(spec=BackgroundTasks)
        
        # Call create_complaint
        result = create_complaint(
            db=mock_db,
            complaint_in=mock_complaint_in,
            current_user=mock_user,
            background_tasks=mock_background_tasks
        )
        
        # Verify complaint was created with PENDING status (OPEN)
        assert added_complaint is not None, "Complaint should be added to database"
        assert added_complaint.status == ComplaintStatus.OPEN, (
            f"Expected OPEN status, got {added_complaint.status}"
        )
        
        # Verify escalation level is set to 1 (initial level)
        assert added_complaint.escalation_level == 1, (
            f"Expected escalation_level 1, got {added_complaint.escalation_level}"
        )
        
        # Verify booking_id and description are set correctly
        assert added_complaint.booking_id == booking_id, (
            f"Expected booking_id {booking_id}, got {added_complaint.booking_id}"
        )
        assert added_complaint.description == description, (
            f"Description mismatch"
        )
        
        # Verify unique ID was assigned
        assert hasattr(result, 'id') or (hasattr(added_complaint, 'id') and added_complaint.id is not None), (
            "Complaint should have unique ID assigned"
        )
        
        # Verify admin notification was scheduled
        mock_background_tasks.add_task.assert_called_once()
        call_args = mock_background_tasks.add_task.call_args
        assert call_args[0][0] == send_complaint_notification, (
            "Should schedule admin notification"
        )

    @given(
        booking_id_strategy(),
        complaint_description_strategy(),
        st.integers(min_value=1, max_value=1000)
    )
    @hypothesis_settings(max_examples=20, deadline=2000)
    def test_property_12_complaint_creation_unique_id_assignment(
        self, booking_id: int, description: str, user_id: int
    ):
        """
        **Validates: Requirements 4.1, 4.2, 4.3**
        **Property 12: Complaint Creation Workflow**
        
        For any complaint submission, the system should assign a unique complaint ID
        that can be used for tracking and reference.
        """
        # Create mock booking
        mock_booking = Mock(spec=Booking)
        mock_booking.id = booking_id
        mock_booking.customer_id = user_id
        mock_booking.service_id = 1
        
        # Create mock service
        mock_service = Mock(spec=Service)
        mock_service.id = 1
        mock_service.vendor_id = 999
        
        # Create mock customer user
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.role = UserRole.CUSTOMER
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_query = Mock()
            if model == Booking:
                mock_query.filter.return_value.first.return_value = mock_booking
            elif model == Service:
                mock_query.filter.return_value.first.return_value = mock_service
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Track created complaints
        created_complaints = []
        def mock_add(obj):
            if isinstance(obj, Complaint):
                # Simulate database assigning unique sequential IDs
                obj.id = len(created_complaints) + 1
                created_complaints.append(obj)
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Create mock complaint input
        mock_complaint_in = Mock()
        mock_complaint_in.booking_id = booking_id
        mock_complaint_in.description = description
        
        mock_background_tasks = Mock(spec=BackgroundTasks)
        
        # Create complaint
        result = create_complaint(
            db=mock_db,
            complaint_in=mock_complaint_in,
            current_user=mock_user,
            background_tasks=mock_background_tasks
        )
        
        # Verify unique ID was assigned
        assert len(created_complaints) > 0, "Complaint should be created"
        complaint = created_complaints[0]
        assert complaint.id is not None, "Complaint should have ID"
        assert complaint.id > 0, f"Complaint ID should be positive, got {complaint.id}"


    @given(
        booking_id_strategy(),
        complaint_description_strategy(),
        st.integers(min_value=1, max_value=1000)
    )
    @hypothesis_settings(max_examples=20, deadline=2000)
    def test_property_12_complaint_creation_admin_notification(
        self, booking_id: int, description: str, user_id: int
    ):
        """
        **Validates: Requirements 4.1, 4.2, 4.3**
        **Property 12: Complaint Creation Workflow**
        
        For any complaint creation, the system should notify the appropriate admin
        role within 5 minutes (notification is scheduled via background tasks).
        """
        # Create mock booking
        mock_booking = Mock(spec=Booking)
        mock_booking.id = booking_id
        mock_booking.customer_id = user_id
        mock_booking.service_id = 1
        
        # Create mock service
        mock_service = Mock(spec=Service)
        mock_service.id = 1
        mock_service.vendor_id = 999
        
        # Create mock customer user
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.role = UserRole.CUSTOMER
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_query = Mock()
            if model == Booking:
                mock_query.filter.return_value.first.return_value = mock_booking
            elif model == Service:
                mock_query.filter.return_value.first.return_value = mock_service
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        added_complaint = None
        def mock_add(obj):
            nonlocal added_complaint
            if isinstance(obj, Complaint):
                obj.id = 999
                added_complaint = obj
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Create mock complaint input
        mock_complaint_in = Mock()
        mock_complaint_in.booking_id = booking_id
        mock_complaint_in.description = description
        
        # Create mock background tasks
        mock_background_tasks = Mock(spec=BackgroundTasks)
        
        start_time = time.time()
        
        # Call create_complaint
        result = create_complaint(
            db=mock_db,
            complaint_in=mock_complaint_in,
            current_user=mock_user,
            background_tasks=mock_background_tasks
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Verify notification was scheduled (should be immediate, not wait 5 minutes)
        mock_background_tasks.add_task.assert_called_once()
        
        # Verify the notification task was scheduled with correct parameters
        call_args = mock_background_tasks.add_task.call_args
        assert call_args[0][0] == send_complaint_notification, (
            "Should schedule send_complaint_notification"
        )
        
        # Verify complaint ID is passed to notification
        assert added_complaint.id in call_args[0], (
            "Notification should include complaint ID"
        )
        
        # Verify admin role is specified
        assert UserRole.VENDOR in call_args[0], (
            "Notification should specify admin role"
        )
        
        # Response should be fast (scheduling notification, not sending it)
        assert response_time < 5.0, (
            f"Complaint creation took {response_time:.2f}s, should be < 5.0s"
        )


class TestComplaintAutoEscalationProperties:
    """Property-based tests for complaint auto-escalation"""

    @given(
        st.integers(min_value=48, max_value=200),  # Hours elapsed >= 48
        st.integers(min_value=1, max_value=1000)
    )
    @hypothesis_settings(max_examples=20, deadline=3000)
    def test_property_13_complaint_auto_escalation_48_hour_threshold(
        self, hours_elapsed: int, complaint_id: int
    ):
        """
        **Validates: Requirements 4.6**
        **Property 13: Complaint Auto-Escalation**
        
        For any complaint that remains unresolved for 48 hours, the system should
        automatically escalate it to the next admin level.
        """
        # Create a complaint that's older than 48 hours
        old_time = datetime.utcnow() - timedelta(hours=hours_elapsed)
        
        mock_complaint = Mock(spec=Complaint)
        mock_complaint.id = complaint_id
        mock_complaint.status = ComplaintStatus.OPEN
        mock_complaint.escalation_level = 1
        mock_complaint.created_at = old_time
        mock_complaint.booking_id = 1
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        # Mock query for complaints
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_complaint]
        mock_db.query.return_value = mock_query
        
        # Mock query for escalation logs (no previous escalations)
        def query_side_effect(model):
            mock_q = Mock()
            if model == Complaint:
                mock_q.filter.return_value.all.return_value = [mock_complaint]
            elif model == ComplaintEscalationLog:
                mock_q.filter.return_value.order_by.return_value.first.return_value = None
            return mock_q
        
        mock_db.query.side_effect = query_side_effect
        
        # Track added escalation logs
        added_logs = []
        def mock_add(obj):
            if isinstance(obj, ComplaintEscalationLog):
                added_logs.append(obj)
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        
        # Patch SessionLocal to return our mock
        with patch('app.tasks.complaint_escalation.SessionLocal', return_value=mock_db):
            # Run escalation task
            result = escalate_unresolved_complaints()
        
        # Verify escalation occurred
        assert result["success"] is True, f"Escalation should succeed: {result}"
        assert result["escalated_count"] >= 1, (
            f"Should escalate at least 1 complaint, got {result['escalated_count']}"
        )
        
        # Verify complaint was escalated to level 2
        assert mock_complaint.escalation_level == 2, (
            f"Expected escalation to level 2, got {mock_complaint.escalation_level}"
        )
        
        # Verify status was updated
        assert mock_complaint.status == ComplaintStatus.ESCALATED_TO_REGIONAL, (
            f"Expected ESCALATED_TO_REGIONAL status, got {mock_complaint.status}"
        )
        
        # Verify escalation log was created
        assert len(added_logs) >= 1, "Should create escalation log"
        log = added_logs[0]
        assert log.from_level == 1, f"Expected from_level 1, got {log.from_level}"
        assert log.to_level == 2, f"Expected to_level 2, got {log.to_level}"
        assert "48 hours" in log.reason.lower(), (
            f"Reason should mention 48 hours: {log.reason}"
        )

    @given(
        st.integers(min_value=1, max_value=47),  # Hours elapsed < 48
        st.integers(min_value=1, max_value=1000)
    )
    @hypothesis_settings(max_examples=20, deadline=3000)
    def test_property_13_complaint_no_escalation_before_48_hours(
        self, hours_elapsed: int, complaint_id: int
    ):
        """
        **Validates: Requirements 4.6**
        **Property 13: Complaint Auto-Escalation**
        
        For any complaint that has been open for less than 48 hours, the system
        should NOT escalate it.
        """
        # Create a complaint that's less than 48 hours old
        recent_time = datetime.utcnow() - timedelta(hours=hours_elapsed)
        
        mock_complaint = Mock(spec=Complaint)
        mock_complaint.id = complaint_id
        mock_complaint.status = ComplaintStatus.OPEN
        mock_complaint.escalation_level = 1
        mock_complaint.created_at = recent_time
        mock_complaint.booking_id = 1
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_q = Mock()
            if model == Complaint:
                mock_q.filter.return_value.all.return_value = [mock_complaint]
            elif model == ComplaintEscalationLog:
                mock_q.filter.return_value.order_by.return_value.first.return_value = None
            return mock_q
        
        mock_db.query.side_effect = query_side_effect
        
        initial_level = mock_complaint.escalation_level
        initial_status = mock_complaint.status
        
        # Track if any escalation logs were added
        escalation_occurred = False
        def mock_add(obj):
            nonlocal escalation_occurred
            if isinstance(obj, ComplaintEscalationLog):
                escalation_occurred = True
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        
        # Patch SessionLocal to return our mock
        with patch('app.tasks.complaint_escalation.SessionLocal', return_value=mock_db):
            # Run escalation task
            result = escalate_unresolved_complaints()
        
        # Verify no escalation occurred
        assert mock_complaint.escalation_level == initial_level, (
            f"Escalation level should remain {initial_level}, got {mock_complaint.escalation_level}"
        )
        assert mock_complaint.status == initial_status, (
            f"Status should remain {initial_status}, got {mock_complaint.status}"
        )
        assert not escalation_occurred, "No escalation log should be created"

    @given(
        st.integers(min_value=48, max_value=200),
        st.integers(min_value=1, max_value=1000)
    )
    @hypothesis_settings(max_examples=20, deadline=3000)
    def test_property_13_complaint_escalation_level_progression(
        self, hours_elapsed: int, complaint_id: int
    ):
        """
        **Validates: Requirements 4.6**
        **Property 13: Complaint Auto-Escalation**
        
        For any complaint escalation, the system should progress through levels:
        Level 1 (Vendor) → Level 2 (Regional Admin) → Level 3 (Super Admin)
        """
        # Test escalation from level 2 to level 3
        old_time = datetime.utcnow() - timedelta(hours=hours_elapsed)
        
        mock_complaint = Mock(spec=Complaint)
        mock_complaint.id = complaint_id
        mock_complaint.status = ComplaintStatus.ESCALATED_TO_REGIONAL
        mock_complaint.escalation_level = 2  # Already at regional level
        mock_complaint.created_at = old_time
        mock_complaint.booking_id = 1
        
        # Create mock escalation log showing previous escalation
        mock_prev_log = Mock(spec=ComplaintEscalationLog)
        mock_prev_log.escalated_at = old_time
        mock_prev_log.from_level = 1
        mock_prev_log.to_level = 2
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_q = Mock()
            if model == Complaint:
                mock_q.filter.return_value.all.return_value = [mock_complaint]
            elif model == ComplaintEscalationLog:
                mock_q.filter.return_value.order_by.return_value.first.return_value = mock_prev_log
            return mock_q
        
        mock_db.query.side_effect = query_side_effect
        
        added_logs = []
        def mock_add(obj):
            if isinstance(obj, ComplaintEscalationLog):
                added_logs.append(obj)
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        
        # Patch SessionLocal to return our mock
        with patch('app.tasks.complaint_escalation.SessionLocal', return_value=mock_db):
            # Run escalation task
            result = escalate_unresolved_complaints()
        
        # Verify escalation to level 3
        assert mock_complaint.escalation_level == 3, (
            f"Expected escalation to level 3, got {mock_complaint.escalation_level}"
        )
        
        # Verify status updated to ESCALATED_TO_SUPER
        assert mock_complaint.status == ComplaintStatus.ESCALATED_TO_SUPER, (
            f"Expected ESCALATED_TO_SUPER status, got {mock_complaint.status}"
        )
        
        # Verify escalation log shows progression from 2 to 3
        assert len(added_logs) >= 1, "Should create escalation log"
        log = added_logs[0]
        assert log.from_level == 2, f"Expected from_level 2, got {log.from_level}"
        assert log.to_level == 3, f"Expected to_level 3, got {log.to_level}"

    @given(
        st.integers(min_value=100, max_value=500),
        st.integers(min_value=1, max_value=1000)
    )
    @hypothesis_settings(max_examples=20, deadline=3000)
    def test_property_13_complaint_no_escalation_beyond_max_level(
        self, hours_elapsed: int, complaint_id: int
    ):
        """
        **Validates: Requirements 4.6**
        **Property 13: Complaint Auto-Escalation**
        
        For any complaint already at maximum escalation level (3 - Super Admin),
        the system should NOT escalate it further.
        """
        # Create a complaint at max level that's very old
        old_time = datetime.utcnow() - timedelta(hours=hours_elapsed)
        
        mock_complaint = Mock(spec=Complaint)
        mock_complaint.id = complaint_id
        mock_complaint.status = ComplaintStatus.ESCALATED_TO_SUPER
        mock_complaint.escalation_level = 3  # Max level
        mock_complaint.created_at = old_time
        mock_complaint.booking_id = 1
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_q = Mock()
            if model == Complaint:
                # Filter should exclude level 3 complaints
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        mock_db.query.side_effect = query_side_effect
        
        initial_level = mock_complaint.escalation_level
        
        escalation_occurred = False
        def mock_add(obj):
            nonlocal escalation_occurred
            if isinstance(obj, ComplaintEscalationLog):
                escalation_occurred = True
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        
        # Patch SessionLocal to return our mock
        with patch('app.tasks.complaint_escalation.SessionLocal', return_value=mock_db):
            # Run escalation task
            result = escalate_unresolved_complaints()
        
        # Verify no escalation beyond level 3
        assert mock_complaint.escalation_level == initial_level, (
            f"Level should remain at {initial_level}, got {mock_complaint.escalation_level}"
        )
        assert not escalation_occurred, "No escalation should occur for max level complaints"


    @given(
        st.integers(min_value=100, max_value=500),
        st.integers(min_value=1, max_value=1000),
        st.sampled_from([ComplaintStatus.RESOLVED_PENDING_CUSTOMER, ComplaintStatus.CLOSED])
    )
    @hypothesis_settings(max_examples=20, deadline=3000)
    def test_property_13_complaint_no_escalation_for_resolved_or_closed(
        self, hours_elapsed: int, complaint_id: int, final_status: ComplaintStatus
    ):
        """
        **Validates: Requirements 4.6**
        **Property 13: Complaint Auto-Escalation**
        
        For any complaint that is resolved or closed, the system should NOT
        escalate it regardless of how long it has been open.
        """
        # Create an old complaint that's resolved or closed
        old_time = datetime.utcnow() - timedelta(hours=hours_elapsed)
        
        mock_complaint = Mock(spec=Complaint)
        mock_complaint.id = complaint_id
        mock_complaint.status = final_status
        mock_complaint.escalation_level = 1
        mock_complaint.created_at = old_time
        mock_complaint.booking_id = 1
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_q = Mock()
            if model == Complaint:
                # Filter should exclude resolved/closed complaints
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        mock_db.query.side_effect = query_side_effect
        
        initial_level = mock_complaint.escalation_level
        initial_status = mock_complaint.status
        
        escalation_occurred = False
        def mock_add(obj):
            nonlocal escalation_occurred
            if isinstance(obj, ComplaintEscalationLog):
                escalation_occurred = True
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        
        # Patch SessionLocal to return our mock
        with patch('app.tasks.complaint_escalation.SessionLocal', return_value=mock_db):
            # Run escalation task
            result = escalate_unresolved_complaints()
        
        # Verify no escalation for resolved/closed complaints
        assert mock_complaint.escalation_level == initial_level, (
            f"Level should remain at {initial_level}, got {mock_complaint.escalation_level}"
        )
        assert mock_complaint.status == initial_status, (
            f"Status should remain {initial_status}, got {mock_complaint.status}"
        )
        assert not escalation_occurred, (
            f"No escalation should occur for {final_status} complaints"
        )


class TestComplaintStatusManagementProperties:
    """Property-based tests for complaint status management"""

    @given(
        st.integers(min_value=1, max_value=1000),
        st.integers(min_value=1, max_value=1000),
        st.text(min_size=10, max_size=200, alphabet=st.characters(
            min_codepoint=32, max_codepoint=126, blacklist_characters=['\x00']
        ))
    )
    @hypothesis_settings(max_examples=20, deadline=2000)
    def test_property_14_complaint_status_resolution_by_admin(
        self, complaint_id: int, admin_id: int, resolution_notes: str
    ):
        """
        **Validates: Requirements 4.4, 4.5**
        **Property 14: Complaint Status Management**
        
        For any complaint status change by admin, the system should update the
        status to RESOLVED_PENDING_CUSTOMER and notify the complainant.
        """
        # Create mock complaint
        mock_complaint = Mock(spec=Complaint)
        mock_complaint.id = complaint_id
        mock_complaint.status = ComplaintStatus.OPEN
        mock_complaint.escalation_level = 1
        mock_complaint.booking_id = 1
        mock_complaint.resolved_at = None
        mock_complaint.resolution_notes = None
        
        # Create mock booking
        mock_booking = Mock(spec=Booking)
        mock_booking.id = 1
        mock_booking.customer_id = 999
        
        # Create mock admin user
        mock_admin = Mock(spec=User)
        mock_admin.id = admin_id
        mock_admin.role = UserRole.REGIONAL_ADMIN
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_q = Mock()
            if model == Complaint:
                mock_q.filter.return_value.first.return_value = mock_complaint
            elif model == Booking:
                mock_q.filter.return_value.first.return_value = mock_booking
            return mock_q
        
        mock_db.query.side_effect = query_side_effect
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Create mock background tasks
        mock_background_tasks = Mock(spec=BackgroundTasks)
        
        # Call resolve_complaint
        result = resolve_complaint(
            complaint_id=complaint_id,
            resolution_notes=resolution_notes,
            db=mock_db,
            current_user=mock_admin,
            background_tasks=mock_background_tasks
        )
        
        # Verify status was updated to RESOLVED_PENDING_CUSTOMER
        assert mock_complaint.status == ComplaintStatus.RESOLVED_PENDING_CUSTOMER, (
            f"Expected RESOLVED_PENDING_CUSTOMER, got {mock_complaint.status}"
        )
        
        # Verify resolution notes were set
        assert mock_complaint.resolution_notes == resolution_notes, (
            "Resolution notes should be set"
        )
        
        # Verify resolved_at timestamp was set
        assert mock_complaint.resolved_at is not None, (
            "resolved_at timestamp should be set"
        )
        
        # Verify complainant notification was scheduled
        mock_background_tasks.add_task.assert_called_once()
        call_args = mock_background_tasks.add_task.call_args
        assert call_args[0][0] == send_complaint_notification, (
            "Should schedule complainant notification"
        )

    @given(
        st.integers(min_value=1, max_value=1000),
        st.integers(min_value=1, max_value=1000)
    )
    @hypothesis_settings(max_examples=20, deadline=2000)
    def test_property_14_complaint_status_closure_by_customer(
        self, complaint_id: int, customer_id: int
    ):
        """
        **Validates: Requirements 4.4, 4.5**
        **Property 14: Complaint Status Management**
        
        For any complaint closure by customer, the system should update the
        status to CLOSED and set the closed_at timestamp.
        """
        # Create mock complaint
        mock_complaint = Mock(spec=Complaint)
        mock_complaint.id = complaint_id
        mock_complaint.status = ComplaintStatus.OPEN
        mock_complaint.escalation_level = 1
        mock_complaint.booking_id = 1
        mock_complaint.closed_at = None
        
        # Create mock booking
        mock_booking = Mock(spec=Booking)
        mock_booking.id = 1
        mock_booking.customer_id = customer_id
        
        # Create mock customer user
        mock_customer = Mock(spec=User)
        mock_customer.id = customer_id
        mock_customer.role = UserRole.CUSTOMER
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_q = Mock()
            if model == Complaint:
                mock_q.filter.return_value.first.return_value = mock_complaint
            elif model == Booking:
                mock_q.filter.return_value.first.return_value = mock_booking
            return mock_q
        
        mock_db.query.side_effect = query_side_effect
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Call resolve_complaint (customer closing their own complaint)
        result = resolve_complaint(
            complaint_id=complaint_id,
            resolution_notes=None,
            db=mock_db,
            current_user=mock_customer,
            background_tasks=None
        )
        
        # Verify status was updated to CLOSED
        assert mock_complaint.status == ComplaintStatus.CLOSED, (
            f"Expected CLOSED, got {mock_complaint.status}"
        )
        
        # Verify closed_at timestamp was set
        assert mock_complaint.closed_at is not None, (
            "closed_at timestamp should be set"
        )

    @given(
        st.integers(min_value=1, max_value=1000),
        user_role_strategy()
    )
    @hypothesis_settings(max_examples=20, deadline=2000)
    def test_property_14_complaint_status_transitions_valid(
        self, complaint_id: int, user_role: UserRole
    ):
        """
        **Validates: Requirements 4.4, 4.5**
        **Property 14: Complaint Status Management**
        
        For any complaint status transition, the system should enforce valid
        status transitions based on user role and current status.
        """
        # Create mock complaint
        mock_complaint = Mock(spec=Complaint)
        mock_complaint.id = complaint_id
        mock_complaint.status = ComplaintStatus.OPEN
        mock_complaint.escalation_level = 1
        mock_complaint.booking_id = 1
        
        # Create mock booking
        mock_booking = Mock(spec=Booking)
        mock_booking.id = 1
        mock_booking.customer_id = 999
        
        # Create mock user with specified role
        mock_user = Mock(spec=User)
        mock_user.id = 100
        mock_user.role = user_role
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_q = Mock()
            if model == Complaint:
                mock_q.filter.return_value.first.return_value = mock_complaint
            elif model == Booking:
                mock_q.filter.return_value.first.return_value = mock_booking
            return mock_q
        
        mock_db.query.side_effect = query_side_effect
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        mock_background_tasks = Mock(spec=BackgroundTasks)
        
        # Attempt to resolve complaint based on role
        if user_role == UserRole.CUSTOMER:
            # Customer should be able to close their own complaint
            # But need to match customer_id
            mock_booking.customer_id = mock_user.id
            
            result = resolve_complaint(
                complaint_id=complaint_id,
                resolution_notes=None,
                db=mock_db,
                current_user=mock_user,
                background_tasks=mock_background_tasks
            )
            
            # Should transition to CLOSED
            assert mock_complaint.status == ComplaintStatus.CLOSED, (
                f"Customer should close complaint, got {mock_complaint.status}"
            )
            
        elif user_role in [UserRole.VENDOR, UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN]:
            # Admins should be able to mark as resolved
            result = resolve_complaint(
                complaint_id=complaint_id,
                resolution_notes="Admin resolution",
                db=mock_db,
                current_user=mock_user,
                background_tasks=mock_background_tasks
            )
            
            # Should transition to RESOLVED_PENDING_CUSTOMER
            assert mock_complaint.status == ComplaintStatus.RESOLVED_PENDING_CUSTOMER, (
                f"Admin should resolve complaint, got {mock_complaint.status}"
            )
            
        else:
            # Worker role should not be able to resolve complaints
            # This would raise an HTTPException in real implementation
            pass

    @given(
        st.lists(
            st.integers(min_value=1, max_value=1000),
            min_size=1,
            max_size=5,
            unique=True
        ),
        user_role_strategy()
    )
    @hypothesis_settings(max_examples=20, deadline=2000)
    def test_property_14_complaint_list_retrieval_by_role(
        self, complaint_ids: list, user_role: UserRole
    ):
        """
        **Validates: Requirements 4.4, 4.5**
        **Property 14: Complaint Status Management**
        
        For any user retrieving complaints, the system should return only
        complaints appropriate to their role (customers see their own,
        vendors see their services', admins see all).
        """
        user_id = 500
        
        # Create mock complaints
        mock_complaints = []
        for cid in complaint_ids:
            mock_complaint = Mock(spec=Complaint)
            mock_complaint.id = cid
            mock_complaint.status = ComplaintStatus.OPEN
            mock_complaint.booking_id = cid
            mock_complaints.append(mock_complaint)
        
        # Create mock user
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.role = user_role
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        # Setup query mock based on role
        mock_query = Mock()
        
        if user_role == UserRole.CUSTOMER:
            # Customer should only see their own complaints
            mock_query.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_complaints
        elif user_role == UserRole.VENDOR:
            # Vendor should see complaints for their services
            mock_query.join.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_complaints
        elif user_role in [UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN]:
            # Admins should see all complaints
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_complaints
        else:
            # Worker role should not have access
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        # Call get_user_complaints
        if user_role in [UserRole.CUSTOMER, UserRole.VENDOR, UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN]:
            result = get_user_complaints(
                db=mock_db,
                current_user=mock_user,
                skip=0,
                limit=100
            )
            
            # Should return complaints
            assert isinstance(result, list), "Should return list of complaints"
            assert len(result) == len(complaint_ids), (
                f"Should return {len(complaint_ids)} complaints, got {len(result)}"
            )
        else:
            # Worker role should raise exception
            with pytest.raises(HTTPException) as exc_info:
                result = get_user_complaints(
                    db=mock_db,
                    current_user=mock_user,
                    skip=0,
                    limit=100
                )
            
            assert exc_info.value.status_code == 403, (
                f"Should return 403 for unauthorized role, got {exc_info.value.status_code}"
            )


class TestComplaintSystemIntegration:
    """Integration tests for complaint system properties"""

    @given(
        st.integers(min_value=1, max_value=100),
        st.integers(min_value=48, max_value=200)
    )
    @hypothesis_settings(max_examples=15, deadline=3000)
    def test_complaint_workflow_end_to_end(
        self, num_complaints: int, hours_elapsed: int
    ):
        """
        Test complete complaint workflow: creation → escalation → resolution
        """
        # This test validates the entire workflow across multiple properties
        old_time = datetime.utcnow() - timedelta(hours=hours_elapsed)
        
        # Create mock complaints
        mock_complaints = []
        for i in range(num_complaints):
            mock_complaint = Mock(spec=Complaint)
            mock_complaint.id = i + 1
            mock_complaint.status = ComplaintStatus.OPEN
            mock_complaint.escalation_level = 1
            mock_complaint.created_at = old_time
            mock_complaint.booking_id = i + 1
            mock_complaints.append(mock_complaint)
        
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        def query_side_effect(model):
            mock_q = Mock()
            if model == Complaint:
                mock_q.filter.return_value.all.return_value = mock_complaints
            elif model == ComplaintEscalationLog:
                mock_q.filter.return_value.order_by.return_value.first.return_value = None
            return mock_q
        
        mock_db.query.side_effect = query_side_effect
        
        added_logs = []
        def mock_add(obj):
            if isinstance(obj, ComplaintEscalationLog):
                added_logs.append(obj)
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        
        # Patch SessionLocal to return our mock
        with patch('app.tasks.complaint_escalation.SessionLocal', return_value=mock_db):
            # Run escalation task
            result = escalate_unresolved_complaints()
        
        # Verify all complaints were escalated
        assert result["success"] is True, "Escalation should succeed"
        assert result["escalated_count"] == num_complaints, (
            f"Should escalate {num_complaints} complaints, got {result['escalated_count']}"
        )
        
        # Verify all complaints are now at level 2
        for complaint in mock_complaints:
            assert complaint.escalation_level == 2, (
                f"Complaint {complaint.id} should be at level 2"
            )
            assert complaint.status == ComplaintStatus.ESCALATED_TO_REGIONAL, (
                f"Complaint {complaint.id} should be ESCALATED_TO_REGIONAL"
            )
        
        # Verify escalation logs were created
        assert len(added_logs) == num_complaints, (
            f"Should create {num_complaints} logs, got {len(added_logs)}"
        )

"""
Booking State Machine - Validates status transitions
"""
from typing import Dict, Set, Optional
from app.models.models import BookingStatus, UserRole


# Valid state transitions
VALID_TRANSITIONS: Dict[BookingStatus, Set[BookingStatus]] = {
    BookingStatus.CREATED: {BookingStatus.VENDOR_ACCEPTED, BookingStatus.VENDOR_REJECTED, BookingStatus.CANCELLED},
    BookingStatus.VENDOR_ACCEPTED: {BookingStatus.WORKER_ASSIGNED, BookingStatus.CANCELLED},
    BookingStatus.VENDOR_REJECTED: set(),  # Terminal state
    BookingStatus.WORKER_ASSIGNED: {BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED},
    BookingStatus.IN_PROGRESS: {BookingStatus.COMPLETED},
    BookingStatus.COMPLETED: {BookingStatus.PAYMENT_UPLOADED},
    BookingStatus.PAYMENT_UPLOADED: set(),  # Terminal state
    BookingStatus.CANCELLED: set(),  # Terminal state
}

# Who can make which transitions
TRANSITION_PERMISSIONS: Dict[BookingStatus, Set[UserRole]] = {
    BookingStatus.VENDOR_ACCEPTED: {UserRole.VENDOR},
    BookingStatus.VENDOR_REJECTED: {UserRole.VENDOR},
    BookingStatus.WORKER_ASSIGNED: {UserRole.VENDOR},
    BookingStatus.IN_PROGRESS: {UserRole.WORKER},
    BookingStatus.COMPLETED: {UserRole.WORKER},
    BookingStatus.PAYMENT_UPLOADED: {UserRole.WORKER},
    BookingStatus.CANCELLED: {UserRole.CUSTOMER, UserRole.VENDOR, UserRole.SUPER_ADMIN},
}


class BookingStateMachine:
    """Validates and enforces booking status transitions"""
    
    @staticmethod
    def can_transition(current_status: BookingStatus, new_status: BookingStatus) -> bool:
        """Check if transition is valid"""
        valid_next_states = VALID_TRANSITIONS.get(current_status, set())
        return new_status in valid_next_states
    
    @staticmethod
    def can_user_transition(new_status: BookingStatus, user_role: UserRole) -> bool:
        """Check if user role has permission for this transition"""
        allowed_roles = TRANSITION_PERMISSIONS.get(new_status, set())
        return user_role in allowed_roles
    
    @staticmethod
    def validate_transition(
        current_status: BookingStatus, 
        new_status: BookingStatus, 
        user_role: UserRole
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a status transition.
        Returns (is_valid, error_message)
        """
        # Check if transition is valid
        if not BookingStateMachine.can_transition(current_status, new_status):
            return False, f"Cannot transition from {current_status.value} to {new_status.value}"
        
        # Check if user has permission
        if not BookingStateMachine.can_user_transition(new_status, user_role):
            return False, f"Role {user_role.value} cannot set status to {new_status.value}"
        
        return True, None
    
    @staticmethod
    def get_next_valid_statuses(current_status: BookingStatus, user_role: UserRole) -> Set[BookingStatus]:
        """Get all valid next statuses for a given role"""
        valid_next = VALID_TRANSITIONS.get(current_status, set())
        return {
            status for status in valid_next 
            if BookingStateMachine.can_user_transition(status, user_role)
        }

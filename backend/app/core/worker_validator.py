"""
Worker Assignment Validator
Validates worker assignments for bookings
"""
from typing import Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.models import Worker, Booking, BookingStatus, Vendor


class WorkerValidator:
    """Validates worker assignments"""
    
    def validate_assignment(
        self,
        worker_id: int,
        booking_id: int,
        vendor_id: int,
        db: Session
    ) -> Tuple[bool, str]:
        """
        Validate worker assignment for a booking
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get worker
        worker = db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            return False, "Worker not found"
        
        # Validate worker belongs to vendor
        if worker.vendor_id != vendor_id:
            return False, "Worker does not belong to this vendor"
        
        # Check worker availability
        if not worker.is_available:
            return False, "Worker is not available"
        
        # Check for double-booking
        active_bookings = (
            db.query(Booking)
            .filter(Booking.worker_id == worker_id)
            .filter(Booking.status.in_([
                BookingStatus.WORKER_ASSIGNED,
                BookingStatus.IN_PROGRESS
            ]))
            .all()
        )
        
        if len(active_bookings) > 0:
            return False, f"Worker is already assigned to {len(active_bookings)} active booking(s)"
        
        # Check capacity (max 3 bookings per day)
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            same_day_bookings = (
                db.query(Booking)
                .filter(Booking.worker_id == worker_id)
                .filter(Booking.scheduled_time >= booking.scheduled_time.replace(hour=0, minute=0))
                .filter(Booking.scheduled_time < booking.scheduled_time.replace(hour=23, minute=59))
                .count()
            )
            
            if same_day_bookings >= 3:
                return False, "Worker has reached maximum capacity for this day (3 bookings)"
        
        return True, "Worker assignment is valid"
    
    def validate_skills(
        self,
        worker_id: int,
        service_id: int,
        db: Session
    ) -> Tuple[bool, str]:
        """
        Validate worker has required skills for service
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        from app.models.models import Service
        import json
        
        # Get worker and service
        worker = db.query(Worker).filter(Worker.id == worker_id).first()
        service = db.query(Service).filter(Service.id == service_id).first()
        
        if not worker or not service:
            return False, "Worker or service not found"
        
        # Parse skills (stored as JSON)
        worker_skills = json.loads(worker.skills) if worker.skills else []
        required_skills = json.loads(service.required_skills) if hasattr(service, 'required_skills') and service.required_skills else []
        
        # Check if worker has all required skills
        if required_skills:
            missing_skills = [skill for skill in required_skills if skill not in worker_skills]
            if missing_skills:
                return False, f"Worker missing required skills: {', '.join(missing_skills)}"
        
        return True, "Worker has required skills"


# Global instance
worker_validator = WorkerValidator()

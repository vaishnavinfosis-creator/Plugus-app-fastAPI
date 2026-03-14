"""
Review API Endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.core.database import get_db
from app.models.models import Review, Booking, Service, BookingStatus
from app.schemas.schemas import ReviewCreate, ReviewResponse
from app.api.deps import get_current_active_user
from app.models.models import User
from app.core.content_moderator import content_moderator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/bookings/{booking_id}/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    booking_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a review for a completed booking
    
    Requirements:
    - Rating must be 1-5 stars
    - Comment max 500 characters
    - Booking must be completed
    - User must be the customer of the booking
    - Only one review per booking
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
            detail="You can only review your own bookings"
        )
    
    # Verify booking is completed
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only review completed bookings"
        )
    
    # Check if review already exists
    existing_review = db.query(Review).filter(Review.booking_id == booking_id).first()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this booking"
        )
    
    # Validate rating (1-5)
    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5 stars"
        )
    
    # Validate comment length (max 500 characters)
    if review_data.comment and len(review_data.comment) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment must not exceed 500 characters"
        )
    
    # Check content for inappropriate content
    is_flagged = False
    moderation_notes = None
    if review_data.comment:
        is_flagged, reasons = content_moderator.check_content(review_data.comment)
        if is_flagged:
            moderation_notes = "; ".join(reasons)
            logger.warning(f"Review flagged for moderation: booking_id={booking_id}, reasons={reasons}")
    
    # Create review
    review = Review(
        booking_id=booking_id,
        user_id=current_user.id,
        rating=review_data.rating,
        comment=review_data.comment,
        is_flagged=is_flagged,
        is_approved=not is_flagged,  # Auto-approve if not flagged
        moderation_notes=moderation_notes
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    
    logger.info(f"Review created: booking_id={booking_id}, user_id={current_user.id}, rating={review_data.rating}, flagged={is_flagged}")
    
    return review


@router.get("/services/{service_id}/reviews", response_model=List[ReviewResponse])
def get_service_reviews(
    service_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all reviews for a service
    
    Returns reviews with ratings and comments for all completed bookings of this service
    """
    # Verify service exists
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Get all approved reviews for bookings of this service
    reviews = (
        db.query(Review)
        .join(Booking, Review.booking_id == Booking.id)
        .filter(Booking.service_id == service_id)
        .filter(Review.is_approved == True)  # Only show approved reviews
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return reviews


@router.get("/services/{service_id}/average-rating")
def get_service_average_rating(
    service_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get average rating for a service
    
    Calculates and returns the average rating from all reviews
    """
    # Verify service exists
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Calculate average rating from approved reviews only
    result = (
        db.query(
            func.avg(Review.rating).label('average_rating'),
            func.count(Review.id).label('review_count')
        )
        .join(Booking, Review.booking_id == Booking.id)
        .filter(Booking.service_id == service_id)
        .filter(Review.is_approved == True)  # Only count approved reviews
        .first()
    )
    
    average_rating = float(result.average_rating) if result.average_rating else 0.0
    review_count = result.review_count or 0
    
    return {
        "service_id": service_id,
        "average_rating": round(average_rating, 2),
        "review_count": review_count
    }



@router.get("/admin/reviews/flagged", response_model=List[ReviewResponse])
def get_flagged_reviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get all flagged reviews for admin moderation
    
    Requires: Admin role
    """
    from app.models.models import UserRole
    
    # Check if user is admin
    if current_user.role not in [UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access flagged reviews"
        )
    
    # Get all flagged reviews
    reviews = (
        db.query(Review)
        .filter(Review.is_flagged == True)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return reviews


@router.put("/admin/reviews/{review_id}/approve")
def approve_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Approve a flagged review
    
    Requires: Admin role
    """
    from app.models.models import UserRole
    
    # Check if user is admin
    if current_user.role not in [UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve reviews"
        )
    
    # Get review
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Approve review
    review.is_approved = True
    db.commit()
    db.refresh(review)
    
    logger.info(f"Review approved: review_id={review_id}, admin_id={current_user.id}")
    
    return {"message": "Review approved successfully", "review_id": review_id}


@router.put("/admin/reviews/{review_id}/reject")
def reject_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Reject a flagged review
    
    Requires: Admin role
    """
    from app.models.models import UserRole
    
    # Check if user is admin
    if current_user.role not in [UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reject reviews"
        )
    
    # Get review
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Reject review (keep flagged, set not approved)
    review.is_approved = False
    db.commit()
    db.refresh(review)
    
    logger.info(f"Review rejected: review_id={review_id}, admin_id={current_user.id}")
    
    return {"message": "Review rejected successfully", "review_id": review_id}

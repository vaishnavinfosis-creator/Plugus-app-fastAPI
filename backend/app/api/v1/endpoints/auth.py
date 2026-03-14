"""
Auth API Endpoints
"""
from datetime import timedelta
from typing import Any, Union
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.password_reset import PasswordResetService
from app.core.email_service import EmailService
from app.core.config import settings
from app.models.models import User, UserRole, Vendor, Region
from app.schemas.schemas import Token, UserCreate, UserResponse, PasswordResetRequest, PasswordResetVerify, PasswordResetConfirm, PasswordResetResponse, PasswordResetVerifyResponse, PasswordChange, PasswordChangeResponse
from app.schemas.errors import ErrorResponse, AuthErrorCodes, create_error_response
from app.api.deps import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=Token, responses={
    400: {"model": ErrorResponse, "description": "Authentication failed"},
    401: {"model": ErrorResponse, "description": "Invalid credentials"},
    404: {"model": ErrorResponse, "description": "User not found"}
})
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Login with email and password"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == form_data.username).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {form_data.username}")
            error_response = create_error_response(
                error_code=AuthErrorCodes.USER_NOT_FOUND,
                message="Email not found. Please register first.",
                details={"email": form_data.username}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response.model_dump()
            )
        
        # Verify password
        if not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Login attempt with incorrect password for user: {user.id}")
            error_response = create_error_response(
                error_code=AuthErrorCodes.INVALID_PASSWORD,
                message="Incorrect password. Please try again.",
                details={"email": form_data.username}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_response.model_dump()
            )
        
        # Check if account is active
        if not user.is_active:
            logger.warning(f"Login attempt with inactive account: {user.id}")
            error_response = create_error_response(
                error_code=AuthErrorCodes.ACCOUNT_INACTIVE,
                message="Your account has been deactivated. Please contact support.",
                details={"email": form_data.username, "user_id": user.id}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.model_dump()
            )
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(user.id, expires_delta=access_token_expires)
        
        logger.info(f"Successful login for user: {user.id}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during login: {str(e)}")
        error_response = create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            details={"error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump()
        )


@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Register new user (Customer or Vendor only)"""
    # Only customers and vendors can self-register
    # Prevent Super Admin creation through registration
    if user_in.role not in [UserRole.CUSTOMER, UserRole.VENDOR]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Customers and Vendors can self-register"
        )
    
    # Additional check to prevent Super Admin creation
    if user_in.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create Super Admin through registration. Only one Super Admin is allowed in the system."
        )
    
    # Validate region_id for vendors
    if user_in.role == UserRole.VENDOR:
        if not user_in.region_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Region selection is required for vendor registration"
            )
        
        # Verify region exists
        region = db.query(Region).filter(Region.id == user_in.region_id).first()
        if not region:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid region selected"
            )
    
    # Check if email exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Auto-create vendor profile if vendor
    if user.role == UserRole.VENDOR:
        vendor = Vendor(
            user_id=user.id,
            region_id=user_in.region_id,
            business_name=f"Vendor {user.id}",
            is_approved=False,  # Requires admin approval
            is_visible=False
        )
        db.add(vendor)
        db.commit()
    
    return user


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current user info"""
    return current_user
@router.post("/logout", response_model=dict)
def logout(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Logout current user

    Note: Since we use JWT tokens, actual token invalidation happens client-side.
    This endpoint serves as a confirmation that the logout request was received.
    In a production system with token blacklisting, this would invalidate the token.
    """
    logger.info(f"User logged out: {current_user.id}")
    return {"message": "Successfully logged out"}



@router.post("/password-reset/request", response_model=PasswordResetResponse, responses={
    404: {"model": ErrorResponse, "description": "User not found"},
    400: {"model": ErrorResponse, "description": "Invalid request"}
})
def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Request password reset for Super Admin
    Generates a secure token and sends reset email
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="If this email exists in our system, you will receive a password reset link."
            )
        
        # Verify user is Super Admin (only Super Admins can reset password via this endpoint)
        if user.role != UserRole.SUPER_ADMIN:
            logger.warning(f"Password reset requested for non-Super Admin user: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset is only available for Super Admin accounts."
            )
        
        # Verify only one Super Admin exists
        if not PasswordResetService.verify_single_super_admin(db):
            logger.error("Multiple Super Admin accounts detected in system")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System configuration error. Please contact support."
            )
        
        # Generate reset token
        token = PasswordResetService.generate_reset_token(db, user.id)
        
        # Send reset email
        email_sent = EmailService.send_password_reset_email(user.email, token)
        
        if not email_sent:
            logger.error(f"Failed to send password reset email to: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email. Please try again later."
            )
        
        logger.info(f"Password reset email sent to: {user.email}")
        return PasswordResetResponse(
            message="If this email exists in our system, you will receive a password reset link."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password reset request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.post("/password-reset/verify", response_model=PasswordResetVerifyResponse, responses={
    400: {"model": ErrorResponse, "description": "Invalid or expired token"}
})
def verify_password_reset_token(
    request: PasswordResetVerify,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify a password reset token
    Returns whether the token is valid and the associated user_id
    """
    try:
        # Validate the token
        user_id = PasswordResetService.validate_reset_token(db, request.token)
        
        if not user_id:
            logger.warning("Invalid or expired password reset token provided")
            return PasswordResetVerifyResponse(valid=False, user_id=None)
        
        logger.info(f"Password reset token verified for user: {user_id}")
        return PasswordResetVerifyResponse(valid=True, user_id=user_id)
        
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.post("/password-reset/confirm", response_model=PasswordResetResponse, responses={
    400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    404: {"model": ErrorResponse, "description": "User not found"}
})
def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Any:
    """
    Confirm password reset with valid token and new password
    Resets the user's password and marks the token as used
    """
    try:
        # Reset the password
        success = PasswordResetService.reset_password(db, request.token, request.new_password)
        
        if not success:
            logger.warning("Password reset failed - invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token. Please request a new password reset."
            )
        
        logger.info("Password reset completed successfully")
        return PasswordResetResponse(
            message="Password has been reset successfully. You can now log in with your new password."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password reset confirmation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )



@router.post("/change-password", response_model=PasswordChangeResponse, responses={
    400: {"model": ErrorResponse, "description": "Invalid current password"},
    401: {"model": ErrorResponse, "description": "Unauthorized"}
})
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Change password for authenticated user"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            logger.warning(f"Password change attempt with incorrect current password for user: {current_user.id}")
            error_response = create_error_response(
                error_code=AuthErrorCodes.INVALID_PASSWORD,
                message="Current password is incorrect.",
                details={"user_id": current_user.id}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.model_dump()
            )
        
        # Update password
        current_user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()
        
        logger.info(f"Password changed successfully for user: {current_user.id}")
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password change: {str(e)}")
        db.rollback()
        error_response = create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            details={"error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump()
        )


@router.get("/regions")
def get_public_regions(
    db: Session = Depends(get_db)
) -> Any:
    """Get all active regions (public endpoint for vendor registration)"""
    from app.models.models import Region
    
    regions = db.query(Region).filter(Region.is_active == True).all()
    
    # Return as dict to avoid serialization issues
    return [
        {
            "id": region.id,
            "name": region.name,
            "state": region.state,
            "description": region.description,
            "is_active": region.is_active
        }
        for region in regions
    ]


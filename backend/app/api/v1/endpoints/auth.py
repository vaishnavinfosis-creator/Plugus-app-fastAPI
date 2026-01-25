"""
Auth API Endpoints
"""
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.models import User, UserRole, Vendor, Region
from app.schemas.schemas import Token, UserCreate, UserResponse
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Login with email and password"""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please register first."
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(user.id, expires_delta=access_token_expires),
        "token_type": "bearer"
    }


@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Register new user (Customer or Vendor only)"""
    # Only customers and vendors can self-register
    if user_in.role not in [UserRole.CUSTOMER, UserRole.VENDOR]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Customers and Vendors can self-register"
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
        # Get first region or create default
        region = db.query(Region).first()
        if not region:
            region = Region(name="Default Region")
            db.add(region)
            db.commit()
            db.refresh(region)
        
        vendor = Vendor(
            user_id=user.id,
            region_id=region.id,
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

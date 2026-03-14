"""
API Dependencies - Auth and RBAC
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.database import get_db
from app.core.security import decode_token
from app.models.models import User, UserRole
from app.schemas.errors import ErrorResponse, AuthErrorCodes
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get current authenticated user from JWT token"""
    
    # First, check if token is expired by trying to decode it directly
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        # Token has expired - return specific error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=AuthErrorCodes.TOKEN_EXPIRED,
                message="Your session has expired. Please log in again.",
                details=None
            ).dict(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        # Other JWT errors (invalid signature, malformed token, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=AuthErrorCodes.TOKEN_INVALID,
                message="Could not validate credentials",
                details=None
            ).dict(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Now decode to get user_id
    user_id = decode_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=AuthErrorCodes.TOKEN_INVALID,
                message="Could not validate credentials",
                details=None
            ).dict(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=AuthErrorCodes.USER_NOT_FOUND,
                message="User not found",
                details=None
            ).dict(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class RoleChecker:
    """Dependency for checking user roles (RBAC)"""
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return user


# Pre-defined role checkers
require_customer = RoleChecker([UserRole.CUSTOMER])
require_vendor = RoleChecker([UserRole.VENDOR])
require_worker = RoleChecker([UserRole.WORKER])
require_regional_admin = RoleChecker([UserRole.REGIONAL_ADMIN])
require_super_admin = RoleChecker([UserRole.SUPER_ADMIN])
require_any_admin = RoleChecker([UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN])

"""
Password Reset Service
Handles secure password reset token generation, validation, and password reset logic
"""
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
from sqlalchemy.orm import Session
from jose import jwt

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.models import PasswordResetToken, User, UserRole


class PasswordResetService:
    """Service for handling password reset operations"""
    
    TOKEN_EXPIRY_HOURS = 1
    
    @staticmethod
    def generate_reset_token(db: Session, user_id: int) -> str:
        """
        Generate a secure reset token for a user
        
        Args:
            db: Database session
            user_id: ID of the user requesting password reset
            
        Returns:
            The plain token string to be sent to the user
        """
        # Generate a secure random token
        plain_token = secrets.token_urlsafe(32)
        
        # Hash the token for storage
        token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
        
        # Calculate expiration time (1 hour from now)
        expires_at = datetime.utcnow() + timedelta(hours=PasswordResetService.TOKEN_EXPIRY_HOURS)
        
        # Create token record in database
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        
        db.add(reset_token)
        db.commit()
        
        return plain_token
    
    @staticmethod
    def validate_reset_token(db: Session, token: str) -> Optional[int]:
        """
        Validate a reset token and return the associated user_id
        
        Args:
            db: Database session
            token: The plain token string from the user
            
        Returns:
            user_id if token is valid, None otherwise
        """
        # Hash the provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Find the token in database
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()
        
        if not reset_token:
            return None
        
        # Check if token has been used
        if reset_token.used:
            return None
        
        # Check if token has expired
        if datetime.utcnow() > reset_token.expires_at:
            return None
        
        return reset_token.user_id
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """
        Reset a user's password using a valid token
        
        Args:
            db: Database session
            token: The plain token string from the user
            new_password: The new password to set
            
        Returns:
            True if password was reset successfully, False otherwise
        """
        # Validate the token
        user_id = PasswordResetService.validate_reset_token(db, token)
        
        if not user_id:
            return False
        
        # Get the user
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False
        
        # Update the password
        user.hashed_password = get_password_hash(new_password)
        
        # Mark the token as used
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()
        
        if reset_token:
            reset_token.used = True
        
        db.commit()
        
        return True
    
    @staticmethod
    def verify_single_super_admin(db: Session) -> bool:
        """
        Verify that only one Super Admin exists in the system
        
        Args:
            db: Database session
            
        Returns:
            True if exactly one Super Admin exists, False otherwise
        """
        super_admin_count = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN,
            User.is_active == True
        ).count()
        
        return super_admin_count == 1
    
    @staticmethod
    def get_super_admin_email(db: Session) -> Optional[str]:
        """
        Get the email of the Super Admin
        
        Args:
            db: Database session
            
        Returns:
            Email of the Super Admin if exists, None otherwise
        """
        super_admin = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN,
            User.is_active == True
        ).first()
        
        return super_admin.email if super_admin else None

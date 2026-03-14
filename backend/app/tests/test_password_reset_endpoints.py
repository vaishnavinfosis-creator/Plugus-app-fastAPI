"""
Unit tests for password reset API endpoints
Tests the three password reset endpoints: request, verify, and confirm
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import User, UserRole, PasswordResetToken
from app.core.security import get_password_hash, verify_password


def test_password_reset_request_success(client: TestClient, db: Session, super_admin_user: User):
    """Test successful password reset request for Super Admin"""
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": super_admin_user.email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "email exists" in data["message"].lower()
    
    # Verify token was created in database
    token = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == super_admin_user.id
    ).first()
    assert token is not None
    assert token.used is False


def test_password_reset_request_nonexistent_email(client: TestClient):
    """Test password reset request with non-existent email"""
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "nonexistent@example.com"}
    )
    
    # Should return 404 but with generic message for security
    assert response.status_code == 404


def test_password_reset_request_non_super_admin(client: TestClient, db: Session):
    """Test password reset request for non-Super Admin user"""
    # Create a regular customer user
    customer = User(
        email="customer@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(customer)
    db.commit()
    
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": customer.email}
    )
    
    assert response.status_code == 400
    assert "Super Admin" in response.json()["detail"]


def test_password_reset_verify_valid_token(client: TestClient, db: Session, super_admin_user: User):
    """Test verifying a valid password reset token"""
    # First request a password reset
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": super_admin_user.email}
    )
    assert response.status_code == 200
    
    # Get the token from database (in real scenario, user gets it from email)
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == super_admin_user.id
    ).first()
    
    # We need to get the plain token - for testing, we'll create a new one
    from app.core.password_reset import PasswordResetService
    plain_token = PasswordResetService.generate_reset_token(db, super_admin_user.id)
    
    # Verify the token
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={"token": plain_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user_id"] == super_admin_user.id


def test_password_reset_verify_invalid_token(client: TestClient):
    """Test verifying an invalid password reset token"""
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={"token": "invalid_token_12345"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["user_id"] is None


def test_password_reset_confirm_success(client: TestClient, db: Session, super_admin_user: User):
    """Test successful password reset confirmation"""
    # Generate a reset token
    from app.core.password_reset import PasswordResetService
    plain_token = PasswordResetService.generate_reset_token(db, super_admin_user.id)
    
    # Get the old password hash
    old_password_hash = super_admin_user.hashed_password
    
    # Confirm password reset with new password
    new_password = "new_secure_password_123"
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": plain_token,
            "new_password": new_password
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "successfully" in data["message"].lower()
    
    # Verify password was changed
    db.refresh(super_admin_user)
    assert super_admin_user.hashed_password != old_password_hash
    assert verify_password(new_password, super_admin_user.hashed_password)
    
    # Verify token was marked as used
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == super_admin_user.id
    ).order_by(PasswordResetToken.created_at.desc()).first()
    assert token_record.used is True


def test_password_reset_confirm_invalid_token(client: TestClient):
    """Test password reset confirmation with invalid token"""
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": "invalid_token_12345",
            "new_password": "new_password_123"
        }
    )
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_password_reset_confirm_used_token(client: TestClient, db: Session, super_admin_user: User):
    """Test password reset confirmation with already used token"""
    # Generate and use a token
    from app.core.password_reset import PasswordResetService
    plain_token = PasswordResetService.generate_reset_token(db, super_admin_user.id)
    
    # Use the token once
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": plain_token,
            "new_password": "first_password_123"
        }
    )
    assert response.status_code == 200
    
    # Try to use the same token again
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": plain_token,
            "new_password": "second_password_123"
        }
    )
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_password_reset_flow_end_to_end(client: TestClient, db: Session, super_admin_user: User):
    """Test complete password reset flow from request to confirmation"""
    original_password = "original_password"
    new_password = "new_secure_password_456"
    
    # Set a known password
    super_admin_user.hashed_password = get_password_hash(original_password)
    db.commit()
    
    # Step 1: Request password reset
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": super_admin_user.email}
    )
    assert response.status_code == 200
    
    # Step 2: Get token (simulating email retrieval)
    from app.core.password_reset import PasswordResetService
    plain_token = PasswordResetService.generate_reset_token(db, super_admin_user.id)
    
    # Step 3: Verify token
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={"token": plain_token}
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True
    
    # Step 4: Confirm password reset
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": plain_token,
            "new_password": new_password
        }
    )
    assert response.status_code == 200
    
    # Step 5: Verify can login with new password
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": super_admin_user.email,
            "password": new_password
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Step 6: Verify cannot login with old password
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": super_admin_user.email,
            "password": original_password
        }
    )
    assert response.status_code == 401

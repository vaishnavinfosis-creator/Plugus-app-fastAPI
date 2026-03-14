"""
Tests for logout endpoint
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.models import User, UserRole
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)


@pytest.fixture
def test_vendor_user(db: Session):
    """Create a test vendor user"""
    user = User(
        email="vendor@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VENDOR,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_customer_user(db: Session):
    """Create a test customer user"""
    user = User(
        email="customer@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestLogoutEndpoint:
    """Test logout functionality for all user roles"""
    
    def test_vendor_can_logout(self, client: TestClient, test_vendor_user: User):
        """Test that vendor can successfully logout (Requirement 9.1)"""
        # Create access token for vendor
        token = create_access_token(test_vendor_user.id)
        
        # Call logout endpoint
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    def test_customer_can_logout(self, client: TestClient, test_customer_user: User):
        """Test that customer can successfully logout (Requirement 11.1)"""
        # Create access token for customer
        token = create_access_token(test_customer_user.id)
        
        # Call logout endpoint
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    def test_logout_requires_authentication(self, client: TestClient):
        """Test that logout endpoint requires authentication"""
        # Call logout without token
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401
    
    def test_logout_with_invalid_token(self, client: TestClient):
        """Test that logout with invalid token returns 401"""
        # Call logout with invalid token
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_protected_endpoint_requires_valid_token(self, client: TestClient, test_vendor_user: User):
        """Test that protected endpoints require valid authentication (Requirement 9.3, 11.3)"""
        # Try to access protected endpoint without token
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        
        # Try with invalid token
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        
        # Try with valid token - should work
        token = create_access_token(test_vendor_user.id)
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == test_vendor_user.email

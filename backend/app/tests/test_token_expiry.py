"""
Unit tests for token expiry handling
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.schemas.errors import AuthErrorCodes


def test_expired_token_returns_specific_error(client: TestClient):
    """Test that expired tokens return TOKEN_EXPIRED error code"""
    
    # Create an expired token (expired 1 hour ago)
    expire = datetime.utcnow() - timedelta(hours=1)
    expired_token_data = {"exp": expire, "sub": "999"}
    expired_token = jwt.encode(expired_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Try to access a protected endpoint with expired token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    # Should return 401
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    # Should have TOKEN_EXPIRED error code
    response_data = response.json()
    assert "detail" in response_data, "Response should have detail field"
    
    detail = response_data["detail"]
    if isinstance(detail, dict):
        assert detail.get("error_code") == AuthErrorCodes.TOKEN_EXPIRED, \
            f"Expected TOKEN_EXPIRED error code, got {detail.get('error_code')}"
        assert "expired" in detail.get("message", "").lower(), \
            "Error message should mention expiration"


def test_invalid_token_returns_token_invalid_error(client: TestClient):
    """Test that invalid tokens return TOKEN_INVALID error code"""
    
    # Create a token with invalid signature
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTkifQ.invalid_signature"
    
    # Try to access a protected endpoint with invalid token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    # Should return 401
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    # Should have TOKEN_INVALID error code
    response_data = response.json()
    assert "detail" in response_data, "Response should have detail field"
    
    detail = response_data["detail"]
    if isinstance(detail, dict):
        assert detail.get("error_code") == AuthErrorCodes.TOKEN_INVALID, \
            f"Expected TOKEN_INVALID error code, got {detail.get('error_code')}"


def test_missing_token_returns_401(client: TestClient):
    """Test that missing token returns 401"""
    
    # Try to access a protected endpoint without token
    response = client.get("/api/v1/auth/me")
    
    # Should return 401
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

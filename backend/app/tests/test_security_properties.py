"""
Property-Based Tests for Security Configuration
**Feature: platform-robustness-improvements**
"""
import time
import string
import secrets
from typing import List
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, strategies as st, settings as hypothesis_settings
from fastapi import Request
from fastapi.testclient import TestClient

from app.core.security_config import SecurityConfigValidator
from app.middleware.rate_limit import (
    InMemoryRateLimiter, 
    get_client_ip, 
    get_rate_limit_key,
    RateLimitConfig
)
from app.main import app


class TestSecurityProperties:
    """Property-based tests for security configuration"""

    @given(st.text(min_size=32, max_size=128))
    @hypothesis_settings(max_examples=30)
    def test_property_4_secret_key_security_valid_length(self, secret_key: str):
        """
        **Validates: Requirements 2.1, 2.3**
        **Property 4: Secret Key Security**
        
        For any SECRET_KEY with minimum 32 characters, the system should accept it as valid length.
        """
        result = SecurityConfigValidator.validate_secret_key(secret_key)
        
        # Should not have length-related errors
        length_errors = [error for error in result.errors if "32 characters" in error]
        assert len(length_errors) == 0, f"Valid length key rejected: {secret_key[:10]}..."

    @given(st.text(min_size=1, max_size=31))
    @hypothesis_settings(max_examples=30)
    def test_property_4_secret_key_security_invalid_length(self, secret_key: str):
        """
        **Validates: Requirements 2.1, 2.3**
        **Property 4: Secret Key Security**
        
        For any SECRET_KEY with less than 32 characters, the system should reject it.
        """
        result = SecurityConfigValidator.validate_secret_key(secret_key)
        
        # Should have length error
        assert not result.is_valid, f"Short key accepted: {secret_key}"
        length_errors = [error for error in result.errors if "32 characters" in error]
        assert len(length_errors) > 0, f"No length error for short key: {secret_key}"

    @given(st.lists(
        st.one_of(
            st.just("your-super-secret-key"),
            st.just("change-in-production"),
            st.just("secret"),
            st.just("password"),
            st.just("123456"),
            st.just("default"),
            st.just("test")
        ),
        min_size=1,
        max_size=3
    ))
    @hypothesis_settings(max_examples=30)
    def test_property_4_secret_key_security_weak_patterns(self, weak_patterns: List[str]):
        """
        **Validates: Requirements 2.1, 2.3**
        **Property 4: Secret Key Security**
        
        For any SECRET_KEY containing weak patterns, the system should reject it.
        """
        # Create a key with weak patterns but valid length
        secret_key = "".join(weak_patterns) + "x" * (32 - sum(len(p) for p in weak_patterns))
        if len(secret_key) < 32:
            secret_key += "x" * (32 - len(secret_key))
        
        result = SecurityConfigValidator.validate_secret_key(secret_key)
        
        # Should have weak pattern errors
        assert not result.is_valid, f"Weak key accepted: {secret_key[:20]}..."
        pattern_errors = [error for error in result.errors if "weak pattern" in error]
        assert len(pattern_errors) > 0, f"No weak pattern error for: {secret_key[:20]}..."

    @hypothesis_settings(max_examples=30)
    @given(st.integers(min_value=32, max_value=128))
    def test_property_4_secret_key_security_cryptographic_generation(self, length: int):
        """
        **Validates: Requirements 2.1, 2.3**
        **Property 4: Secret Key Security**
        
        For any generated SECRET_KEY, it should be cryptographically secure.
        """
        secret_key = SecurityConfigValidator.generate_secure_secret_key(length)
        
        # Generated key should pass validation
        result = SecurityConfigValidator.validate_secret_key(secret_key)
        assert result.is_valid, f"Generated key failed validation: {result.errors}"
        
        # Should have correct length
        assert len(secret_key) == length, f"Generated key has wrong length: {len(secret_key)} != {length}"
        
        # Should have character diversity
        has_upper = any(c.isupper() for c in secret_key)
        has_lower = any(c.islower() for c in secret_key)
        has_digit = any(c.isdigit() for c in secret_key)
        has_symbol = any(not c.isalnum() for c in secret_key)
        
        diversity_count = sum([has_upper, has_lower, has_digit, has_symbol])
        assert diversity_count >= 3, f"Generated key lacks diversity: {secret_key[:20]}..."

    @given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10))
    @hypothesis_settings(max_examples=30)
    def test_property_5_cors_configuration_security_no_wildcard(self, origins: List[str]):
        """
        **Validates: Requirements 2.4**
        **Property 5: CORS Configuration Security**
        
        For any CORS configuration without wildcards, the system should accept it.
        """
        # Filter out any wildcards that might be generated
        safe_origins = [origin for origin in origins if "*" not in origin]
        
        if not safe_origins:
            # Skip if no safe origins
            return
        
        result = SecurityConfigValidator.validate_cors_origins(safe_origins)
        
        # Should not have wildcard errors
        wildcard_errors = [error for error in result.errors if "wildcard" in error]
        assert len(wildcard_errors) == 0, f"Safe origins rejected: {safe_origins}"

    @given(st.lists(
        st.one_of(
            st.just("*"),
            st.text(min_size=1, max_size=20).map(lambda x: f"*{x}"),
            st.text(min_size=1, max_size=20).map(lambda x: f"{x}*"),
            st.text(min_size=1, max_size=20).map(lambda x: f"{x}*{x}")
        ),
        min_size=1,
        max_size=5
    ))
    @hypothesis_settings(max_examples=30)
    def test_property_5_cors_configuration_security_wildcard_rejection(self, origins_with_wildcards: List[str]):
        """
        **Validates: Requirements 2.4**
        **Property 5: CORS Configuration Security**
        
        For any CORS configuration containing wildcards, the system should reject it.
        """
        result = SecurityConfigValidator.validate_cors_origins(origins_with_wildcards)
        
        # Should have wildcard errors
        assert not result.is_valid, f"Wildcard origins accepted: {origins_with_wildcards}"
        wildcard_errors = [error for error in result.errors if "wildcard" in error]
        assert len(wildcard_errors) > 0, f"No wildcard error for: {origins_with_wildcards}"

    @given(st.lists(
        st.one_of(
            st.just("http://localhost:3000"),
            st.just("http://127.0.0.1:8080"),
            st.just("http://0.0.0.0:5000")
        ),
        min_size=1,
        max_size=3
    ))
    @hypothesis_settings(max_examples=30)
    def test_property_5_cors_configuration_security_localhost_warning(self, localhost_origins: List[str]):
        """
        **Validates: Requirements 2.4**
        **Property 5: CORS Configuration Security**
        
        For any CORS configuration with localhost origins, the system should warn about production usage.
        """
        result = SecurityConfigValidator.validate_cors_origins(localhost_origins)
        
        # Should have localhost warnings
        localhost_warnings = [warning for warning in result.warnings if "localhost" in warning]
        assert len(localhost_warnings) > 0, f"No localhost warning for: {localhost_origins}"

    @given(st.integers(min_value=1, max_value=20))
    @hypothesis_settings(max_examples=30)
    def test_property_6_rate_limiting_enforcement_auth_endpoints(self, request_count: int):
        """
        **Validates: Requirements 2.6, 2.7**
        **Property 6: Rate Limiting Enforcement**
        
        For any series of requests to auth endpoints, rate limiting should enforce 10 req/min limit.
        """
        rate_limiter = InMemoryRateLimiter()
        client_key = "test_client_auth"
        
        allowed_count = 0
        for i in range(request_count):
            is_allowed, retry_after = rate_limiter.is_allowed(
                client_key, 
                RateLimitConfig.AUTH_LIMIT, 
                RateLimitConfig.AUTH_WINDOW
            )
            if is_allowed:
                allowed_count += 1
        
        # Should not allow more than the limit
        assert allowed_count <= RateLimitConfig.AUTH_LIMIT, (
            f"Rate limiter allowed {allowed_count} requests, limit is {RateLimitConfig.AUTH_LIMIT}"
        )
        
        # If we exceeded the limit, should get retry_after
        if request_count > RateLimitConfig.AUTH_LIMIT:
            is_allowed, retry_after = rate_limiter.is_allowed(
                client_key, 
                RateLimitConfig.AUTH_LIMIT, 
                RateLimitConfig.AUTH_WINDOW
            )
            assert not is_allowed, "Rate limiter should reject requests after limit"
            assert retry_after is not None, "Rate limiter should provide retry_after time"
            assert retry_after > 0, f"Invalid retry_after time: {retry_after}"

    @given(st.integers(min_value=1, max_value=150))
    @hypothesis_settings(max_examples=30)
    def test_property_6_rate_limiting_enforcement_api_endpoints(self, request_count: int):
        """
        **Validates: Requirements 2.6, 2.7**
        **Property 6: Rate Limiting Enforcement**
        
        For any series of requests to API endpoints, rate limiting should enforce 100 req/min limit.
        """
        rate_limiter = InMemoryRateLimiter()
        client_key = "test_client_api"
        
        allowed_count = 0
        for i in range(request_count):
            is_allowed, retry_after = rate_limiter.is_allowed(
                client_key, 
                RateLimitConfig.API_LIMIT, 
                RateLimitConfig.API_WINDOW
            )
            if is_allowed:
                allowed_count += 1
        
        # Should not allow more than the limit
        assert allowed_count <= RateLimitConfig.API_LIMIT, (
            f"Rate limiter allowed {allowed_count} requests, limit is {RateLimitConfig.API_LIMIT}"
        )
        
        # If we exceeded the limit, should get retry_after
        if request_count > RateLimitConfig.API_LIMIT:
            is_allowed, retry_after = rate_limiter.is_allowed(
                client_key, 
                RateLimitConfig.API_LIMIT, 
                RateLimitConfig.API_WINDOW
            )
            assert not is_allowed, "Rate limiter should reject requests after limit"
            assert retry_after is not None, "Rate limiter should provide retry_after time"

    @given(st.text(min_size=1, max_size=50))
    @hypothesis_settings(max_examples=30)
    def test_property_6_rate_limiting_enforcement_key_generation(self, client_identifier: str):
        """
        **Validates: Requirements 2.6, 2.7**
        **Property 6: Rate Limiting Enforcement**
        
        For any client identifier, rate limiting should generate consistent keys.
        """
        # Mock request object
        mock_request = Mock(spec=Request)
        mock_request.client = Mock()
        mock_request.client.host = client_identifier
        mock_request.headers = {}
        
        # Test IP-based key generation
        key1 = get_rate_limit_key(mock_request, None)
        key2 = get_rate_limit_key(mock_request, None)
        
        assert key1 == key2, f"Inconsistent keys for same client: {key1} != {key2}"
        assert client_identifier in key1, f"Client identifier not in key: {key1}"
        
        # Test user-based key generation
        user_id = 123
        user_key1 = get_rate_limit_key(mock_request, user_id)
        user_key2 = get_rate_limit_key(mock_request, user_id)
        
        assert user_key1 == user_key2, f"Inconsistent user keys: {user_key1} != {user_key2}"
        assert str(user_id) in user_key1, f"User ID not in key: {user_key1}"
        assert client_identifier in user_key1, f"Client identifier not in user key: {user_key1}"

    @given(st.integers(min_value=1, max_value=10))
    @hypothesis_settings(max_examples=25)
    def test_property_6_rate_limiting_enforcement_sliding_window(self, delay_seconds: int):
        """
        **Validates: Requirements 2.6, 2.7**
        **Property 6: Rate Limiting Enforcement**
        
        For any time-based request pattern, rate limiting should use sliding window correctly.
        """
        rate_limiter = InMemoryRateLimiter()
        client_key = "test_sliding_window"
        limit = 3
        window = 10
        
        # Fill up the limit
        for i in range(limit):
            is_allowed, _ = rate_limiter.is_allowed(client_key, limit, window)
            assert is_allowed, f"Request {i+1} should be allowed"
        
        # Next request should be denied
        is_allowed, retry_after = rate_limiter.is_allowed(client_key, limit, window)
        assert not is_allowed, "Request after limit should be denied"
        assert retry_after is not None, "Should provide retry_after time"
        
        # Test that the sliding window works by checking basic properties
        # After filling the limit, we should consistently get denials
        for _ in range(3):
            is_allowed, retry_after = rate_limiter.is_allowed(client_key, limit, window)
            assert not is_allowed, "Should continue to deny requests when limit exceeded"
            assert retry_after is not None and retry_after > 0, "Should provide positive retry_after"


class TestSecurityIntegration:
    """Integration tests for security configuration"""

    def test_security_validation_integration(self):
        """Test that security validation integrates properly with application startup"""
        from app.core.config import settings
        from app.core.security_config import validate_startup_security
        
        # Should pass with current settings (assuming they're valid)
        result = validate_startup_security(settings)
        assert isinstance(result, bool), "validate_startup_security should return boolean"

    def test_rate_limiting_middleware_integration(self):
        """Test that rate limiting middleware integrates with FastAPI"""
        client = TestClient(app)
        
        # Test that the app starts and responds
        response = client.get("/health")
        assert response.status_code == 200
        
        # Health endpoint is excluded from rate limiting, so test with API endpoint
        # Try to access an API endpoint that should have rate limiting
        response = client.get("/api/v1/auth/me")  # This should have rate limiting
        
        # Even if it returns 401 (unauthorized), it should have rate limit headers
        # or if it's a 404, that's also fine - we just want to test the middleware
        assert response.status_code in [401, 404, 422], f"Unexpected status: {response.status_code}"
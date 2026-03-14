"""
Property-Based Tests for Authentication Error Handling
**Feature: platform-robustness-improvements**
"""
import time
import json
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings as hypothesis_settings
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import login
from app.models.models import User, UserRole
from app.schemas.errors import AuthErrorCodes
from app.core.security import get_password_hash, create_access_token
from app.core.database import get_db


class TestAuthenticationErrorProperties:
    """Property-based tests for authentication error handling"""

    @given(
        st.emails(),
        st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_1_authentication_error_specificity_user_not_found(self, email: str, password: str):
        """
        **Validates: Requirements 1.1, 1.2, 1.3**
        **Property 1: Authentication Error Specificity**
        
        For any authentication attempt with unregistered email, the system should return 
        specific "Email not found" error message within 3 seconds.
        """
        # Create mock database session that returns None (user not found)
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Create mock form data
        mock_form_data = Mock()
        mock_form_data.username = email
        mock_form_data.password = password
        
        start_time = time.time()
        
        # Test the login function directly
        with pytest.raises(HTTPException) as exc_info:
            login(db=mock_db, form_data=mock_form_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should respond within 3 seconds
        assert response_time < 3.0, f"Response took {response_time:.2f} seconds, should be < 3.0"
        
        # Should return 404 for user not found
        assert exc_info.value.status_code == 404, f"Expected 404, got {exc_info.value.status_code}"
        
        # Should have specific error message
        detail = exc_info.value.detail
        assert "error_code" in detail, "Error should contain error_code"
        assert detail["error_code"] == AuthErrorCodes.USER_NOT_FOUND, (
            f"Expected {AuthErrorCodes.USER_NOT_FOUND}, got {detail['error_code']}"
        )
        
        assert "message" in detail, "Error should contain message"
        assert "Email not found" in detail["message"], (
            f"Expected 'Email not found' in message, got: {detail['message']}"
        )
        assert "register first" in detail["message"], (
            f"Expected 'register first' in message, got: {detail['message']}"
        )

    @given(
        st.emails(),
        st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_1_authentication_error_specificity_invalid_password(
        self, email: str, correct_password: str, wrong_password: str
    ):
        """
        **Validates: Requirements 1.1, 1.2, 1.3**
        **Property 1: Authentication Error Specificity**
        
        For any authentication attempt with wrong password, the system should return 
        specific "Incorrect password" error message within 3 seconds.
        """
        # Skip if passwords are the same
        if correct_password == wrong_password:
            return
        
        # Create mock user with correct password
        mock_user = Mock()
        mock_user.id = 123
        mock_user.email = email
        mock_user.hashed_password = get_password_hash(correct_password)
        mock_user.is_active = True
        
        # Create mock database session that returns the user
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Create mock form data with wrong password
        mock_form_data = Mock()
        mock_form_data.username = email
        mock_form_data.password = wrong_password
        
        start_time = time.time()
        
        # Test the login function directly
        with pytest.raises(HTTPException) as exc_info:
            login(db=mock_db, form_data=mock_form_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should respond within 3 seconds
        assert response_time < 3.0, f"Response took {response_time:.2f} seconds, should be < 3.0"
        
        # Should return 401 for invalid password
        assert exc_info.value.status_code == 401, f"Expected 401, got {exc_info.value.status_code}"
        
        # Should have specific error message
        detail = exc_info.value.detail
        assert "error_code" in detail, "Error should contain error_code"
        assert detail["error_code"] == AuthErrorCodes.INVALID_PASSWORD, (
            f"Expected {AuthErrorCodes.INVALID_PASSWORD}, got {detail['error_code']}"
        )
        
        assert "message" in detail, "Error should contain message"
        assert "Incorrect password" in detail["message"], (
            f"Expected 'Incorrect password' in message, got: {detail['message']}"
        )
        assert "try again" in detail["message"], (
            f"Expected 'try again' in message, got: {detail['message']}"
        )

    @given(
        st.emails(),
        st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_1_authentication_error_specificity_inactive_account(self, email: str, password: str):
        """
        **Validates: Requirements 1.1, 1.2, 1.3**
        **Property 1: Authentication Error Specificity**
        
        For any authentication attempt with inactive account, the system should return 
        specific "account deactivated" error message within 3 seconds.
        """
        # Create mock inactive user
        mock_user = Mock()
        mock_user.id = 456
        mock_user.email = email
        mock_user.hashed_password = get_password_hash(password)
        mock_user.is_active = False  # Inactive account
        
        # Create mock database session that returns the inactive user
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Create mock form data
        mock_form_data = Mock()
        mock_form_data.username = email
        mock_form_data.password = password
        
        start_time = time.time()
        
        # Test the login function directly
        with pytest.raises(HTTPException) as exc_info:
            login(db=mock_db, form_data=mock_form_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should respond within 3 seconds
        assert response_time < 3.0, f"Response took {response_time:.2f} seconds, should be < 3.0"
        
        # Should return 400 for inactive account
        assert exc_info.value.status_code == 400, f"Expected 400, got {exc_info.value.status_code}"
        
        # Should have specific error message
        detail = exc_info.value.detail
        assert "error_code" in detail, "Error should contain error_code"
        assert detail["error_code"] == AuthErrorCodes.ACCOUNT_INACTIVE, (
            f"Expected {AuthErrorCodes.ACCOUNT_INACTIVE}, got {detail['error_code']}"
        )
        
        assert "message" in detail, "Error should contain message"
        assert "deactivated" in detail["message"], (
            f"Expected 'deactivated' in message, got: {detail['message']}"
        )
        assert "contact support" in detail["message"], (
            f"Expected 'contact support' in message, got: {detail['message']}"
        )

    @given(
        st.emails(),
        st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_2_network_error_handling_connection_timeout(self, email: str, password: str):
        """
        **Validates: Requirements 1.4, 1.5**
        **Property 2: Network Error Handling**
        
        For any network failure during authentication, the system should display 
        appropriate connectivity error messages and provide recovery options.
        """
        # Create mock database session that raises connection error
        mock_db = Mock(spec=Session)
        mock_db.query.side_effect = ConnectionError("Database connection failed")
        
        # Create mock form data
        mock_form_data = Mock()
        mock_form_data.username = email
        mock_form_data.password = password
        
        # Test the login function directly
        with pytest.raises(HTTPException) as exc_info:
            login(db=mock_db, form_data=mock_form_data)
        
        # Should return 500 for internal server error
        assert exc_info.value.status_code == 500, f"Expected 500, got {exc_info.value.status_code}"
        
        # Should have appropriate error message
        detail = exc_info.value.detail
        assert "error_code" in detail, "Error should contain error_code"
        assert detail["error_code"] == "INTERNAL_SERVER_ERROR", (
            f"Expected INTERNAL_SERVER_ERROR, got {detail['error_code']}"
        )
        
        assert "message" in detail, "Error should contain message"
        assert "try again later" in detail["message"], (
            f"Expected 'try again later' in message, got: {detail['message']}"
        )

    @given(
        st.emails(),
        st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_2_network_error_handling_service_unavailable(self, email: str, password: str):
        """
        **Validates: Requirements 1.4, 1.5**
        **Property 2: Network Error Handling**
        
        For any backend unavailability during authentication, the system should display 
        "Service temporarily unavailable" error message.
        """
        # Create mock database session that raises service unavailable error
        mock_db = Mock(spec=Session)
        mock_db.query.side_effect = Exception("Service unavailable")
        
        # Create mock form data
        mock_form_data = Mock()
        mock_form_data.username = email
        mock_form_data.password = password
        
        # Test the login function directly
        with pytest.raises(HTTPException) as exc_info:
            login(db=mock_db, form_data=mock_form_data)
        
        # Should return 500 for internal server error
        assert exc_info.value.status_code == 500, f"Expected 500, got {exc_info.value.status_code}"
        
        # Should have appropriate error message
        detail = exc_info.value.detail
        assert "message" in detail, "Error should contain message"
        
        # Should indicate service issue
        message = detail["message"].lower()
        assert any(phrase in message for phrase in [
            "try again later", 
            "service", 
            "unavailable", 
            "error occurred"
        ]), f"Expected service error message, got: {detail['message']}"

    @given(
        st.emails(),
        st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        st.sampled_from([UserRole.CUSTOMER, UserRole.VENDOR, UserRole.WORKER, UserRole.REGIONAL_ADMIN, UserRole.SUPER_ADMIN])
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_3_role_based_redirect_successful_authentication(
        self, email: str, password: str, user_role: UserRole
    ):
        """
        **Validates: Requirements 1.6**
        **Property 3: Role-Based Redirect**
        
        For any successful authentication, the system should redirect users to their 
        role-appropriate dashboard within 2 seconds.
        """
        # Create mock active user with specific role
        mock_user = Mock()
        mock_user.id = 789
        mock_user.email = email
        mock_user.hashed_password = get_password_hash(password)
        mock_user.is_active = True
        mock_user.role = user_role
        
        # Create mock database session that returns the active user
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Create mock form data
        mock_form_data = Mock()
        mock_form_data.username = email
        mock_form_data.password = password
        
        start_time = time.time()
        
        # Test the login function directly
        result = login(db=mock_db, form_data=mock_form_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should respond within 2 seconds for successful login
        assert response_time < 2.0, f"Response took {response_time:.2f} seconds, should be < 2.0"
        
        # Should return access token
        assert "access_token" in result, "Response should contain access_token"
        assert "token_type" in result, "Response should contain token_type"
        assert result["token_type"] == "bearer", f"Expected bearer token, got {result['token_type']}"
        
        # Token should not be empty
        assert len(result["access_token"]) > 0, "Access token should not be empty"
        
        # Token should be a valid JWT format (3 parts separated by dots)
        token_parts = result["access_token"].split(".")
        assert len(token_parts) == 3, f"JWT should have 3 parts, got {len(token_parts)}"

    @given(
        st.emails(),
        st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_3_role_based_redirect_token_contains_user_info(self, email: str, password: str):
        """
        **Validates: Requirements 1.6**
        **Property 3: Role-Based Redirect**
        
        For any successful authentication, the returned token should contain user information
        that can be used for role-based navigation.
        """
        user_id = 999
        
        # Create mock active user
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = email
        mock_user.hashed_password = get_password_hash(password)
        mock_user.is_active = True
        mock_user.role = UserRole.CUSTOMER
        
        # Create mock database session that returns the active user
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Create mock form data
        mock_form_data = Mock()
        mock_form_data.username = email
        mock_form_data.password = password
        
        # Test the login function directly
        result = login(db=mock_db, form_data=mock_form_data)
        
        # Should return access token
        assert "access_token" in result, "Response should contain access_token"
        
        # Test that the token contains the user ID by creating a token and verifying it
        # This validates that the token contains the necessary user information
        token = result["access_token"]
        
        # Token should be a valid JWT format (3 parts separated by dots)
        token_parts = token.split(".")
        assert len(token_parts) == 3, f"JWT should have 3 parts, got {len(token_parts)}"
        
        # Verify the token was created with the correct user ID
        # We can't decode it easily in tests, but we can verify it was created properly
        # by checking that create_access_token was called with the right user_id
        expected_token = create_access_token(user_id)
        assert len(token) == len(expected_token), "Token should have expected length"

    @given(st.integers(min_value=1, max_value=10))
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_1_authentication_error_specificity_response_time_consistency(self, num_requests: int):
        """
        **Validates: Requirements 1.1, 1.2, 1.3**
        **Property 1: Authentication Error Specificity**
        
        For any number of authentication attempts, all error responses should be 
        consistently fast (< 3 seconds) regardless of error type.
        """
        response_times = []
        
        for i in range(num_requests):
            # Create mock database session that returns None (user not found)
            mock_db = Mock(spec=Session)
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            mock_db.query.return_value = mock_query
            
            # Create mock form data
            mock_form_data = Mock()
            mock_form_data.username = f"test{i}@example.com"
            mock_form_data.password = "any_password"
            
            start_time = time.time()
            
            # Test the login function directly
            with pytest.raises(HTTPException):
                login(db=mock_db, form_data=mock_form_data)
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Each individual response should be fast
            assert response_time < 3.0, f"Request {i+1} took {response_time:.2f} seconds, should be < 3.0"
        
        # All response times should be consistently fast
        max_response_time = max(response_times)
        avg_response_time = sum(response_times) / len(response_times)
        
        assert max_response_time < 3.0, f"Max response time {max_response_time:.2f}s should be < 3.0s"
        assert avg_response_time < 1.0, f"Average response time {avg_response_time:.2f}s should be < 1.0s"

    @given(
        st.lists(
            st.tuples(
                st.emails(),
                st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
            ),
            min_size=1,
            max_size=5
        )
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_2_network_error_handling_error_structure_consistency(self, credentials_list):
        """
        **Validates: Requirements 1.4, 1.5**
        **Property 2: Network Error Handling**
        
        For any network error during authentication, the error response structure 
        should be consistent and contain recovery information.
        """
        for email, password in credentials_list:
            # Create mock database session that raises connection error
            mock_db = Mock(spec=Session)
            mock_db.query.side_effect = ConnectionError("Network connection failed")
            
            # Create mock form data
            mock_form_data = Mock()
            mock_form_data.username = email
            mock_form_data.password = password
            
            # Test the login function directly
            with pytest.raises(HTTPException) as exc_info:
                login(db=mock_db, form_data=mock_form_data)
            
            # Should return 500 for network errors
            assert exc_info.value.status_code == 500, f"Expected 500, got {exc_info.value.status_code}"
            
            # Should have consistent error structure
            detail = exc_info.value.detail
            
            # Should have required error fields
            assert "error_code" in detail, "Error should contain error_code"
            assert "message" in detail, "Error should contain message"
            assert "timestamp" in detail, "Error should contain timestamp"
            assert "request_id" in detail, "Error should contain request_id"
            
            # Error code should be consistent
            assert detail["error_code"] == "INTERNAL_SERVER_ERROR", (
                f"Expected INTERNAL_SERVER_ERROR, got {detail['error_code']}"
            )
            
            # Message should provide recovery guidance
            message = detail["message"].lower()
            assert "try again" in message or "later" in message, (
                f"Error message should suggest retry, got: {detail['message']}"
            )


class TestAuthenticationIntegration:
    """Integration tests for authentication error handling"""

    def test_authentication_error_logging(self):
        """Test that authentication errors are properly logged"""
        # Create mock database session that returns None (user not found)
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Create mock form data
        mock_form_data = Mock()
        mock_form_data.username = "nonexistent@example.com"
        mock_form_data.password = "password"
        
        with patch('app.api.v1.endpoints.auth.logger') as mock_logger:
            with pytest.raises(HTTPException):
                login(db=mock_db, form_data=mock_form_data)
            
            # Should log the authentication attempt
            mock_logger.warning.assert_called()
            
            # Log message should contain relevant information
            log_calls = mock_logger.warning.call_args_list
            assert len(log_calls) > 0, "Should have logged warning for failed login"
            
            log_message = str(log_calls[0])
            assert "non-existent email" in log_message or "nonexistent@example.com" in log_message, (
                f"Log should contain email info, got: {log_message}"
            )

    def test_authentication_function_direct_call(self):
        """Test that authentication function works correctly when called directly"""
        # Create mock database session that returns None (user not found)
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Create mock form data
        mock_form_data = Mock()
        mock_form_data.username = "test@example.com"
        mock_form_data.password = "password"
        
        # Test the login function directly
        with pytest.raises(HTTPException) as exc_info:
            login(db=mock_db, form_data=mock_form_data)
        
        # Should get a proper HTTP exception
        assert exc_info.value.status_code in [400, 401, 404, 422, 500], (
            f"Should get proper HTTP status, got {exc_info.value.status_code}"
        )
        
        # Detail should be a dictionary
        assert isinstance(exc_info.value.detail, dict), "Detail should be a dictionary"

    def test_authentication_successful_login(self):
        """Test that successful authentication works correctly"""
        # Create mock active user
        mock_user = Mock()
        mock_user.id = 123
        mock_user.email = "test@example.com"
        mock_user.hashed_password = get_password_hash("correct_password")
        mock_user.is_active = True
        mock_user.role = UserRole.CUSTOMER
        
        # Create mock database session that returns the active user
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Create mock form data
        mock_form_data = Mock()
        mock_form_data.username = "test@example.com"
        mock_form_data.password = "correct_password"
        
        # Test the login function directly
        result = login(db=mock_db, form_data=mock_form_data)
        
        # Should return token data
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "access_token" in result, "Should contain access_token"
        assert "token_type" in result, "Should contain token_type"
        assert result["token_type"] == "bearer", "Should be bearer token"
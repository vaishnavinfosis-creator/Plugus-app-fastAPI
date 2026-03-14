"""
Property-Based Tests for Error Handling
**Feature: platform-robustness-improvements**
"""
import time
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings as hypothesis_settings
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.middleware.error_handler import ErrorHandler, BusinessLogicError, ResourceNotFoundError
from app.schemas.errors import (
    ErrorResponse, 
    ValidationErrorResponse, 
    ValidationErrorDetail,
    create_error_response,
    AuthErrorCodes,
    NetworkErrorCodes,
    ValidationErrorCodes,
    BusinessErrorCodes
)


class TestStructuredErrorResponsesProperty:
    """Property-based tests for structured error responses"""

    @given(
        st.integers(min_value=400, max_value=599),
        st.text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
            st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
            min_size=0,
            max_size=3
        )
    )
    @hypothesis_settings(max_examples=20, deadline=1000)
    def test_property_24_structured_error_responses_http_exceptions(
        self, status_code: int, error_message: str, details: Dict[str, str]
    ):
        """
        **Validates: Requirements 8.1, 8.3**
        **Property 24: Structured Error Responses**
        
        For any API request failure, the system should return structured error responses 
        with error codes, user-friendly messages, and appropriate logging.
        """
        # Create a mock request
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/test"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        
        # Create HTTP exception with structured detail
        error_code = ErrorHandler._get_error_code_from_status(status_code)
        structured_detail = {
            "error_code": error_code,
            "message": error_message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4())
        }
        
        exc = HTTPException(status_code=status_code, detail=structured_detail)
        
        # Handle the error
        with patch('app.middleware.error_handler.logger') as mock_logger:
            response = ErrorHandler._handle_http_exception(exc, "test-request-id")
        
        # Verify response is JSONResponse
        assert isinstance(response, JSONResponse), "Response should be JSONResponse"
        assert response.status_code == status_code, f"Status code should be {status_code}"
        
        # Parse response content
        response_data = json.loads(response.body.decode())
        
        # Verify structured error format
        assert "error_code" in response_data, "Response should contain error_code"
        assert "message" in response_data, "Response should contain message"
        assert "timestamp" in response_data, "Response should contain timestamp"
        assert "request_id" in response_data, "Response should contain request_id"
        
        # Verify error code is not empty
        assert len(response_data["error_code"]) > 0, "Error code should not be empty"
        
        # Verify message is user-friendly (not empty)
        assert len(response_data["message"]) > 0, "Message should not be empty"
        
        # Verify timestamp is valid ISO format
        try:
            datetime.fromisoformat(response_data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Timestamp should be valid ISO format: {response_data['timestamp']}")
        
        # Verify request_id exists and is not empty
        assert "request_id" in response_data, "Response should contain request_id"
        assert len(response_data["request_id"]) > 0, "Request ID should not be empty"

    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
                st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
            ),
            min_size=1,
            max_size=5
        )
    )
    @hypothesis_settings(max_examples=20, deadline=1000)
    def test_property_24_structured_error_responses_validation_errors(self, field_errors):
        """
        **Validates: Requirements 8.1, 8.3**
        **Property 24: Structured Error Responses**
        
        For any validation error, the system should return structured error responses 
        with field-level details and error codes.
        """
        # Create validation error details
        validation_errors = [
            ValidationErrorDetail(field=field, message=message, rejected_value=None)
            for field, message in field_errors
        ]
        
        # Create mock validation error
        mock_error = Mock()
        mock_error.errors.return_value = [
            {"loc": (field,), "msg": message, "input": None}
            for field, message in field_errors
        ]
        
        # Handle the validation error
        response = ErrorHandler._handle_validation_error(mock_error, "test-request-id")
        
        # Verify response structure
        assert isinstance(response, JSONResponse), "Response should be JSONResponse"
        assert response.status_code == 422, "Validation errors should return 422"
        
        # Parse response content
        response_data = json.loads(response.body.decode())
        
        # Verify structured error format
        assert "error_code" in response_data, "Response should contain error_code"
        assert "message" in response_data, "Response should contain message"
        assert "validation_errors" in response_data, "Response should contain validation_errors"
        assert "timestamp" in response_data, "Response should contain timestamp"
        assert "request_id" in response_data, "Response should contain request_id"
        
        # Verify validation errors list
        assert len(response_data["validation_errors"]) == len(field_errors), (
            f"Should have {len(field_errors)} validation errors"
        )
        
        # Verify each validation error has required fields
        for val_error in response_data["validation_errors"]:
            assert "field" in val_error, "Validation error should contain field"
            assert "message" in val_error, "Validation error should contain message"
            assert len(val_error["field"]) > 0, "Field name should not be empty"
            assert len(val_error["message"]) > 0, "Error message should not be empty"

    @given(
        st.sampled_from([
            "unique constraint",
            "foreign key constraint",
            "not null constraint",
            "check constraint"
        ]),
        st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @hypothesis_settings(max_examples=20, deadline=1000)
    def test_property_24_structured_error_responses_database_errors(
        self, constraint_type: str, error_detail: str
    ):
        """
        **Validates: Requirements 8.1, 8.3**
        **Property 24: Structured Error Responses**
        
        For any database error, the system should return structured error responses 
        with appropriate error codes and user-friendly messages.
        """
        # Create mock integrity error
        mock_error = IntegrityError(
            statement="INSERT INTO test",
            params={},
            orig=Exception(f"{constraint_type} failed: {error_detail}")
        )
        
        # Handle the database error
        with patch('app.middleware.error_handler.logger') as mock_logger:
            response = ErrorHandler._handle_database_error(mock_error, "test-request-id")
        
        # Verify response structure
        assert isinstance(response, JSONResponse), "Response should be JSONResponse"
        assert response.status_code == 409, "Integrity errors should return 409"
        
        # Parse response content
        response_data = json.loads(response.body.decode())
        
        # Verify structured error format
        assert "error_code" in response_data, "Response should contain error_code"
        assert "message" in response_data, "Response should contain message"
        assert "timestamp" in response_data, "Response should contain timestamp"
        assert "request_id" in response_data, "Response should contain request_id"
        
        # Verify error code is appropriate for database errors
        assert response_data["error_code"] == BusinessErrorCodes.DUPLICATE_RESOURCE, (
            f"Expected {BusinessErrorCodes.DUPLICATE_RESOURCE}, got {response_data['error_code']}"
        )
        
        # Verify message is user-friendly (not technical database error)
        message = response_data["message"].lower()
        assert not any(tech_term in message for tech_term in ["sql", "query", "statement"]), (
            f"Message should be user-friendly, got: {response_data['message']}"
        )
        
        # Verify logging occurred
        mock_logger.error.assert_not_called()  # IntegrityError doesn't log at error level

    @given(
        st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @hypothesis_settings(max_examples=20, deadline=1000)
    def test_property_24_structured_error_responses_generic_errors(self, error_message: str):
        """
        **Validates: Requirements 8.1, 8.3**
        **Property 24: Structured Error Responses**
        
        For any unexpected error, the system should return structured error responses 
        with generic user-friendly messages and detailed logging.
        """
        # Create generic exception
        exc = Exception(error_message)
        
        # Handle the generic error
        with patch('app.middleware.error_handler.logger') as mock_logger:
            response = ErrorHandler._handle_generic_error(exc, "test-request-id")
        
        # Verify response structure
        assert isinstance(response, JSONResponse), "Response should be JSONResponse"
        assert response.status_code == 500, "Generic errors should return 500"
        
        # Parse response content
        response_data = json.loads(response.body.decode())
        
        # Verify structured error format
        assert "error_code" in response_data, "Response should contain error_code"
        assert "message" in response_data, "Response should contain message"
        assert "details" in response_data, "Response should contain details"
        assert "timestamp" in response_data, "Response should contain timestamp"
        assert "request_id" in response_data, "Response should contain request_id"
        
        # Verify error code
        assert response_data["error_code"] == "INTERNAL_SERVER_ERROR", (
            f"Expected INTERNAL_SERVER_ERROR, got {response_data['error_code']}"
        )
        
        # Verify message is generic and user-friendly
        message = response_data["message"].lower()
        assert "unexpected error" in message or "try again later" in message, (
            f"Message should be generic, got: {response_data['message']}"
        )
        
        # Verify details contain support information
        assert "support_message" in response_data["details"], (
            "Details should contain support message"
        )
        assert "request ID" in response_data["details"]["support_message"], (
            "Support message should reference request ID"
        )
        
        # Verify logging occurred
        mock_logger.error.assert_called()

    @given(
        st.integers(min_value=1, max_value=10)
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_property_24_structured_error_responses_consistency(self, num_errors: int):
        """
        **Validates: Requirements 8.1, 8.3**
        **Property 24: Structured Error Responses**
        
        For any sequence of errors, all error responses should have consistent structure 
        and format regardless of error type.
        """
        error_responses = []
        
        for i in range(num_errors):
            # Create different types of errors
            if i % 3 == 0:
                # HTTP exception
                exc = HTTPException(
                    status_code=404,
                    detail={"error_code": "NOT_FOUND", "message": f"Resource {i} not found"}
                )
                response = ErrorHandler._handle_http_exception(exc, f"request-{i}")
            elif i % 3 == 1:
                # Validation error
                mock_error = Mock()
                mock_error.errors.return_value = [
                    {"loc": (f"field{i}",), "msg": f"Invalid value {i}", "input": None}
                ]
                response = ErrorHandler._handle_validation_error(mock_error, f"request-{i}")
            else:
                # Generic error
                exc = Exception(f"Error {i}")
                response = ErrorHandler._handle_generic_error(exc, f"request-{i}")
            
            response_data = json.loads(response.body.decode())
            error_responses.append(response_data)
        
        # Verify all responses have consistent structure
        required_fields = ["error_code", "message", "timestamp", "request_id"]
        
        for response_data in error_responses:
            for field in required_fields:
                assert field in response_data, f"All responses should contain {field}"
                assert response_data[field] is not None, f"{field} should not be None"
                
                if field == "error_code":
                    assert len(response_data[field]) > 0, "Error code should not be empty"
                elif field == "message":
                    assert len(response_data[field]) > 0, "Message should not be empty"
                elif field == "timestamp":
                    # Verify timestamp format
                    try:
                        datetime.fromisoformat(response_data[field].replace('Z', '+00:00'))
                    except ValueError:
                        pytest.fail(f"Invalid timestamp format: {response_data[field]}")
                elif field == "request_id":
                    # Verify request_id is not empty
                    assert len(response_data[field]) > 0, "Request ID should not be empty"


class TestErrorResponseCreationHelpers:
    """Test error response creation helper functions"""

    @given(
        st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),
        st.text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @hypothesis_settings(max_examples=20, deadline=1000)
    def test_create_error_response_helper(self, error_code: str, message: str):
        """Test create_error_response helper function"""
        error_response = create_error_response(
            error_code=error_code,
            message=message
        )
        
        assert isinstance(error_response, ErrorResponse), "Should return ErrorResponse"
        assert error_response.error_code == error_code, "Error code should match"
        assert error_response.message == message, "Message should match"
        assert error_response.timestamp is not None, "Timestamp should be set"
        assert error_response.request_id is not None, "Request ID should be set"
        
        # Verify request_id is valid UUID
        try:
            uuid.UUID(error_response.request_id)
        except ValueError:
            pytest.fail(f"Request ID should be valid UUID: {error_response.request_id}")

    @given(
        st.sampled_from([
            AuthErrorCodes.USER_NOT_FOUND,
            AuthErrorCodes.INVALID_PASSWORD,
            AuthErrorCodes.TOKEN_EXPIRED,
            NetworkErrorCodes.CONNECTION_TIMEOUT,
            NetworkErrorCodes.SERVICE_UNAVAILABLE,
            ValidationErrorCodes.INVALID_INPUT,
            BusinessErrorCodes.RESOURCE_NOT_FOUND
        ])
    )
    @hypothesis_settings(max_examples=15, deadline=1000)
    def test_error_codes_are_consistent(self, error_code: str):
        """Test that error codes are consistent and well-defined"""
        # Error codes should be uppercase with underscores
        assert error_code.isupper(), f"Error code should be uppercase: {error_code}"
        assert "_" in error_code or error_code.isalpha(), (
            f"Error code should use underscores or be single word: {error_code}"
        )
        
        # Error codes should not be empty
        assert len(error_code) > 0, "Error code should not be empty"
        
        # Error codes should be descriptive (at least 3 characters)
        assert len(error_code) >= 3, f"Error code should be descriptive: {error_code}"

"""
Error Response Schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class ErrorResponse(BaseModel):
    """Structured error response model"""
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="User-friendly error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error occurrence time")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Request tracking ID")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def model_dump(self, **kwargs):
        """Override to ensure datetime is serialized as ISO string"""
        data = super().model_dump(**kwargs)
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data


class ValidationErrorDetail(BaseModel):
    """Validation error detail for specific fields"""
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    rejected_value: Optional[Any] = Field(None, description="The value that was rejected")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field details"""
    error_code: str = Field(default="VALIDATION_ERROR", description="Validation error code")
    validation_errors: list[ValidationErrorDetail] = Field(..., description="List of field validation errors")


# Authentication Error Codes
class AuthErrorCodes:
    USER_NOT_FOUND = "USER_NOT_FOUND"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"


# Network Error Codes
class NetworkErrorCodes:
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


# Validation Error Codes
class ValidationErrorCodes:
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    VALUE_TOO_LONG = "VALUE_TOO_LONG"
    VALUE_TOO_SHORT = "VALUE_TOO_SHORT"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"


# Business Logic Error Codes
class BusinessErrorCodes:
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    BOOKING_CONFLICT = "BOOKING_CONFLICT"
    WORKER_UNAVAILABLE = "WORKER_UNAVAILABLE"


def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Helper function to create standardized error responses"""
    return ErrorResponse(
        error_code=error_code,
        message=message,
        details=details or {},
        request_id=request_id or str(uuid.uuid4())
    )


def create_validation_error_response(
    validation_errors: list[ValidationErrorDetail],
    message: str = "Validation failed",
    request_id: Optional[str] = None
) -> ValidationErrorResponse:
    """Helper function to create validation error responses"""
    return ValidationErrorResponse(
        message=message,
        validation_errors=validation_errors,
        request_id=request_id or str(uuid.uuid4())
    )
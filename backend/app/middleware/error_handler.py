"""
Global Error Handler Middleware
"""
import logging
import traceback
import uuid
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

from app.schemas.errors import (
    ErrorResponse, 
    ValidationErrorResponse, 
    ValidationErrorDetail,
    create_error_response,
    create_validation_error_response,
    AuthErrorCodes,
    NetworkErrorCodes,
    ValidationErrorCodes,
    BusinessErrorCodes
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Global error handler for the application"""
    
    @staticmethod
    async def handle_error(request: Request, exc: Exception) -> JSONResponse:
        """Handle different types of exceptions"""
        request_id = str(uuid.uuid4())
        
        # Log error with context
        logger.error(
            f"Error handling request {request.method} {request.url.path}: {str(exc)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc()
            }
        )
        
        # Handle specific exception types
        if isinstance(exc, HTTPException):
            return ErrorHandler._handle_http_exception(exc, request_id)
        elif isinstance(exc, RequestValidationError):
            return ErrorHandler._handle_validation_error(exc, request_id)
        elif isinstance(exc, ValidationError):
            return ErrorHandler._handle_pydantic_validation_error(exc, request_id)
        elif isinstance(exc, SQLAlchemyError):
            return ErrorHandler._handle_database_error(exc, request_id)
        else:
            return ErrorHandler._handle_generic_error(exc, request_id)
    
    @staticmethod
    def _handle_http_exception(exc: HTTPException, request_id: str) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""
        # Check if detail is already a structured error
        if isinstance(exc.detail, dict) and "error_code" in exc.detail:
            error_response = ErrorResponse(**exc.detail)
            error_response.request_id = request_id
        else:
            # Convert string detail to structured error
            error_code = ErrorHandler._get_error_code_from_status(exc.status_code)
            error_response = create_error_response(
                error_code=error_code,
                message=str(exc.detail),
                request_id=request_id
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode='json')
        )
    
    @staticmethod
    def _handle_validation_error(exc: RequestValidationError, request_id: str) -> JSONResponse:
        """Handle FastAPI request validation errors"""
        validation_errors = []
        
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append(
                ValidationErrorDetail(
                    field=field_path,
                    message=error["msg"],
                    rejected_value=error.get("input")
                )
            )
        
        error_response = create_validation_error_response(
            validation_errors=validation_errors,
            message="Request validation failed",
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(mode='json')
        )
    
    @staticmethod
    def _handle_pydantic_validation_error(exc: ValidationError, request_id: str) -> JSONResponse:
        """Handle Pydantic model validation errors"""
        validation_errors = []
        
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append(
                ValidationErrorDetail(
                    field=field_path,
                    message=error["msg"],
                    rejected_value=error.get("input")
                )
            )
        
        error_response = create_validation_error_response(
            validation_errors=validation_errors,
            message="Data validation failed",
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(mode='json')
        )
    
    @staticmethod
    def _handle_database_error(exc: SQLAlchemyError, request_id: str) -> JSONResponse:
        """Handle database-related errors"""
        if isinstance(exc, IntegrityError):
            # Handle constraint violations
            error_message = "Data integrity constraint violated"
            error_code = BusinessErrorCodes.DUPLICATE_RESOURCE
            
            # Try to extract meaningful error from the exception
            if "unique constraint" in str(exc).lower():
                error_message = "A record with this information already exists"
            elif "foreign key constraint" in str(exc).lower():
                error_message = "Referenced record does not exist"
            elif "not null constraint" in str(exc).lower():
                error_message = "Required field is missing"
            
            error_response = create_error_response(
                error_code=error_code,
                message=error_message,
                details={"constraint_type": "integrity"},
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=error_response.model_dump(mode='json')
            )
        else:
            # Generic database error
            logger.error(f"Database error: {str(exc)}")
            error_response = create_error_response(
                error_code="DATABASE_ERROR",
                message="A database error occurred. Please try again later.",
                details={"error_type": type(exc).__name__},
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(mode='json')
            )
    
    @staticmethod
    def _handle_generic_error(exc: Exception, request_id: str) -> JSONResponse:
        """Handle unexpected errors"""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        
        error_response = create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            details={
                "error_type": type(exc).__name__,
                "support_message": f"If this problem persists, please contact support with request ID: {request_id}"
            },
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(mode='json')
        )
    
    @staticmethod
    def _get_error_code_from_status(status_code: int) -> str:
        """Map HTTP status codes to error codes"""
        status_map = {
            400: ValidationErrorCodes.INVALID_INPUT,
            401: AuthErrorCodes.TOKEN_INVALID,
            403: AuthErrorCodes.INSUFFICIENT_PERMISSIONS,
            404: BusinessErrorCodes.RESOURCE_NOT_FOUND,
            409: BusinessErrorCodes.DUPLICATE_RESOURCE,
            422: ValidationErrorCodes.INVALID_INPUT,
            429: NetworkErrorCodes.RATE_LIMIT_EXCEEDED,
            500: "INTERNAL_SERVER_ERROR",
            502: NetworkErrorCodes.SERVICE_UNAVAILABLE,
            503: NetworkErrorCodes.SERVICE_UNAVAILABLE,
            504: NetworkErrorCodes.CONNECTION_TIMEOUT
        }
        
        return status_map.get(status_code, "UNKNOWN_ERROR")


async def error_handler_middleware(request: Request, call_next):
    """Error handling middleware"""
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return await ErrorHandler.handle_error(request, exc)


# Custom exception classes for business logic
class BusinessLogicError(Exception):
    """Base class for business logic errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or BusinessErrorCodes.OPERATION_NOT_ALLOWED
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundError(BusinessLogicError):
    """Raised when a requested resource is not found"""
    def __init__(self, resource_type: str, resource_id: Union[str, int] = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(
            message=message,
            error_code=BusinessErrorCodes.RESOURCE_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class DuplicateResourceError(BusinessLogicError):
    """Raised when trying to create a duplicate resource"""
    def __init__(self, resource_type: str, field: str = None, value: str = None):
        message = f"{resource_type} already exists"
        if field and value:
            message += f" with {field}: {value}"
        
        super().__init__(
            message=message,
            error_code=BusinessErrorCodes.DUPLICATE_RESOURCE,
            details={"resource_type": resource_type, "field": field, "value": value}
        )


class InsufficientPermissionsError(BusinessLogicError):
    """Raised when user lacks required permissions"""
    def __init__(self, required_permission: str = None, user_role: str = None):
        message = "Insufficient permissions for this operation"
        if required_permission:
            message += f". Required: {required_permission}"
        
        super().__init__(
            message=message,
            error_code=AuthErrorCodes.INSUFFICIENT_PERMISSIONS,
            details={"required_permission": required_permission, "user_role": user_role}
        )


class ValidationFailedError(BusinessLogicError):
    """Raised when business validation fails"""
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(
            message=message,
            error_code=ValidationErrorCodes.INVALID_INPUT,
            details={"field": field, "value": value}
        )
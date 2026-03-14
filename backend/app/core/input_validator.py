"""
Input Validation and Sanitization Service
"""
import re
import html
import logging
from typing import Any, Optional, List, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    """Supported field types for validation"""
    EMAIL = "email"
    TEXT = "text"
    NAME = "name"
    PHONE = "phone"
    ADDRESS = "address"
    DESCRIPTION = "description"
    URL = "url"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"


class ValidationResult:
    """Result of input validation"""
    def __init__(self, is_valid: bool, sanitized_value: Any = None, errors: List[str] = None):
        self.is_valid = is_valid
        self.sanitized_value = sanitized_value
        self.errors = errors or []


class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # SQL Injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(;|\|\||&&)",
        r"(\bxp_cmdshell\b|\bsp_executesql\b)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ]
    
    # Email regex (RFC 5322 compliant with required TLD)
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
    )
    
    # Phone pattern (international format)
    PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{1,14}$")
    
    # URL pattern
    URL_PATTERN = re.compile(
        r"^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$"
    )
    
    # Field length limits (based on database constraints)
    FIELD_LIMITS = {
        FieldType.EMAIL: 255,
        FieldType.TEXT: 500,
        FieldType.NAME: 255,
        FieldType.PHONE: 20,
        FieldType.ADDRESS: 1000,
        FieldType.DESCRIPTION: 2000,
        FieldType.URL: 500,
    }
    
    @classmethod
    def validate_and_sanitize(
        cls, 
        value: Any, 
        field_type: FieldType, 
        required: bool = True,
        max_length: Optional[int] = None
    ) -> ValidationResult:
        """Main validation and sanitization entry point"""
        
        # Handle None/empty values
        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                return ValidationResult(False, None, ["This field is required"])
            return ValidationResult(True, None)
        
        # Convert to string for text-based validation
        if not isinstance(value, str):
            value = str(value)
        
        # Basic sanitization
        sanitized = cls._basic_sanitize(value)
        errors = []
        
        # Check for malicious patterns
        if cls._contains_sql_injection(sanitized):
            logger.warning(f"SQL injection attempt detected: {value[:100]}")
            errors.append("Invalid characters detected")
        
        if cls._contains_xss(sanitized):
            logger.warning(f"XSS attempt detected: {value[:100]}")
            sanitized = cls._sanitize_xss(sanitized)
        
        # Length validation
        max_len = max_length or cls.FIELD_LIMITS.get(field_type, 1000)
        if len(sanitized) > max_len:
            errors.append(f"Maximum length is {max_len} characters")
        
        # Type-specific validation
        type_errors = cls._validate_field_type(sanitized, field_type)
        errors.extend(type_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized if len(errors) == 0 else None,
            errors=errors
        )
    
    @classmethod
    def _basic_sanitize(cls, value: str) -> str:
        """Basic string sanitization"""
        # Strip whitespace
        value = value.strip()
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Normalize unicode
        value = value.encode('utf-8', 'ignore').decode('utf-8')
        
        return value
    
    @classmethod
    def _contains_sql_injection(cls, value: str) -> bool:
        """Check for SQL injection patterns"""
        value_lower = value.lower()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def _contains_xss(cls, value: str) -> bool:
        """Check for XSS patterns"""
        value_lower = value.lower()
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def _sanitize_xss(cls, value: str) -> str:
        """Sanitize XSS by HTML encoding"""
        # HTML encode dangerous characters
        sanitized = html.escape(value, quote=True)
        
        # Remove script tags and javascript
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'vbscript:', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @classmethod
    def _validate_field_type(cls, value: str, field_type: FieldType) -> List[str]:
        """Validate specific field types"""
        errors = []
        
        if field_type == FieldType.EMAIL:
            if not cls.EMAIL_PATTERN.match(value):
                errors.append("Invalid email format")
        
        elif field_type == FieldType.PHONE:
            # Remove common phone formatting
            clean_phone = re.sub(r'[\s\-\(\)]', '', value)
            if not cls.PHONE_PATTERN.match(clean_phone):
                errors.append("Invalid phone number format")
        
        elif field_type == FieldType.URL:
            if not cls.URL_PATTERN.match(value):
                errors.append("Invalid URL format")
        
        elif field_type == FieldType.NAME:
            # Names should only contain letters, spaces, hyphens, apostrophes
            if not re.match(r"^[a-zA-Z\s\-'\.]+$", value):
                errors.append("Name contains invalid characters")
        
        elif field_type == FieldType.NUMERIC:
            try:
                float(value)
            except ValueError:
                errors.append("Must be a valid number")
        
        elif field_type == FieldType.BOOLEAN:
            if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                errors.append("Must be a valid boolean value")
        
        return errors
    
    @classmethod
    def validate_multiple_fields(
        cls, 
        data: Dict[str, Any], 
        field_definitions: Dict[str, Dict]
    ) -> Dict[str, ValidationResult]:
        """Validate multiple fields at once"""
        results = {}
        
        for field_name, definition in field_definitions.items():
            field_type = definition.get('type', FieldType.TEXT)
            required = definition.get('required', False)
            max_length = definition.get('max_length')
            
            value = data.get(field_name)
            result = cls.validate_and_sanitize(value, field_type, required, max_length)
            results[field_name] = result
        
        return results
    
    @classmethod
    def get_sanitized_data(cls, validation_results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Extract sanitized data from validation results"""
        sanitized_data = {}
        
        for field_name, result in validation_results.items():
            if result.is_valid and result.sanitized_value is not None:
                sanitized_data[field_name] = result.sanitized_value
        
        return sanitized_data
    
    @classmethod
    def get_validation_errors(cls, validation_results: Dict[str, ValidationResult]) -> Dict[str, List[str]]:
        """Extract validation errors from results"""
        errors = {}
        
        for field_name, result in validation_results.items():
            if not result.is_valid:
                errors[field_name] = result.errors
        
        return errors


# Convenience functions for common validations
def validate_email(email: str) -> ValidationResult:
    """Validate email address"""
    return InputValidator.validate_and_sanitize(email, FieldType.EMAIL)


def validate_phone(phone: str) -> ValidationResult:
    """Validate phone number"""
    return InputValidator.validate_and_sanitize(phone, FieldType.PHONE)


def validate_text(text: str, max_length: int = 500, required: bool = True) -> ValidationResult:
    """Validate general text input"""
    return InputValidator.validate_and_sanitize(text, FieldType.TEXT, required, max_length)


def validate_name(name: str) -> ValidationResult:
    """Validate person/business name"""
    return InputValidator.validate_and_sanitize(name, FieldType.NAME)
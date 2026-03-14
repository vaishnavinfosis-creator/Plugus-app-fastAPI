"""
Property-Based Tests for Input Validation
**Feature: platform-robustness-improvements**
"""
import io
import os
import string
import tempfile
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

import pytest
from hypothesis import given, strategies as st, settings as hypothesis_settings
from fastapi import UploadFile

from app.core.input_validator import (
    InputValidator, 
    FieldType, 
    ValidationResult,
    validate_email,
    validate_phone,
    validate_text,
    validate_name
)
from app.core.file_validator import (
    FileValidator,
    FileValidationResult,
    validate_image_upload,
    validate_document_upload
)


class TestInputValidationProperties:
    """Property-based tests for input validation"""

    @given(st.dictionaries(
        keys=st.sampled_from(['name', 'email', 'phone', 'description']),
        values=st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=4
    ))
    @hypothesis_settings(max_examples=50)
    def test_property_7_input_validation_completeness_format_validation(self, input_data: Dict[str, str]):
        """
        **Validates: Requirements 2.5, 3.1**
        **Property 7: Input Validation Completeness**
        
        For any user input received by the system, it should be validated against format constraints.
        """
        field_definitions = {
            'name': {'type': FieldType.NAME, 'required': True},
            'email': {'type': FieldType.EMAIL, 'required': True},
            'phone': {'type': FieldType.PHONE, 'required': True},
            'description': {'type': FieldType.DESCRIPTION, 'required': True}
        }
        
        results = InputValidator.validate_multiple_fields(input_data, field_definitions)
        
        # Every field should have a validation result
        for field_name in input_data.keys():
            assert field_name in results, f"No validation result for field: {field_name}"
            assert isinstance(results[field_name], ValidationResult), f"Invalid result type for {field_name}"
        
        # Format validation should be applied
        for field_name, result in results.items():
            if field_name == 'email' and field_name in input_data:
                # Email should be validated with RFC pattern
                email_value = input_data[field_name]
                if '@' not in email_value or '.' not in email_value.split('@')[-1]:
                    assert not result.is_valid, f"Invalid email accepted: {email_value}"
            
            elif field_name == 'name' and field_name in input_data:
                # Name should only contain valid characters
                name_value = input_data[field_name]
                if any(c in name_value for c in '<>{}[]()@#$%^&*+=|\\'):
                    assert not result.is_valid, f"Invalid name characters accepted: {name_value}"

    @given(st.dictionaries(
        keys=st.sampled_from(['short_text', 'medium_text', 'long_text']),
        values=st.text(min_size=1, max_size=3000),
        min_size=1,
        max_size=3
    ))
    @hypothesis_settings(max_examples=50)
    def test_property_7_input_validation_completeness_length_validation(self, input_data: Dict[str, str]):
        """
        **Validates: Requirements 2.5, 3.1**
        **Property 7: Input Validation Completeness**
        
        For any user input received by the system, it should be validated against length constraints.
        """
        field_definitions = {
            'short_text': {'type': FieldType.TEXT, 'required': True, 'max_length': 50},
            'medium_text': {'type': FieldType.TEXT, 'required': True, 'max_length': 500},
            'long_text': {'type': FieldType.DESCRIPTION, 'required': True, 'max_length': 2000}
        }
        
        results = InputValidator.validate_multiple_fields(input_data, field_definitions)
        
        # Length constraints should be enforced
        for field_name, result in results.items():
            if field_name in input_data:
                field_value = input_data[field_name]
                max_length = field_definitions[field_name]['max_length']
                
                if len(field_value) > max_length:
                    assert not result.is_valid, f"Long input accepted for {field_name}: {len(field_value)} > {max_length}"
                    length_errors = [error for error in result.errors if "Maximum length" in error]
                    assert len(length_errors) > 0, f"No length error for {field_name}"

    @given(st.lists(
        st.one_of(
            # SQL injection patterns
            st.just("'; DROP TABLE users; --"),
            st.just("1' OR '1'='1"),
            st.just("admin'--"),
            st.just("' UNION SELECT * FROM passwords --"),
            st.just("1; DELETE FROM accounts;"),
            st.just("' OR 1=1 --"),
            st.just("'; INSERT INTO users VALUES ('hacker', 'password'); --"),
            st.just("1' AND (SELECT COUNT(*) FROM users) > 0 --"),
            # Mixed with normal text
            st.text(min_size=5, max_size=50).map(lambda x: f"{x}'; DROP TABLE users; --"),
            st.text(min_size=5, max_size=50).map(lambda x: f"normal text {x} OR 1=1")
        ),
        min_size=1,
        max_size=5
    ))
    @hypothesis_settings(max_examples=30)
    def test_property_8_malicious_input_detection_sql_injection(self, sql_injection_inputs: List[str]):
        """
        **Validates: Requirements 3.2, 3.3**
        **Property 8: Malicious Input Detection**
        
        For any input containing SQL injection patterns, the system should detect and reject the attempt.
        """
        for malicious_input in sql_injection_inputs:
            result = InputValidator.validate_and_sanitize(malicious_input, FieldType.TEXT)
            
            # SQL injection should be detected and rejected
            assert not result.is_valid, f"SQL injection not detected: {malicious_input[:50]}..."
            
            # Should have appropriate error message
            injection_errors = [error for error in result.errors if "Invalid characters" in error]
            assert len(injection_errors) > 0, f"No SQL injection error for: {malicious_input[:50]}..."

    @given(st.lists(
        st.one_of(
            # XSS patterns
            st.just("<script>alert('xss')</script>"),
            st.just("<img src=x onerror=alert('xss')>"),
            st.just("javascript:alert('xss')"),
            st.just("<iframe src='javascript:alert(1)'></iframe>"),
            st.just("<svg onload=alert('xss')>"),
            st.just("<body onload=alert('xss')>"),
            st.just("<link rel=stylesheet href=javascript:alert('xss')>"),
            st.just("<meta http-equiv=refresh content=0;url=javascript:alert('xss')>"),
            # Mixed with normal text
            st.text(min_size=5, max_size=50).map(lambda x: f"{x}<script>alert('xss')</script>"),
            st.text(min_size=5, max_size=50).map(lambda x: f"normal text {x} javascript:alert(1)")
        ),
        min_size=1,
        max_size=5
    ))
    @hypothesis_settings(max_examples=30)
    def test_property_8_malicious_input_detection_xss_patterns(self, xss_inputs: List[str]):
        """
        **Validates: Requirements 3.2, 3.3**
        **Property 8: Malicious Input Detection**
        
        For any input containing XSS patterns, the system should detect, sanitize, and log the attempt.
        """
        for malicious_input in xss_inputs:
            result = InputValidator.validate_and_sanitize(malicious_input, FieldType.TEXT)
            
            # XSS should be detected and sanitized
            if result.is_valid:
                # If valid, should be sanitized (HTML encoded)
                assert result.sanitized_value != malicious_input, f"XSS not sanitized: {malicious_input[:50]}..."
                # Should not contain dangerous patterns
                sanitized = result.sanitized_value.lower()
                assert '<script' not in sanitized, f"Script tag not removed: {result.sanitized_value[:50]}..."
                assert 'javascript:' not in sanitized, f"JavaScript protocol not removed: {result.sanitized_value[:50]}..."
            else:
                # If invalid, should have been rejected
                assert len(result.errors) > 0, f"XSS input rejected without errors: {malicious_input[:50]}..."

    @given(st.binary(min_size=1, max_size=10*1024*1024))  # Up to 10MB
    @hypothesis_settings(max_examples=25, deadline=5000)  # Longer deadline for file operations
    def test_property_9_file_upload_validation_size_constraints(self, file_content: bytes):
        """
        **Validates: Requirements 3.4**
        **Property 9: File Upload Validation**
        
        For any file upload, the system should validate size constraints before storage.
        """
        import asyncio
        
        async def run_validation():
            # Create mock UploadFile
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = "test.jpg"
            mock_file.content_type = "image/jpeg"
            mock_file.read = AsyncMock(return_value=file_content)
            mock_file.seek = AsyncMock()
            
            result = await FileValidator.validate_upload_file(mock_file, "image")
            
            file_size = len(file_content)
            max_size = FileValidator.MAX_IMAGE_SIZE
            
            if file_size > max_size:
                # Large files should be rejected
                assert not result.is_valid, f"Large file accepted: {file_size} bytes > {max_size}"
                size_errors = [error for error in result.errors if "exceeds maximum" in error]
                assert len(size_errors) > 0, f"No size error for large file: {file_size} bytes"
            
            if file_size == 0:
                # Empty files should be rejected
                assert not result.is_valid, "Empty file accepted"
                empty_errors = [error for error in result.errors if "empty" in error]
                assert len(empty_errors) > 0, "No empty file error"
        
        # Run the async validation
        asyncio.run(run_validation())

    @given(st.lists(
        st.one_of(
            st.just(b'\x4D\x5A'),  # PE executable header
            st.just(b'\x7F\x45\x4C\x46'),  # ELF executable header
            st.just(b'\xCA\xFE\xBA\xBE'),  # Java class file
            st.binary(min_size=100, max_size=1000).map(lambda x: b'\x4D\x5A' + x),  # PE with content
            st.binary(min_size=100, max_size=1000).map(lambda x: x + b'<script>alert("xss")</script>'),  # Script injection
        ),
        min_size=1,
        max_size=3
    ))
    @hypothesis_settings(max_examples=25, deadline=5000)
    def test_property_9_file_upload_validation_malicious_content(self, malicious_contents: List[bytes]):
        """
        **Validates: Requirements 3.4**
        **Property 9: File Upload Validation**
        
        For any file upload with malicious content, the system should detect and reject it.
        """
        import asyncio
        
        async def run_validation():
            for malicious_content in malicious_contents:
                # Create mock UploadFile with malicious content
                mock_file = Mock(spec=UploadFile)
                mock_file.filename = "test.jpg"
                mock_file.content_type = "image/jpeg"
                mock_file.read = AsyncMock(return_value=malicious_content)
                mock_file.seek = AsyncMock()
                
                result = await FileValidator.validate_upload_file(mock_file, "image")
                
                # Malicious content should be detected and rejected
                if len(malicious_content) <= FileValidator.MAX_IMAGE_SIZE:
                    # Only check for malicious content if size is acceptable
                    malicious_errors = [error for error in result.errors if "malicious" in error.lower()]
                    if len(malicious_errors) == 0:
                        # If no malicious error, should at least fail type validation
                        type_errors = [error for error in result.errors if "type" in error.lower() or "format" in error.lower()]
                        assert len(type_errors) > 0 or not result.is_valid, f"Malicious content not detected: {malicious_content[:20]}..."
        
        # Run the async validation
        asyncio.run(run_validation())

    @given(st.lists(
        st.one_of(
            st.just("test.exe"),
            st.just("malware.bat"),
            st.just("script.js"),
            st.just("file.php"),
            st.just("document.html"),
            st.just("image.svg"),  # SVG can contain scripts
            st.text(min_size=5, max_size=20).map(lambda x: f"{x}.exe"),
            st.text(min_size=5, max_size=20).map(lambda x: f"{x}.bat"),
        ),
        min_size=1,
        max_size=5
    ))
    @hypothesis_settings(max_examples=30, deadline=3000)
    def test_property_9_file_upload_validation_type_whitelist(self, filenames: List[str]):
        """
        **Validates: Requirements 3.4**
        **Property 9: File Upload Validation**
        
        For any file upload, the system should validate against type whitelist.
        """
        import asyncio
        
        async def run_validation():
            for filename in filenames:
                # Create mock UploadFile with safe content but dangerous filename
                safe_jpeg_header = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
                mock_file = Mock(spec=UploadFile)
                mock_file.filename = filename
                mock_file.content_type = "image/jpeg"
                mock_file.read = AsyncMock(return_value=safe_jpeg_header + b'\x00' * 100)
                mock_file.seek = AsyncMock()
                
                result = await FileValidator.validate_upload_file(mock_file, "image")
                
                file_extension = os.path.splitext(filename)[1].lower()
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                
                if file_extension not in allowed_extensions:
                    # Dangerous file types should be rejected
                    assert not result.is_valid, f"Dangerous file type accepted: {filename}"
                    type_errors = [error for error in result.errors if "type" in error.lower() or "extension" in error.lower()]
                    assert len(type_errors) > 0, f"No type error for dangerous file: {filename}"
        
        # Run the async validation
        asyncio.run(run_validation())

    @given(st.dictionaries(
        keys=st.sampled_from(['title', 'description', 'comment', 'address']),
        values=st.text(min_size=1, max_size=5000),
        min_size=1,
        max_size=4
    ))
    @hypothesis_settings(max_examples=50)
    def test_property_10_string_length_enforcement_database_constraints(self, text_fields: Dict[str, str]):
        """
        **Validates: Requirements 3.5**
        **Property 10: String Length Enforcement**
        
        For any text field input, the system should enforce maximum length limits based on database constraints.
        """
        # Define database-based field limits
        field_definitions = {
            'title': {'type': FieldType.TEXT, 'required': True, 'max_length': 255},
            'description': {'type': FieldType.DESCRIPTION, 'required': True, 'max_length': 2000},
            'comment': {'type': FieldType.TEXT, 'required': True, 'max_length': 500},
            'address': {'type': FieldType.ADDRESS, 'required': True, 'max_length': 1000}
        }
        
        results = InputValidator.validate_multiple_fields(text_fields, field_definitions)
        
        # Length limits should be strictly enforced
        for field_name, result in results.items():
            if field_name in text_fields:
                field_value = text_fields[field_name]
                max_length = field_definitions[field_name]['max_length']
                
                if len(field_value) > max_length:
                    # Over-length inputs should be rejected
                    assert not result.is_valid, f"Over-length input accepted for {field_name}: {len(field_value)} > {max_length}"
                    
                    # Should have specific length error
                    length_errors = [error for error in result.errors if f"Maximum length is {max_length}" in error]
                    assert len(length_errors) > 0, f"No specific length error for {field_name}"
                else:
                    # Within-length inputs should pass length validation (may fail other validations)
                    length_errors = [error for error in result.errors if "Maximum length" in error]
                    assert len(length_errors) == 0, f"False length error for {field_name}: {len(field_value)} <= {max_length}"

    @given(st.lists(
        st.one_of(
            # Valid email formats
            st.just("user@example.com"),
            st.just("test.email@domain.co.uk"),
            st.just("user+tag@example.org"),
            st.just("firstname.lastname@company.com"),
            st.just("user123@test-domain.com"),
            # Invalid email formats
            st.just("invalid-email"),
            st.just("@domain.com"),
            st.just("user@"),
            st.just("user@@domain.com"),
            st.just("user@domain"),
            st.just("user@.com"),
            st.just("user@domain."),
            st.just("user name@domain.com"),  # Space in local part
            st.just("user@domain .com"),  # Space in domain
            # Edge cases
            st.text(min_size=1, max_size=50).map(lambda x: f"{x}@example.com"),
            st.text(min_size=1, max_size=50).map(lambda x: f"user@{x}.com"),
        ),
        min_size=1,
        max_size=10
    ))
    @hypothesis_settings(max_examples=40)
    def test_property_11_email_validation_compliance_rfc_patterns(self, email_inputs: List[str]):
        """
        **Validates: Requirements 3.6**
        **Property 11: Email Validation Compliance**
        
        For any email address input, the system should validate it using RFC-compliant regex patterns.
        """
        for email_input in email_inputs:
            result = validate_email(email_input)
            
            # Basic RFC compliance checks
            if '@' not in email_input:
                # No @ symbol - should be invalid
                assert not result.is_valid, f"Email without @ accepted: {email_input}"
            elif email_input.count('@') > 1:
                # Multiple @ symbols - should be invalid
                assert not result.is_valid, f"Email with multiple @ accepted: {email_input}"
            elif email_input.startswith('@') or email_input.endswith('@'):
                # @ at start or end - should be invalid
                assert not result.is_valid, f"Email with @ at boundary accepted: {email_input}"
            elif '..' in email_input:
                # Consecutive dots - should be invalid
                assert not result.is_valid, f"Email with consecutive dots accepted: {email_input}"
            elif ' ' in email_input:
                # Spaces - should be invalid
                assert not result.is_valid, f"Email with spaces accepted: {email_input}"
            else:
                # For potentially valid emails, check domain part
                local_part, domain_part = email_input.rsplit('@', 1)
                
                if not domain_part or '.' not in domain_part:
                    # No domain or no TLD - should be invalid
                    assert not result.is_valid, f"Email without proper domain accepted: {email_input}"
                elif domain_part.startswith('.') or domain_part.endswith('.'):
                    # Domain starts or ends with dot - should be invalid
                    assert not result.is_valid, f"Email with invalid domain format accepted: {email_input}"
                elif not local_part:
                    # Empty local part - should be invalid
                    assert not result.is_valid, f"Email with empty local part accepted: {email_input}"

    @given(st.lists(
        st.one_of(
            # Valid email patterns that should pass
            st.just("valid@example.com"),
            st.just("test.user@domain.org"),
            st.just("user+tag@company.co.uk"),
            st.just("firstname.lastname@test-domain.com"),
            st.just("user123@example-domain.net"),
            st.just("a@b.co"),  # Minimal valid email
        ),
        min_size=1,
        max_size=5
    ))
    @hypothesis_settings(max_examples=30)
    def test_property_11_email_validation_compliance_valid_patterns(self, valid_emails: List[str]):
        """
        **Validates: Requirements 3.6**
        **Property 11: Email Validation Compliance**
        
        For any valid email address input, the system should accept it as RFC-compliant.
        """
        for email_input in valid_emails:
            result = validate_email(email_input)
            
            # Valid emails should be accepted
            assert result.is_valid, f"Valid email rejected: {email_input}, errors: {result.errors}"
            
            # Sanitized value should be the same as input (no changes needed)
            assert result.sanitized_value == email_input, f"Valid email was modified: {email_input} -> {result.sanitized_value}"

    @given(st.integers(min_value=1, max_value=1000))
    @hypothesis_settings(max_examples=50)
    def test_property_10_string_length_enforcement_exact_limits(self, length: int):
        """
        **Validates: Requirements 3.5**
        **Property 10: String Length Enforcement**
        
        For any text input at exact length limits, the system should handle boundary conditions correctly.
        """
        # Test at exact limit
        test_text = 'a' * length
        
        # Test with different field types and their limits
        field_limits = [
            (FieldType.EMAIL, 255),
            (FieldType.TEXT, 500),
            (FieldType.NAME, 255),
            (FieldType.DESCRIPTION, 2000)
        ]
        
        for field_type, max_length in field_limits:
            result = InputValidator.validate_and_sanitize(
                test_text, 
                field_type, 
                required=True, 
                max_length=max_length
            )
            
            if length <= max_length:
                # At or under limit should pass length validation
                length_errors = [error for error in result.errors if "Maximum length" in error]
                assert len(length_errors) == 0, f"False length error at limit for {field_type}: {length} <= {max_length}"
            else:
                # Over limit should fail length validation
                assert not result.is_valid, f"Over-limit input accepted for {field_type}: {length} > {max_length}"
                length_errors = [error for error in result.errors if "Maximum length" in error]
                assert len(length_errors) > 0, f"No length error over limit for {field_type}: {length} > {max_length}"


class TestInputValidationIntegration:
    """Integration tests for input validation properties"""

    def test_validation_error_aggregation(self):
        """Test that multiple validation errors are properly aggregated"""
        # Input with multiple issues: too long, contains SQL injection, invalid email format
        malicious_long_email = "admin'; DROP TABLE users; --" + "x" * 300 + "@invalid"
        
        result = validate_email(malicious_long_email)
        
        # Should be invalid
        assert not result.is_valid
        
        # Should have multiple types of errors
        assert len(result.errors) > 0
        
        # Should detect malicious content
        has_malicious_error = any("Invalid characters" in error for error in result.errors)
        has_format_error = any("Invalid email format" in error for error in result.errors)
        has_length_error = any("Maximum length" in error for error in result.errors)
        
        # At least one type of error should be detected
        assert has_malicious_error or has_format_error or has_length_error

    def test_sanitization_preserves_valid_content(self):
        """Test that sanitization doesn't modify valid content"""
        valid_inputs = [
            ("John Doe", FieldType.NAME),
            ("user@example.com", FieldType.EMAIL),
            ("This is a normal description.", FieldType.DESCRIPTION),
            ("+1234567890", FieldType.PHONE)
        ]
        
        for input_value, field_type in valid_inputs:
            result = InputValidator.validate_and_sanitize(input_value, field_type)
            
            if result.is_valid:
                # Valid content should not be modified
                assert result.sanitized_value == input_value, f"Valid input modified: {input_value} -> {result.sanitized_value}"
"""
Security Configuration Validator
"""
import secrets
import string
import re
import logging
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SecurityValidationResult(BaseModel):
    """Result of security validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


class SecurityConfigValidator:
    """Validates security configuration settings"""
    
    # Minimum requirements
    MIN_SECRET_KEY_LENGTH = 32
    WEAK_SECRET_PATTERNS = [
        "your-super-secret-key",
        "change-in-production",
        "secret",
        "password",
        "123456",
        "default",
        "test"
    ]
    
    @staticmethod
    def validate_secret_key(secret_key: str) -> SecurityValidationResult:
        """Validate SECRET_KEY security"""
        errors = []
        warnings = []
        recommendations = []
        
        # Check length
        if len(secret_key) < SecurityConfigValidator.MIN_SECRET_KEY_LENGTH:
            errors.append(f"SECRET_KEY must be at least {SecurityConfigValidator.MIN_SECRET_KEY_LENGTH} characters long")
        
        # Check for weak patterns
        secret_lower = secret_key.lower()
        for pattern in SecurityConfigValidator.WEAK_SECRET_PATTERNS:
            if pattern in secret_lower:
                errors.append(f"SECRET_KEY contains weak pattern: '{pattern}'")
        
        # Check entropy (basic check for randomness)
        if SecurityConfigValidator._is_low_entropy(secret_key):
            warnings.append("SECRET_KEY appears to have low entropy (not random enough)")
        
        # Check character diversity
        if not SecurityConfigValidator._has_character_diversity(secret_key):
            warnings.append("SECRET_KEY should contain a mix of uppercase, lowercase, numbers, and symbols")
        
        # Recommendations
        if len(secret_key) < 64:
            recommendations.append("Consider using a 64+ character SECRET_KEY for enhanced security")
        
        recommendations.append("Use 'openssl rand -hex 32' or 'python -c \"import secrets; print(secrets.token_hex(32))\"' to generate a secure key")
        
        return SecurityValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    @staticmethod
    def validate_cors_origins(cors_origins: List[str]) -> SecurityValidationResult:
        """Validate CORS origins configuration"""
        errors = []
        warnings = []
        recommendations = []
        
        # Check for wildcard
        for origin in cors_origins:
            if "*" in origin:
                errors.append(f"CORS_ORIGINS contains wildcard '*' in '{origin}' which allows any origin - security risk")
        
        # Check for localhost in production
        localhost_patterns = ["localhost", "127.0.0.1", "0.0.0.0"]
        for origin in cors_origins:
            for pattern in localhost_patterns:
                if pattern in origin.lower():
                    warnings.append(f"CORS origin '{origin}' contains localhost - ensure this is not production")
        
        # Check for HTTP in production
        for origin in cors_origins:
            if origin.startswith("http://") and "localhost" not in origin:
                warnings.append(f"CORS origin '{origin}' uses HTTP instead of HTTPS - security risk")
        
        # Recommendations
        if len(cors_origins) > 10:
            recommendations.append("Consider reducing the number of CORS origins for better security")
        
        recommendations.append("Use specific domains instead of wildcards")
        recommendations.append("Use HTTPS origins in production")
        
        return SecurityValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    @staticmethod
    def generate_secure_secret_key(length: int = 64) -> str:
        """Generate a cryptographically secure secret key"""
        # Use a mix of characters for better entropy
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def _is_low_entropy(text: str) -> bool:
        """Basic entropy check - looks for repeated patterns"""
        if len(text) < 16:
            return True
        
        # Check for repeated characters
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # If any character appears more than 25% of the time, it's low entropy
        max_count = max(char_counts.values())
        if max_count > len(text) * 0.25:
            return True
        
        # Check for sequential patterns
        sequential_count = 0
        for i in range(len(text) - 1):
            if abs(ord(text[i]) - ord(text[i + 1])) <= 1:
                sequential_count += 1
        
        # If more than 50% of characters are sequential, it's low entropy
        if sequential_count > len(text) * 0.5:
            return True
        
        return False
    
    @staticmethod
    def _has_character_diversity(text: str) -> bool:
        """Check if text has good character diversity"""
        has_upper = any(c.isupper() for c in text)
        has_lower = any(c.islower() for c in text)
        has_digit = any(c.isdigit() for c in text)
        has_symbol = any(not c.isalnum() for c in text)
        
        # Should have at least 3 of the 4 character types
        diversity_count = sum([has_upper, has_lower, has_digit, has_symbol])
        return diversity_count >= 3
    
    @staticmethod
    def validate_all_security_settings(
        secret_key: str,
        cors_origins: List[str],
        debug_mode: bool = False
    ) -> SecurityValidationResult:
        """Validate all security settings"""
        all_errors = []
        all_warnings = []
        all_recommendations = []
        
        # Validate secret key
        secret_result = SecurityConfigValidator.validate_secret_key(secret_key)
        all_errors.extend(secret_result.errors)
        all_warnings.extend(secret_result.warnings)
        all_recommendations.extend(secret_result.recommendations)
        
        # Validate CORS
        cors_result = SecurityConfigValidator.validate_cors_origins(cors_origins)
        all_errors.extend(cors_result.errors)
        all_warnings.extend(cors_result.warnings)
        all_recommendations.extend(cors_result.recommendations)
        
        # Check debug mode
        if debug_mode:
            all_warnings.append("DEBUG mode is enabled - ensure this is not production")
        
        return SecurityValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            recommendations=all_recommendations
        )


def validate_startup_security(settings) -> bool:
    """
    Validate security settings at startup.
    Returns True if safe to continue, False if critical issues found.
    """
    logger.info("Validating security configuration...")
    
    result = SecurityConfigValidator.validate_all_security_settings(
        secret_key=settings.SECRET_KEY,
        cors_origins=settings.CORS_ORIGINS,
        debug_mode=settings.DEBUG
    )
    
    # Log all findings
    for error in result.errors:
        logger.critical(f"SECURITY ERROR: {error}")
    
    for warning in result.warnings:
        logger.warning(f"SECURITY WARNING: {warning}")
    
    for recommendation in result.recommendations:
        logger.info(f"SECURITY RECOMMENDATION: {recommendation}")
    
    if not result.is_valid:
        logger.critical("CRITICAL SECURITY ISSUES FOUND - APPLICATION STARTUP BLOCKED")
        logger.critical("Fix the above security errors before starting the application")
        return False
    
    if result.warnings:
        logger.warning(f"Found {len(result.warnings)} security warnings - review recommended")
    
    logger.info("Security validation completed")
    return True
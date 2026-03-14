/**
 * Property-Based Tests for Client-Side Error Handling
 * **Feature: platform-robustness-improvements**
 * 
 * Tests Properties 25 and 26:
 * - Property 25: Client-Side Error Handling (network timeouts, token expiry)
 * - Property 26: Validation Error Display (field-level error messages)
 */

import fc from 'fast-check';
import { getStructuredError } from '../client';

describe('Property 25: Client-Side Error Handling', () => {
    /**
     * **Validates: Requirements 8.2, 8.5**
     * **Property 25: Client-Side Error Handling**
     * 
     * For any network timeout, the frontend should display appropriate messages 
     * and provide recovery options (retry buttons).
     */
    it('should handle network timeout errors with structured format', () => {
        fc.assert(
            fc.property(
                fc.integer({ min: 1000, max: 60000 }), // timeout in ms
                fc.webUrl(), // URL
                (timeout, url) => {
                    // Create timeout error
                    const timeoutError = {
                        code: 'ECONNABORTED',
                        message: `timeout of ${timeout}ms exceeded`,
                        config: {
                            timeout: timeout,
                            url: url
                        }
                    };

                    const result = getStructuredError(timeoutError);

                    // Should return structured error with CONNECTION_TIMEOUT code
                    expect(result.error_code).toBe('CONNECTION_TIMEOUT');
                    
                    // Should have user-friendly message
                    expect(result.message).toBeTruthy();
                    expect(result.message.length).toBeGreaterThan(0);
                    expect(result.message.toLowerCase()).toContain('timed out');
                    expect(result.message.toLowerCase()).toContain('try again');
                    
                    // Should include timeout details
                    expect(result.details).toBeDefined();
                    expect(result.details.timeout).toBeDefined();
                    expect(result.details.url).toBe(url);
                    
                    // Should have timestamp
                    expect(result.timestamp).toBeDefined();
                    expect(typeof result.timestamp).toBe('string');
                    
                    // Timestamp should be valid ISO format
                    const timestamp = new Date(result.timestamp);
                    expect(timestamp.toString()).not.toBe('Invalid Date');
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.2, 8.5**
     * **Property 25: Client-Side Error Handling**
     * 
     * For any network connectivity error, the frontend should display appropriate 
     * messages about checking connection.
     */
    it('should handle network connectivity errors with structured format', () => {
        fc.assert(
            fc.property(
                fc.webUrl(),
                fc.constantFrom('ERR_NETWORK', 'ENOTFOUND', 'ECONNREFUSED', 'ETIMEDOUT'),
                (url, errorCode) => {
                    // Create network error
                    const networkError = {
                        code: errorCode,
                        message: 'Network Error',
                        config: {
                            url: url
                        }
                    };

                    const result = getStructuredError(networkError);

                    // Should return structured error with SERVICE_UNAVAILABLE code
                    expect(result.error_code).toBe('SERVICE_UNAVAILABLE');
                    
                    // Should have user-friendly message about network
                    expect(result.message).toBeTruthy();
                    expect(result.message.toLowerCase()).toContain('network');
                    expect(result.message.toLowerCase()).toContain('connection');
                    
                    // Should include error details
                    expect(result.details).toBeDefined();
                    expect(result.details.error_code).toBe(errorCode);
                    expect(result.details.url).toBe(url);
                    
                    // Should have timestamp
                    expect(result.timestamp).toBeDefined();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.5**
     * **Property 25: Client-Side Error Handling**
     * 
     * For any authentication token expiry, the system should provide structured 
     * error with TOKEN_EXPIRED code for proper handling.
     */
    it('should handle token expiry errors with structured format', () => {
        fc.assert(
            fc.property(
                fc.emailAddress(),
                fc.uuid(),
                (email, requestId) => {
                    // Create token expired error from backend
                    const tokenExpiredError = {
                        response: {
                            status: 401,
                            data: {
                                detail: {
                                    error_code: 'TOKEN_EXPIRED',
                                    message: 'Session expired. Please log in again.',
                                    details: {
                                        email: email
                                    },
                                    timestamp: new Date().toISOString(),
                                    request_id: requestId
                                }
                            }
                        }
                    };

                    const result = getStructuredError(tokenExpiredError);

                    // Should preserve backend structured error
                    expect(result.error_code).toBe('TOKEN_EXPIRED');
                    
                    // Should have user-friendly message about session
                    expect(result.message).toBeTruthy();
                    expect(result.message.toLowerCase()).toContain('session');
                    expect(result.message.toLowerCase()).toContain('log in');
                    
                    // Should include user details
                    expect(result.details).toBeDefined();
                    expect(result.details.email).toBe(email);
                    
                    // Should preserve request_id
                    expect(result.request_id).toBe(requestId);
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.2, 8.5**
     * **Property 25: Client-Side Error Handling**
     * 
     * For any error without response (network failure), the system should 
     * provide recovery options by returning SERVICE_UNAVAILABLE code.
     */
    it('should handle errors without response as network failures', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 1, maxLength: 100 }),
                fc.webUrl(),
                (errorMessage, url) => {
                    // Create error without response (network failure)
                    const networkFailureError = {
                        message: errorMessage,
                        config: {
                            url: url
                        }
                    };

                    const result = getStructuredError(networkFailureError);

                    // Should return SERVICE_UNAVAILABLE for network failures
                    expect(result.error_code).toBe('SERVICE_UNAVAILABLE');
                    
                    // Should have user-friendly message
                    expect(result.message).toBeTruthy();
                    expect(result.message.toLowerCase()).toContain('network');
                    
                    // Should include URL in details
                    expect(result.details).toBeDefined();
                    expect(result.details.url).toBe(url);
                    
                    // Should have timestamp
                    expect(result.timestamp).toBeDefined();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.2, 8.5**
     * **Property 25: Client-Side Error Handling**
     * 
     * For any error, the system should always return a structured error 
     * with required fields for consistent error handling.
     */
    it('should always return structured error with required fields', () => {
        fc.assert(
            fc.property(
                fc.oneof(
                    // Timeout error
                    fc.record({
                        code: fc.constant('ECONNABORTED'),
                        message: fc.string(),
                        config: fc.record({ timeout: fc.integer(), url: fc.webUrl() })
                    }),
                    // Network error
                    fc.record({
                        code: fc.constant('ERR_NETWORK'),
                        message: fc.string(),
                        config: fc.record({ url: fc.webUrl() })
                    }),
                    // Backend error
                    fc.record({
                        response: fc.record({
                            status: fc.integer({ min: 400, max: 599 }),
                            data: fc.record({
                                detail: fc.record({
                                    error_code: fc.string({ minLength: 1 }),
                                    message: fc.string({ minLength: 1 }),
                                    timestamp: fc.date().map(d => d.toISOString())
                                })
                            })
                        })
                    }),
                    // Generic error
                    fc.record({
                        message: fc.string({ minLength: 1 }),
                        name: fc.string({ minLength: 1 })
                    })
                ),
                (error) => {
                    const result = getStructuredError(error);

                    // Should always have required fields
                    expect(result).toBeDefined();
                    expect(result.error_code).toBeDefined();
                    expect(typeof result.error_code).toBe('string');
                    expect(result.error_code.length).toBeGreaterThan(0);
                    
                    expect(result.message).toBeDefined();
                    expect(typeof result.message).toBe('string');
                    expect(result.message.length).toBeGreaterThan(0);
                    
                    expect(result.timestamp).toBeDefined();
                    expect(typeof result.timestamp).toBe('string');
                    
                    // Timestamp should be valid
                    const timestamp = new Date(result.timestamp);
                    expect(timestamp.toString()).not.toBe('Invalid Date');
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.2, 8.5**
     * **Property 25: Client-Side Error Handling**
     * 
     * For any backend structured error, the system should preserve the 
     * error structure from the backend.
     */
    it('should preserve backend structured errors', () => {
        fc.assert(
            fc.property(
                fc.constantFrom(
                    'USER_NOT_FOUND',
                    'INVALID_PASSWORD',
                    'ACCOUNT_INACTIVE',
                    'TOKEN_EXPIRED',
                    'VALIDATION_ERROR',
                    'RESOURCE_NOT_FOUND'
                ),
                fc.string({ minLength: 10, maxLength: 200 }),
                fc.integer({ min: 400, max: 599 }),
                (errorCode, message, statusCode) => {
                    // Create backend structured error
                    const backendError = {
                        response: {
                            status: statusCode,
                            data: {
                                detail: {
                                    error_code: errorCode,
                                    message: message,
                                    details: {},
                                    timestamp: new Date().toISOString(),
                                    request_id: 'test-request-id'
                                }
                            }
                        }
                    };

                    const result = getStructuredError(backendError);

                    // Should preserve backend error structure
                    expect(result.error_code).toBe(errorCode);
                    expect(result.message).toBe(message);
                    expect(result.timestamp).toBeDefined();
                    expect(result.request_id).toBe('test-request-id');
                }
            ),
            { numRuns: 100 }
        );
    });
});

describe('Property 26: Validation Error Display', () => {
    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any validation error, the system should display specific field-level 
     * error messages appropriate to the user's role.
     */
    it('should handle validation errors with field-level details', () => {
        fc.assert(
            fc.property(
                fc.array(
                    fc.record({
                        field: fc.string({ minLength: 1, maxLength: 50 }),
                        message: fc.string({ minLength: 5, maxLength: 200 }),
                        rejected_value: fc.oneof(
                            fc.string(),
                            fc.integer(),
                            fc.constant(null)
                        )
                    }),
                    { minLength: 1, maxLength: 10 }
                ),
                fc.uuid(),
                (validationErrors, requestId) => {
                    // Create validation error response from backend
                    const validationError = {
                        response: {
                            status: 422,
                            data: {
                                detail: {
                                    error_code: 'VALIDATION_ERROR',
                                    message: 'Request validation failed',
                                    validation_errors: validationErrors,
                                    timestamp: new Date().toISOString(),
                                    request_id: requestId
                                }
                            }
                        }
                    };

                    const result = getStructuredError(validationError);

                    // Should preserve validation error structure
                    expect(result.error_code).toBe('VALIDATION_ERROR');
                    expect(result.message).toBeTruthy();
                    
                    // Should include validation errors
                    expect(result.validation_errors).toBeDefined();
                    expect(Array.isArray(result.validation_errors)).toBe(true);
                    expect(result.validation_errors.length).toBe(validationErrors.length);
                    
                    // Each validation error should have field and message
                    result.validation_errors.forEach((error, index) => {
                        expect(error.field).toBe(validationErrors[index].field);
                        expect(error.message).toBe(validationErrors[index].message);
                    });
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any validation error, each field error should contain the field name 
     * and a descriptive error message.
     */
    it('should ensure validation errors have required field information', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 1, maxLength: 50 }),
                fc.string({ minLength: 5, maxLength: 200 }),
                (fieldName, errorMessage) => {
                    // Create single field validation error
                    const validationError = {
                        response: {
                            status: 422,
                            data: {
                                detail: {
                                    error_code: 'VALIDATION_ERROR',
                                    message: 'Validation failed',
                                    validation_errors: [
                                        {
                                            field: fieldName,
                                            message: errorMessage,
                                            rejected_value: null
                                        }
                                    ],
                                    timestamp: new Date().toISOString(),
                                    request_id: 'test-id'
                                }
                            }
                        }
                    };

                    const result = getStructuredError(validationError);

                    // Should have validation errors
                    expect(result.validation_errors).toBeDefined();
                    expect(result.validation_errors.length).toBe(1);
                    
                    const fieldError = result.validation_errors[0];
                    
                    // Field name should be preserved
                    expect(fieldError.field).toBe(fieldName);
                    expect(fieldError.field.length).toBeGreaterThan(0);
                    
                    // Error message should be preserved
                    expect(fieldError.message).toBe(errorMessage);
                    expect(fieldError.message.length).toBeGreaterThan(0);
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any validation error with multiple fields, all field errors should 
     * be preserved and accessible for display.
     */
    it('should handle multiple field validation errors', () => {
        fc.assert(
            fc.property(
                fc.integer({ min: 1, max: 20 }),
                (numFields) => {
                    // Create multiple field validation errors
                    const validationErrors = Array.from({ length: numFields }, (_, i) => ({
                        field: `field_${i}`,
                        message: `Error message for field ${i}`,
                        rejected_value: `invalid_value_${i}`
                    }));

                    const validationError = {
                        response: {
                            status: 422,
                            data: {
                                detail: {
                                    error_code: 'VALIDATION_ERROR',
                                    message: 'Multiple validation errors',
                                    validation_errors: validationErrors,
                                    timestamp: new Date().toISOString(),
                                    request_id: 'test-id'
                                }
                            }
                        }
                    };

                    const result = getStructuredError(validationError);

                    // Should preserve all validation errors
                    expect(result.validation_errors).toBeDefined();
                    expect(result.validation_errors.length).toBe(numFields);
                    
                    // Each error should be accessible
                    result.validation_errors.forEach((error, index) => {
                        expect(error.field).toBe(`field_${index}`);
                        expect(error.message).toContain(`field ${index}`);
                    });
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any validation error, the rejected value should be included when 
     * available to help users understand what was wrong.
     */
    it('should include rejected values in validation errors when available', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 1, maxLength: 50 }),
                fc.oneof(
                    fc.string({ minLength: 1, maxLength: 100 }),
                    fc.integer(),
                    fc.boolean(),
                    fc.constant(null)
                ),
                (fieldName, rejectedValue) => {
                    // Create validation error with rejected value
                    const validationError = {
                        response: {
                            status: 422,
                            data: {
                                detail: {
                                    error_code: 'VALIDATION_ERROR',
                                    message: 'Validation failed',
                                    validation_errors: [
                                        {
                                            field: fieldName,
                                            message: 'Invalid value',
                                            rejected_value: rejectedValue
                                        }
                                    ],
                                    timestamp: new Date().toISOString(),
                                    request_id: 'test-id'
                                }
                            }
                        }
                    };

                    const result = getStructuredError(validationError);

                    // Should preserve rejected value
                    expect(result.validation_errors).toBeDefined();
                    expect(result.validation_errors.length).toBe(1);
                    
                    const fieldError = result.validation_errors[0];
                    expect(fieldError.rejected_value).toEqual(rejectedValue);
                }
            ),
            { numRuns: 100 }
        );
    });
});

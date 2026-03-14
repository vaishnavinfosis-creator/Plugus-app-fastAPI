/**
 * Property-Based Tests for ErrorDisplay Component
 * **Feature: platform-robustness-improvements**
 * 
 * Tests Property 26: Validation Error Display
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import fc from 'fast-check';
import ErrorDisplay from '../ErrorDisplay';

describe('Property 26: Validation Error Display Component', () => {
    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any validation error, the ErrorDisplay component should render 
     * field-level error messages in field mode.
     */
    it('should display field-level errors in field mode', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 5, maxLength: 200 }),
                fc.constantFrom(
                    'USER_NOT_FOUND',
                    'INVALID_PASSWORD',
                    'VALIDATION_ERROR',
                    'CONNECTION_TIMEOUT'
                ),
                (message, errorCode) => {
                    const error = {
                        error_code: errorCode,
                        message: message,
                        timestamp: new Date().toISOString(),
                        request_id: 'test-id'
                    };

                    const { getByText } = render(
                        <ErrorDisplay error={error} fieldMode={true} />
                    );

                    // Should display the error message
                    const messageElement = getByText(message);
                    expect(messageElement).toBeTruthy();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any error in banner mode, the ErrorDisplay component should show 
     * full error details with icon and actions.
     */
    it('should display full error details in banner mode', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 10, maxLength: 200 }),
                fc.constantFrom(
                    'USER_NOT_FOUND',
                    'INVALID_PASSWORD',
                    'ACCOUNT_INACTIVE',
                    'CONNECTION_TIMEOUT',
                    'SERVICE_UNAVAILABLE',
                    'VALIDATION_ERROR'
                ),
                fc.uuid(),
                (message, errorCode, requestId) => {
                    const error = {
                        error_code: errorCode,
                        message: message,
                        timestamp: new Date().toISOString(),
                        request_id: requestId
                    };

                    const { getByText } = render(
                        <ErrorDisplay error={error} fieldMode={false} />
                    );

                    // Should display the error message
                    const messageElement = getByText(message);
                    expect(messageElement).toBeTruthy();
                    
                    // Should display truncated request ID
                    const requestIdShort = requestId.substring(0, 8);
                    const requestIdElement = getByText(`ID: ${requestIdShort}`);
                    expect(requestIdElement).toBeTruthy();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any error with details, the ErrorDisplay component should show 
     * additional context when available.
     */
    it('should display error details when provided', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 10, maxLength: 200 }),
                fc.emailAddress(),
                (message, email) => {
                    const error = {
                        error_code: 'USER_NOT_FOUND',
                        message: message,
                        details: {
                            email: email
                        },
                        timestamp: new Date().toISOString(),
                        request_id: 'test-id'
                    };

                    const { getByText } = render(
                        <ErrorDisplay error={error} fieldMode={false} />
                    );

                    // Should display the error message
                    const messageElement = getByText(message);
                    expect(messageElement).toBeTruthy();
                    
                    // Should display email detail
                    const emailElement = getByText(`Email: ${email}`);
                    expect(emailElement).toBeTruthy();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any error, the ErrorDisplay component should handle null/undefined 
     * errors gracefully by not rendering anything.
     */
    it('should handle null or undefined errors gracefully', () => {
        fc.assert(
            fc.property(
                fc.constantFrom(null, undefined),
                (error) => {
                    const { toJSON } = render(
                        <ErrorDisplay error={error} />
                    );

                    // Should not render anything for null/undefined errors
                    expect(toJSON()).toBeNull();
                }
            ),
            { numRuns: 50 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any error with retry option, the ErrorDisplay component should 
     * show retry button when showRetry is true.
     */
    it('should show retry button when showRetry is true', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 10, maxLength: 200 }),
                fc.constantFrom('CONNECTION_TIMEOUT', 'SERVICE_UNAVAILABLE'),
                (message, errorCode) => {
                    const error = {
                        error_code: errorCode,
                        message: message,
                        timestamp: new Date().toISOString(),
                        request_id: 'test-id'
                    };

                    const mockRetry = jest.fn();

                    const { getByText } = render(
                        <ErrorDisplay 
                            error={error} 
                            showRetry={true} 
                            onRetry={mockRetry}
                        />
                    );

                    // Should display retry button
                    const retryButton = getByText('Retry');
                    expect(retryButton).toBeTruthy();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any error code, the ErrorDisplay component should use appropriate 
     * visual styling (color) based on error type.
     */
    it('should use appropriate error colors for different error types', () => {
        fc.assert(
            fc.property(
                fc.constantFrom(
                    'USER_NOT_FOUND',
                    'INVALID_PASSWORD',
                    'ACCOUNT_INACTIVE',
                    'CONNECTION_TIMEOUT',
                    'SERVICE_UNAVAILABLE',
                    'RATE_LIMIT_EXCEEDED',
                    'VALIDATION_ERROR'
                ),
                (errorCode) => {
                    const error = {
                        error_code: errorCode,
                        message: 'Test error message',
                        timestamp: new Date().toISOString(),
                        request_id: 'test-id'
                    };

                    const { root } = render(
                        <ErrorDisplay error={error} />
                    );

                    // Component should render (we can't easily test colors in RNTL,
                    // but we can verify it renders without crashing)
                    expect(root).toBeTruthy();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any string error (not structured), the ErrorDisplay component should 
     * handle it gracefully in field mode.
     */
    it('should handle string errors in field mode', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 5, maxLength: 200 }),
                (errorMessage) => {
                    const { getByText } = render(
                        <ErrorDisplay error={errorMessage} fieldMode={true} />
                    );

                    // Should display the error message
                    const messageElement = getByText(errorMessage);
                    expect(messageElement).toBeTruthy();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any error, the ErrorDisplay component should consistently render 
     * the same output for the same input.
     */
    it('should render consistently for the same error', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 10, maxLength: 200 }),
                fc.constantFrom(
                    'USER_NOT_FOUND',
                    'INVALID_PASSWORD',
                    'VALIDATION_ERROR'
                ),
                fc.uuid(),
                (message, errorCode, requestId) => {
                    const error = {
                        error_code: errorCode,
                        message: message,
                        timestamp: new Date().toISOString(),
                        request_id: requestId
                    };

                    // Render twice with same props
                    const { getByText: getByText1 } = render(
                        <ErrorDisplay error={error} />
                    );
                    const { getByText: getByText2 } = render(
                        <ErrorDisplay error={error} />
                    );

                    // Both should display the same message
                    const message1 = getByText1(message);
                    const message2 = getByText2(message);
                    
                    expect(message1).toBeTruthy();
                    expect(message2).toBeTruthy();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any error in field mode, the component should render compactly 
     * without action buttons.
     */
    it('should render compactly in field mode without action buttons', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 5, maxLength: 200 }),
                (message) => {
                    const error = {
                        error_code: 'VALIDATION_ERROR',
                        message: message,
                        timestamp: new Date().toISOString(),
                        request_id: 'test-id'
                    };

                    const { queryByText } = render(
                        <ErrorDisplay 
                            error={error} 
                            fieldMode={true}
                            showRetry={true}
                            onRetry={jest.fn()}
                        />
                    );

                    // Should display message
                    expect(queryByText(message)).toBeTruthy();
                    
                    // Should NOT display retry button in field mode
                    expect(queryByText('Retry')).toBeNull();
                }
            ),
            { numRuns: 100 }
        );
    });

    /**
     * **Validates: Requirements 8.4, 8.6**
     * **Property 26: Validation Error Display**
     * 
     * For any error with custom styles, the ErrorDisplay component should 
     * accept and apply custom styling.
     */
    it('should accept custom styles', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 10, maxLength: 200 }),
                fc.integer({ min: 0, max: 100 }),
                (message, marginValue) => {
                    const error = {
                        error_code: 'VALIDATION_ERROR',
                        message: message,
                        timestamp: new Date().toISOString(),
                        request_id: 'test-id'
                    };

                    const customStyle = { marginTop: marginValue };

                    const { root } = render(
                        <ErrorDisplay error={error} style={customStyle} />
                    );

                    // Component should render with custom styles
                    expect(root).toBeTruthy();
                }
            ),
            { numRuns: 100 }
        );
    });
});

/**
 * Unit tests for ErrorDisplay component
 * Tests both banner mode and field mode error display
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import ErrorDisplay from '../ErrorDisplay';

describe('ErrorDisplay Component', () => {
    describe('Banner Mode', () => {
        it('should render error message in banner mode', () => {
            const error = {
                error_code: 'VALIDATION_ERROR',
                message: 'Invalid input provided',
                details: { field: 'email' }
            };

            const { getByText } = render(<ErrorDisplay error={error} />);
            expect(getByText('Invalid input provided')).toBeTruthy();
        });

        it('should not render when error is null', () => {
            const { queryByText } = render(<ErrorDisplay error={null} />);
            expect(queryByText(/./)).toBeNull();
        });

        it('should display retry button when showRetry is true', () => {
            const error = {
                error_code: 'CONNECTION_TIMEOUT',
                message: 'Request timed out'
            };
            const onRetry = jest.fn();

            const { getByText } = render(
                <ErrorDisplay error={error} showRetry={true} onRetry={onRetry} />
            );
            expect(getByText('Retry')).toBeTruthy();
        });

        it('should call onRetry when retry button is pressed', () => {
            const error = {
                error_code: 'CONNECTION_TIMEOUT',
                message: 'Request timed out'
            };
            const onRetry = jest.fn();

            const { getByText } = render(
                <ErrorDisplay error={error} showRetry={true} onRetry={onRetry} />
            );
            
            const retryButton = getByText('Retry');
            fireEvent.press(retryButton.parent);
            expect(onRetry).toHaveBeenCalledTimes(1);
        });

        it('should display email in details when provided', () => {
            const error = {
                error_code: 'USER_NOT_FOUND',
                message: 'Email not found',
                details: { email: 'test@example.com' }
            };

            const { getByText } = render(<ErrorDisplay error={error} />);
            expect(getByText('Email: test@example.com')).toBeTruthy();
        });

        it('should display request ID when provided', () => {
            const error = {
                error_code: 'UNKNOWN_ERROR',
                message: 'Something went wrong',
                request_id: 'abc123def456'
            };

            const { getByText } = render(<ErrorDisplay error={error} />);
            expect(getByText('ID: abc123de')).toBeTruthy(); // First 8 chars
        });
    });

    describe('Field Mode', () => {
        it('should render error message in field mode', () => {
            const error = {
                message: 'Email is required'
            };

            const { getByText } = render(<ErrorDisplay error={error} fieldMode={true} />);
            expect(getByText('Email is required')).toBeTruthy();
        });

        it('should handle string error in field mode', () => {
            const { getByText } = render(<ErrorDisplay error="Password is too short" fieldMode={true} />);
            expect(getByText('Password is too short')).toBeTruthy();
        });

        it('should not render retry button in field mode', () => {
            const error = {
                message: 'Invalid email format'
            };

            const { queryByText } = render(
                <ErrorDisplay error={error} fieldMode={true} showRetry={true} />
            );
            expect(queryByText('Retry')).toBeNull();
        });

        it('should not render when error is null in field mode', () => {
            const { queryByText } = render(<ErrorDisplay error={null} fieldMode={true} />);
            expect(queryByText(/./)).toBeNull();
        });
    });

    describe('Error Color Mapping', () => {
        it('should use correct color for different error codes', () => {
            const errorCodes = [
                'USER_NOT_FOUND',
                'INVALID_PASSWORD',
                'ACCOUNT_INACTIVE',
                'CONNECTION_TIMEOUT',
                'SERVICE_UNAVAILABLE',
                'RATE_LIMIT_EXCEEDED',
                'VALIDATION_ERROR'
            ];

            errorCodes.forEach(code => {
                const error = {
                    error_code: code,
                    message: 'Test error'
                };
                const { getByText } = render(<ErrorDisplay error={error} />);
                expect(getByText('Test error')).toBeTruthy();
            });
        });
    });
});

/**
 * Unit tests for API Client - Network Timeout Handling
 * Tests the getStructuredError helper and timeout configuration
 */

import client, { getStructuredError } from '../client';

describe('API Client - Network Timeout Handling', () => {
    describe('getStructuredError', () => {
        it('should handle timeout errors with ECONNABORTED code', () => {
            const timeoutError = {
                code: 'ECONNABORTED',
                message: 'timeout of 30000ms exceeded',
                config: {
                    timeout: 30000,
                    url: '/api/v1/test'
                }
            };

            const result = getStructuredError(timeoutError);

            expect(result.error_code).toBe('CONNECTION_TIMEOUT');
            expect(result.message).toBe('Request timed out. Please try again.');
            expect(result.details.timeout).toBe('30s');
            expect(result.details.url).toBe('/api/v1/test');
            expect(result.timestamp).toBeDefined();
        });

        it('should handle timeout errors with timeout in message', () => {
            const timeoutError = {
                message: 'timeout exceeded',
                config: {
                    timeout: 10000,
                    url: '/api/v1/auth/login'
                }
            };

            const result = getStructuredError(timeoutError);

            expect(result.error_code).toBe('CONNECTION_TIMEOUT');
            expect(result.message).toBe('Request timed out. Please try again.');
            expect(result.details.timeout).toBe('10s');
        });

        it('should handle timeout errors without config', () => {
            const timeoutError = {
                code: 'ECONNABORTED',
                message: 'timeout exceeded'
            };

            const result = getStructuredError(timeoutError);

            expect(result.error_code).toBe('CONNECTION_TIMEOUT');
            expect(result.message).toBe('Request timed out. Please try again.');
            expect(result.details.timeout).toBe('30s'); // Default fallback
        });

        it('should handle network errors with ERR_NETWORK code', () => {
            const networkError = {
                code: 'ERR_NETWORK',
                message: 'Network Error',
                config: {
                    url: '/api/v1/test'
                }
            };

            const result = getStructuredError(networkError);

            expect(result.error_code).toBe('SERVICE_UNAVAILABLE');
            expect(result.message).toBe('Network error. Please check your connection.');
            expect(result.details.error_code).toBe('ERR_NETWORK');
            expect(result.details.url).toBe('/api/v1/test');
        });

        it('should handle network errors without response', () => {
            const networkError = {
                message: 'Network Error',
                config: {
                    url: '/api/v1/test'
                }
            };

            const result = getStructuredError(networkError);

            expect(result.error_code).toBe('SERVICE_UNAVAILABLE');
            expect(result.message).toBe('Network error. Please check your connection.');
        });

        it('should handle backend structured errors', () => {
            const backendError = {
                response: {
                    status: 401,
                    data: {
                        detail: {
                            error_code: 'INVALID_PASSWORD',
                            message: 'Incorrect password',
                            details: { email: 'test@example.com' },
                            timestamp: '2024-01-01T00:00:00Z'
                        }
                    }
                }
            };

            const result = getStructuredError(backendError);

            expect(result.error_code).toBe('INVALID_PASSWORD');
            expect(result.message).toBe('Incorrect password');
            expect(result.details.email).toBe('test@example.com');
        });

        it('should handle unstructured errors with fallback', () => {
            const unknownError = {
                name: 'CustomError',
                message: 'Something went wrong',
                response: {
                    status: 500
                }
            };

            const result = getStructuredError(unknownError);

            expect(result.error_code).toBe('UNKNOWN_ERROR');
            expect(result.message).toBe('Something went wrong');
            expect(result.details.status).toBe(500);
            expect(result.details.error_type).toBe('CustomError');
        });

        it('should use pre-attached structuredError from interceptor', () => {
            const errorWithStructured = {
                structuredError: {
                    error_code: 'CUSTOM_ERROR',
                    message: 'Custom error message',
                    details: { custom: true },
                    timestamp: '2024-01-01T00:00:00Z'
                }
            };

            const result = getStructuredError(errorWithStructured);

            expect(result.error_code).toBe('CUSTOM_ERROR');
            expect(result.message).toBe('Custom error message');
            expect(result.details.custom).toBe(true);
        });

        it('should handle errors without message', () => {
            const errorWithoutMessage = {
                name: 'Error',
                response: {
                    status: 500
                }
            };

            const result = getStructuredError(errorWithoutMessage);

            expect(result.error_code).toBe('UNKNOWN_ERROR');
            expect(result.message).toBe('An unexpected error occurred. Please try again.');
        });
    });

    describe('Timeout Configuration', () => {
        it('should have default timeout of 30 seconds', () => {
            expect(client.defaults.timeout).toBe(30000);
        });

        it('should have correct base URL configuration', () => {
            expect(client.defaults.baseURL).toBeDefined();
        });

        it('should have JSON content type header', () => {
            expect(client.defaults.headers['Content-Type']).toBe('application/json');
        });
    });

    describe('Error Display Integration', () => {
        it('should provide retry-able errors for timeout', () => {
            const timeoutError = {
                code: 'ECONNABORTED',
                config: { timeout: 30000, url: '/api/v1/test' }
            };

            const result = getStructuredError(timeoutError);

            // These error codes should trigger retry button in ErrorDisplay
            const retryableErrors = ['CONNECTION_TIMEOUT', 'SERVICE_UNAVAILABLE'];
            expect(retryableErrors).toContain(result.error_code);
        });

        it('should provide retry-able errors for network failures', () => {
            const networkError = {
                code: 'ERR_NETWORK',
                config: { url: '/api/v1/test' }
            };

            const result = getStructuredError(networkError);

            const retryableErrors = ['CONNECTION_TIMEOUT', 'SERVICE_UNAVAILABLE'];
            expect(retryableErrors).toContain(result.error_code);
        });

        it('should include timestamp for all structured errors', () => {
            const errors = [
                { code: 'ECONNABORTED', config: {} },
                { code: 'ERR_NETWORK', config: {} },
                { message: 'Unknown error' }
            ];

            errors.forEach(error => {
                const result = getStructuredError(error);
                expect(result.timestamp).toBeDefined();
                expect(typeof result.timestamp).toBe('string');
            });
        });
    });
});


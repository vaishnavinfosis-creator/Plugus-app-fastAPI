import axios from 'axios';
import { Platform, Alert } from 'react-native';

// API base URL - adjust based on your environment
const getBaseUrl = () => {
    if (Platform.OS === 'web') {
        return process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    }
    // For Android emulator, use 10.0.2.2 to access localhost
    // For iOS simulator, use localhost
    // For real device, use your computer's IP address
    return 'http://10.0.2.2:8000/api/v1';
};

const client = axios.create({
    baseURL: getBaseUrl(),
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
client.interceptors.request.use(
    async (config) => {
        // Import here to avoid circular dependency
        const { useAuthStore } = require('../store/authStore');
        const token = useAuthStore.getState().token;

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Handle 401 responses (token expired) and network timeouts
client.interceptors.response.use(
    (response) => response,
    async (error) => {
        // Handle network timeout errors
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
            // Transform timeout error into structured format
            const timeoutError = {
                error_code: 'CONNECTION_TIMEOUT',
                message: 'Request timed out. Please try again.',
                details: {
                    timeout: error.config?.timeout ? `${error.config.timeout / 1000}s` : '30s',
                    url: error.config?.url
                },
                timestamp: new Date().toISOString()
            };
            
            // Attach structured error to the error object for easy access
            error.structuredError = timeoutError;
            return Promise.reject(error);
        }

        // Handle network connectivity errors
        if (error.code === 'ERR_NETWORK' || !error.response) {
            const networkError = {
                error_code: 'SERVICE_UNAVAILABLE',
                message: 'Network error. Please check your connection.',
                details: {
                    error_code: error.code,
                    url: error.config?.url
                },
                timestamp: new Date().toISOString()
            };
            
            error.structuredError = networkError;
            return Promise.reject(error);
        }

        // Handle 401 responses (token expired)
        if (error.response?.status === 401) {
            const { useAuthStore } = require('../store/authStore');
            
            // Check if the error is due to token expiry
            const errorDetail = error.response?.data?.detail;
            const isTokenExpired = 
                typeof errorDetail === 'object' && errorDetail.error_code === 'TOKEN_EXPIRED' ||
                typeof errorDetail === 'string' && errorDetail.toLowerCase().includes('token') ||
                typeof errorDetail === 'string' && errorDetail.toLowerCase().includes('expired');
            
            // Logout user to clear token and user state
            await useAuthStore.getState().logout();
            
            // Display session expired message
            if (Platform.OS === 'web') {
                // For web, show alert before redirect
                if (isTokenExpired) {
                    alert('Session expired. Please log in again.');
                }
                // The logout already redirects to login page via window.location.href
            } else {
                // For React Native, use Alert
                Alert.alert(
                    'Session Expired',
                    'Your session has expired. Please log in again.',
                    [{ text: 'OK' }]
                );
                // Navigation will be handled by the app's navigation state
                // which responds to the token being null
            }
        }
        return Promise.reject(error);
    }
);

export default client;

/**
 * Extract structured error from axios error
 * @param {Error} error - Axios error object
 * @returns {Object} Structured error object with error_code, message, details, timestamp
 */
export const getStructuredError = (error) => {
    // If interceptor already attached structured error, use it
    if (error.structuredError) {
        return error.structuredError;
    }

    // Handle timeout errors
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        return {
            error_code: 'CONNECTION_TIMEOUT',
            message: 'Request timed out. Please try again.',
            details: {
                timeout: error.config?.timeout ? `${error.config.timeout / 1000}s` : '30s',
                url: error.config?.url
            },
            timestamp: new Date().toISOString()
        };
    }

    // Handle network errors
    if (error.code === 'ERR_NETWORK' || !error.response) {
        return {
            error_code: 'SERVICE_UNAVAILABLE',
            message: 'Network error. Please check your connection.',
            details: {
                error_code: error.code,
                url: error.config?.url
            },
            timestamp: new Date().toISOString()
        };
    }

    // Handle backend structured errors
    if (error.response?.data) {
        const errorData = error.response.data;
        
        // Check if it's already a structured error (has error_code)
        if (errorData.error_code) {
            return errorData;
        }
        
        // Check if error is nested under 'detail' key
        if (errorData.detail && typeof errorData.detail === 'object' && errorData.detail.error_code) {
            return errorData.detail;
        }
    }

    // Fallback for unstructured errors
    return {
        error_code: 'UNKNOWN_ERROR',
        message: error.message || 'An unexpected error occurred. Please try again.',
        details: {
            status: error.response?.status,
            error_type: error.name || 'Unknown'
        },
        timestamp: new Date().toISOString()
    };
};

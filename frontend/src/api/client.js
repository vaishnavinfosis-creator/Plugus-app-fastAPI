import axios from 'axios';
import { Platform } from 'react-native';

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

// Handle 401 responses (token expired)
client.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            const { useAuthStore } = require('../store/authStore');
            useAuthStore.getState().logout();
        }
        return Promise.reject(error);
    }
);

export default client;

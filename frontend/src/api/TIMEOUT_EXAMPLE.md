# Network Timeout Handling - Example

This document demonstrates how the network timeout handling works in practice.

## Example: User Profile Screen with Timeout Handling

```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import client, { getStructuredError } from '../api/client';
import ErrorDisplay from '../components/ErrorDisplay';

export default function UserProfileScreen() {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchProfile = async () => {
        setError(null);
        setLoading(true);

        try {
            // This request will timeout after 30 seconds (default)
            const response = await client.get('/users/profile');
            setProfile(response.data);
        } catch (e) {
            // getStructuredError automatically handles:
            // - Timeout errors (ECONNABORTED)
            // - Network errors (ERR_NETWORK)
            // - Backend errors (structured responses)
            const structuredError = getStructuredError(e);
            setError(structuredError);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProfile();
    }, []);

    const handleRetry = () => {
        fetchProfile();
    };

    const handleDismissError = () => {
        setError(null);
    };

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#1E88E5" />
                <Text style={styles.loadingText}>Loading profile...</Text>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            {/* Error Display with Retry Button */}
            {error && (
                <ErrorDisplay
                    error={error}
                    onRetry={handleRetry}
                    onDismiss={handleDismissError}
                    showRetry={['CONNECTION_TIMEOUT', 'SERVICE_UNAVAILABLE'].includes(error.error_code)}
                />
            )}

            {/* Profile Content */}
            {profile && (
                <View style={styles.profileContainer}>
                    <Text style={styles.name}>{profile.name}</Text>
                    <Text style={styles.email}>{profile.email}</Text>
                </View>
            )}

            {/* Manual Refresh Button */}
            <TouchableOpacity style={styles.refreshButton} onPress={fetchProfile}>
                <Text style={styles.refreshButtonText}>Refresh Profile</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 20,
        backgroundColor: '#fff',
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        marginTop: 10,
        fontSize: 16,
        color: '#666',
    },
    profileContainer: {
        padding: 20,
        backgroundColor: '#f5f5f5',
        borderRadius: 12,
        marginTop: 20,
    },
    name: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 8,
    },
    email: {
        fontSize: 16,
        color: '#666',
    },
    refreshButton: {
        backgroundColor: '#1E88E5',
        padding: 16,
        borderRadius: 12,
        alignItems: 'center',
        marginTop: 20,
    },
    refreshButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    },
});
```

## Timeout Scenarios

### Scenario 1: Request Times Out (30 seconds)

**What happens:**
1. User opens profile screen
2. Network is slow, request takes > 30 seconds
3. Axios throws ECONNABORTED error
4. Response interceptor catches it and attaches `structuredError`
5. `getStructuredError()` returns:
   ```javascript
   {
       error_code: 'CONNECTION_TIMEOUT',
       message: 'Request timed out. Please try again.',
       details: {
           timeout: '30s',
           url: '/api/v1/users/profile'
       },
       timestamp: '2024-01-15T10:30:00.000Z'
   }
   ```
6. ErrorDisplay shows error with retry button
7. User clicks retry, request is sent again

### Scenario 2: Network Unavailable

**What happens:**
1. User opens profile screen
2. Device has no internet connection
3. Axios throws ERR_NETWORK error
4. Response interceptor catches it and attaches `structuredError`
5. `getStructuredError()` returns:
   ```javascript
   {
       error_code: 'SERVICE_UNAVAILABLE',
       message: 'Network error. Please check your connection.',
       details: {
           error_code: 'ERR_NETWORK',
           url: '/api/v1/users/profile'
       },
       timestamp: '2024-01-15T10:30:00.000Z'
   }
   ```
6. ErrorDisplay shows error with retry button
7. User fixes connection and clicks retry

### Scenario 3: Custom Timeout for Specific Request

```javascript
const fetchLargeData = async () => {
    try {
        // Increase timeout to 60 seconds for large data
        const response = await client.get('/data/large', {
            timeout: 60000
        });
        setData(response.data);
    } catch (e) {
        const structuredError = getStructuredError(e);
        // If timeout occurs, details.timeout will show '60s'
        setError(structuredError);
    }
};
```

## Error Flow Diagram

```
User Action (API Request)
    ↓
Axios Request Interceptor
    ↓ (adds auth token)
Network Request
    ↓
    ├─→ Success → Response Data
    │
    ├─→ Timeout (>30s) → ECONNABORTED
    │       ↓
    │   Response Interceptor
    │       ↓
    │   Attach structuredError
    │       ↓
    │   getStructuredError()
    │       ↓
    │   CONNECTION_TIMEOUT
    │       ↓
    │   ErrorDisplay (with Retry)
    │
    ├─→ Network Error → ERR_NETWORK
    │       ↓
    │   Response Interceptor
    │       ↓
    │   Attach structuredError
    │       ↓
    │   getStructuredError()
    │       ↓
    │   SERVICE_UNAVAILABLE
    │       ↓
    │   ErrorDisplay (with Retry)
    │
    └─→ Backend Error (401, 404, etc.)
            ↓
        Response Interceptor
            ↓
        Check for structured error
            ↓
        getStructuredError()
            ↓
        Specific Error Code
            ↓
        ErrorDisplay (retry depends on error)
```

## Testing Timeout Handling

### Manual Testing

1. **Simulate Slow Network:**
   - Use Chrome DevTools Network throttling
   - Set to "Slow 3G" or custom profile
   - Make API request and wait for timeout

2. **Simulate Network Offline:**
   - Turn off WiFi/mobile data
   - Make API request
   - Should see SERVICE_UNAVAILABLE error

3. **Test Retry Functionality:**
   - Trigger timeout or network error
   - Click retry button
   - Verify request is sent again

### Unit Testing

See `__tests__/client.test.js` for comprehensive unit tests covering:
- Timeout error transformation
- Network error transformation
- Backend error handling
- Structured error format validation
- Retry button integration

## Best Practices

1. **Always use getStructuredError()** in catch blocks for consistent error handling
2. **Show retry button** for CONNECTION_TIMEOUT and SERVICE_UNAVAILABLE errors
3. **Include error details** in logs for debugging (but not in user-facing messages)
4. **Set appropriate timeouts** based on expected response time:
   - Quick operations: 10-15 seconds
   - Standard operations: 30 seconds (default)
   - Large data transfers: 60+ seconds
5. **Handle errors gracefully** - don't leave users stuck on loading screens
6. **Provide clear feedback** - use ErrorDisplay component for consistent UX

## Related Files

- `frontend/src/api/client.js` - Main API client with timeout handling
- `frontend/src/components/ErrorDisplay.js` - Error display component
- `frontend/src/screens/auth/LoginScreen.js` - Example implementation
- `frontend/src/api/__tests__/client.test.js` - Unit tests

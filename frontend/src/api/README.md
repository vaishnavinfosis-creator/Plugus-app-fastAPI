# API Client - Network Timeout Handling

## Overview

The API client (`client.js`) provides comprehensive network timeout and error handling for all HTTP requests in the application. It includes automatic error transformation, retry support, and user-friendly error messages.

## Features

### 1. Default Timeout Configuration
- **Default timeout**: 30 seconds for all requests
- **Configurable**: Can be overridden per request
- **Automatic handling**: Timeout errors are automatically caught and transformed

### 2. Network Error Handling

The client handles three main types of network errors:

#### Timeout Errors
- **Error Code**: `CONNECTION_TIMEOUT`
- **Triggers**: Request exceeds timeout limit
- **User Message**: "Request timed out. Please try again."
- **Retry**: Enabled by default

#### Network Connectivity Errors
- **Error Code**: `SERVICE_UNAVAILABLE`
- **Triggers**: No network connection, DNS failure, server unreachable
- **User Message**: "Network error. Please check your connection."
- **Retry**: Enabled by default

#### Backend Errors
- **Error Code**: Varies (e.g., `INVALID_PASSWORD`, `USER_NOT_FOUND`)
- **Triggers**: Backend returns structured error response
- **User Message**: Backend-provided message
- **Retry**: Depends on error type

### 3. Structured Error Format

All errors are transformed into a consistent format:

```javascript
{
    error_code: 'CONNECTION_TIMEOUT',
    message: 'Request timed out. Please try again.',
    details: {
        timeout: '30s',
        url: '/api/v1/endpoint'
    },
    timestamp: '2024-01-15T10:30:00.000Z'
}
```

## Usage

### Basic Request with Default Timeout

```javascript
import client from './api/client';

try {
    const response = await client.get('/users');
    console.log(response.data);
} catch (error) {
    // Error is automatically handled by interceptor
    // Access structured error via error.structuredError
    console.error(error.structuredError);
}
```

### Request with Custom Timeout

```javascript
import client from './api/client';

try {
    // 10 second timeout for login
    const response = await client.post('/auth/login', data, {
        timeout: 10000
    });
} catch (error) {
    console.error(error.structuredError);
}
```

### Using getStructuredError Helper

```javascript
import client, { getStructuredError } from './api/client';

try {
    const response = await client.get('/data');
} catch (error) {
    const structuredError = getStructuredError(error);
    
    // Display error to user
    setError(structuredError);
    
    // Check if retry is appropriate
    const retryableErrors = ['CONNECTION_TIMEOUT', 'SERVICE_UNAVAILABLE'];
    if (retryableErrors.includes(structuredError.error_code)) {
        // Show retry button
    }
}
```

### Integration with ErrorDisplay Component

```javascript
import { useState } from 'react';
import client, { getStructuredError } from './api/client';
import ErrorDisplay from '../components/ErrorDisplay';

function MyComponent() {
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const fetchData = async () => {
        setError(null);
        setLoading(true);
        
        try {
            const response = await client.get('/data');
            // Handle success
        } catch (e) {
            const structuredError = getStructuredError(e);
            setError(structuredError);
        } finally {
            setLoading(false);
        }
    };

    const handleRetry = () => {
        setError(null);
        fetchData();
    };

    return (
        <View>
            {error && (
                <ErrorDisplay
                    error={error}
                    onRetry={handleRetry}
                    showRetry={['CONNECTION_TIMEOUT', 'SERVICE_UNAVAILABLE'].includes(error.error_code)}
                />
            )}
            {/* Rest of component */}
        </View>
    );
}
```

## Error Codes Reference

| Error Code | Description | Retry Enabled | User Action |
|------------|-------------|---------------|-------------|
| `CONNECTION_TIMEOUT` | Request exceeded timeout limit | Yes | Check connection, retry |
| `SERVICE_UNAVAILABLE` | Network connectivity issue | Yes | Check connection, retry |
| `USER_NOT_FOUND` | Email not registered | No | Register or check email |
| `INVALID_PASSWORD` | Wrong password | No | Re-enter password |
| `ACCOUNT_INACTIVE` | Account disabled | No | Contact support |
| `TOKEN_EXPIRED` | Session expired | No | Login again (automatic) |
| `VALIDATION_ERROR` | Invalid input | No | Fix validation errors |
| `UNKNOWN_ERROR` | Unexpected error | No | Try again later |

## Interceptors

### Request Interceptor
- Automatically adds authentication token to requests
- Reads token from `authStore`

### Response Interceptor
- Handles timeout errors (ECONNABORTED)
- Handles network errors (ERR_NETWORK)
- Handles token expiry (401 status)
- Transforms errors into structured format
- Automatic logout on token expiry

## Testing

Unit tests are located in `__tests__/client.test.js` and cover:
- Timeout error handling
- Network error handling
- Backend error handling
- Structured error transformation
- Error display integration

To run tests (requires test dependencies):
```bash
npm test
```

## Requirements Validation

This implementation satisfies **Requirement 8.2**:
> WHEN network timeouts occur, THE Frontend_Client SHALL display "Request timed out. Please try again." with a retry button

**Implementation Details**:
- ✅ Timeout detection via ECONNABORTED code and timeout message
- ✅ Structured error with CONNECTION_TIMEOUT code
- ✅ User-friendly message: "Request timed out. Please try again."
- ✅ Retry button enabled via ErrorDisplay component
- ✅ Timeout details included (duration, URL)
- ✅ Consistent error format across all network errors

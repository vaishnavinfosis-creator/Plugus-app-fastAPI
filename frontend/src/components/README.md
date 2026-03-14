# Validation Error Display Components

This directory contains reusable components for displaying validation errors in forms, implementing **Requirement 8.4: Field-level error message display**.

## Components

### ErrorDisplay

A flexible error display component that supports two modes:

1. **Banner Mode** (default): Full-width error banner with icon, message, and optional retry/dismiss actions
2. **Field Mode**: Compact inline error message for form field validation

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `error` | Object/String | - | Error object with `error_code`, `message`, `details`, `request_id` or simple string |
| `onRetry` | Function | - | Callback for retry action |
| `onDismiss` | Function | - | Callback for dismiss action |
| `showRetry` | Boolean | `false` | Whether to show retry button |
| `fieldMode` | Boolean | `false` | Whether to display as field-level error (compact) |
| `style` | Object | `{}` | Additional styles |

#### Usage Examples

**Banner Mode (General Errors):**
```javascript
import ErrorDisplay from '../components/ErrorDisplay';

const error = {
    error_code: 'CONNECTION_TIMEOUT',
    message: 'Request timed out. Please check your connection.',
    details: { timeout: '10 seconds' }
};

<ErrorDisplay
    error={error}
    onRetry={handleRetry}
    showRetry={true}
    onDismiss={handleDismiss}
/>
```

**Field Mode (Validation Errors):**
```javascript
<ErrorDisplay
    error="Email is required"
    fieldMode={true}
/>

// Or with error object
<ErrorDisplay
    error={{ message: 'Invalid email format' }}
    fieldMode={true}
/>
```

### FormField

A reusable form field component with integrated validation error display. Wraps `TextInput` with label, icon, and automatic field-level error handling.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | String | - | Field label text |
| `icon` | String | - | Ionicons icon name |
| `value` | String | - | Input value |
| `onChangeText` | Function | - | Callback when text changes |
| `error` | String/Object | - | Error message or error object |
| `onClearError` | Function | - | Callback to clear error when user types |
| `placeholder` | String | - | Input placeholder text |
| `secureTextEntry` | Boolean | `false` | Whether to hide input (passwords) |
| `keyboardType` | String | `'default'` | Keyboard type |
| `autoCapitalize` | String | `'sentences'` | Auto-capitalization behavior |
| `multiline` | Boolean | `false` | Whether input is multiline |
| `numberOfLines` | Number | `1` | Number of lines for multiline |
| `editable` | Boolean | `true` | Whether input is editable |
| `rightIcon` | String | - | Right-side icon name |
| `onRightIconPress` | Function | - | Callback for right icon press |
| `style` | Object | `{}` | Additional container styles |
| `inputStyle` | Object | `{}` | Additional input styles |

#### Usage Example

```javascript
import FormField from '../components/FormField';

const [email, setEmail] = useState('');
const [fieldErrors, setFieldErrors] = useState({});

<FormField
    label="Email"
    icon="mail-outline"
    placeholder="Enter your email"
    value={email}
    onChangeText={setEmail}
    error={fieldErrors.email}
    onClearError={() => setFieldErrors({ ...fieldErrors, email: null })}
    keyboardType="email-address"
    autoCapitalize="none"
/>
```

## Complete Form Example

Here's a complete example of a login form with field-level validation:

```javascript
import React, { useState } from 'react';
import { View, TouchableOpacity, Text } from 'react-native';
import FormField from '../components/FormField';
import ErrorDisplay from '../components/ErrorDisplay';

export default function LoginScreen() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fieldErrors, setFieldErrors] = useState({});
    const [generalError, setGeneralError] = useState(null);
    const [showPassword, setShowPassword] = useState(false);

    const handleLogin = async () => {
        // Clear previous errors
        setFieldErrors({});
        setGeneralError(null);

        // Field-level validation
        const errors = {};
        if (!email.trim()) {
            errors.email = 'Email is required';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
            errors.email = 'Please enter a valid email address';
        }
        
        if (!password) {
            errors.password = 'Password is required';
        } else if (password.length < 6) {
            errors.password = 'Password must be at least 6 characters';
        }

        if (Object.keys(errors).length > 0) {
            setFieldErrors(errors);
            return;
        }

        try {
            // API call here
            await loginAPI(email, password);
        } catch (e) {
            // Display general error in banner mode
            setGeneralError({
                error_code: 'LOGIN_FAILED',
                message: 'Login failed. Please try again.',
                details: { email }
            });
        }
    };

    return (
        <View>
            {/* General error banner */}
            {generalError && (
                <ErrorDisplay
                    error={generalError}
                    onDismiss={() => setGeneralError(null)}
                />
            )}

            {/* Email field with validation */}
            <FormField
                label="Email"
                icon="mail-outline"
                placeholder="Enter your email"
                value={email}
                onChangeText={setEmail}
                error={fieldErrors.email}
                onClearError={() => setFieldErrors({ ...fieldErrors, email: null })}
                keyboardType="email-address"
                autoCapitalize="none"
            />

            {/* Password field with validation */}
            <FormField
                label="Password"
                icon="lock-closed-outline"
                placeholder="Enter your password"
                value={password}
                onChangeText={setPassword}
                error={fieldErrors.password}
                onClearError={() => setFieldErrors({ ...fieldErrors, password: null })}
                secureTextEntry={!showPassword}
                rightIcon={showPassword ? 'eye-off-outline' : 'eye-outline'}
                onRightIconPress={() => setShowPassword(!showPassword)}
            />

            <TouchableOpacity onPress={handleLogin}>
                <Text>Sign In</Text>
            </TouchableOpacity>
        </View>
    );
}
```

## Validation Patterns

### Required Field Validation
```javascript
if (!value.trim()) {
    errors.fieldName = 'Field name is required';
}
```

### Email Validation
```javascript
if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
    errors.email = 'Please enter a valid email address';
}
```

### Length Validation
```javascript
if (password.length < 6) {
    errors.password = 'Password must be at least 6 characters';
}
```

### Numeric Validation
```javascript
if (isNaN(parseFloat(price)) || parseFloat(price) <= 0) {
    errors.price = 'Please enter a valid price';
}
```

## Error Clearing Pattern

Always clear field errors when the user starts typing:

```javascript
<FormField
    value={email}
    onChangeText={setEmail}
    error={fieldErrors.email}
    onClearError={() => setFieldErrors({ ...fieldErrors, email: null })}
/>
```

The `FormField` component automatically calls `onClearError` when the user types and an error exists.

## Testing

Unit tests are provided in `__tests__/` directory:
- `ErrorDisplay.test.js`: Tests for ErrorDisplay component
- `FormField.test.js`: Tests for FormField component
- `ValidationIntegration.test.js`: Integration tests for validation workflow

Run tests with:
```bash
npm test
```

## Accessibility

Both components follow accessibility best practices:
- Error messages are clearly visible with appropriate colors
- Icons provide visual cues for error types
- Field-level errors appear immediately below the input for easy association
- Error text is readable with sufficient contrast

## Requirements Validation

These components implement **Requirement 8.4**:
> WHEN validation errors occur, THE Error_Handler SHALL display specific field-level error messages

The implementation provides:
- ✅ Field-level error display (compact inline mode)
- ✅ General error display (banner mode)
- ✅ Automatic error clearing on user input
- ✅ Multiple error display support
- ✅ Reusable components for consistent UX

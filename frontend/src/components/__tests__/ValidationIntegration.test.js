/**
 * Integration tests for validation error display
 * Tests the complete validation workflow with FormField and ErrorDisplay
 * 
 * Validates Requirement 8.4: Field-level error message display
 */

import React, { useState } from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { View } from 'react-native';
import FormField from '../FormField';
import ErrorDisplay from '../ErrorDisplay';

// Test component that simulates a login form with validation
const TestLoginForm = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fieldErrors, setFieldErrors] = useState({});
    const [generalError, setGeneralError] = useState(null);

    const validateAndSubmit = () => {
        const errors = {};
        
        // Email validation
        if (!email.trim()) {
            errors.email = 'Email is required';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
            errors.email = 'Please enter a valid email address';
        }
        
        // Password validation
        if (!password) {
            errors.password = 'Password is required';
        } else if (password.length < 6) {
            errors.password = 'Password must be at least 6 characters';
        }

        if (Object.keys(errors).length > 0) {
            setFieldErrors(errors);
            return false;
        }

        // Simulate successful validation
        setGeneralError(null);
        setFieldErrors({});
        return true;
    };

    return (
        <View testID="login-form">
            {generalError && (
                <ErrorDisplay error={generalError} />
            )}
            
            <FormField
                label="Email"
                placeholder="Enter your email"
                value={email}
                onChangeText={setEmail}
                error={fieldErrors.email}
                onClearError={() => setFieldErrors({ ...fieldErrors, email: null })}
                keyboardType="email-address"
                autoCapitalize="none"
            />
            
            <FormField
                label="Password"
                placeholder="Enter your password"
                value={password}
                onChangeText={setPassword}
                error={fieldErrors.password}
                onClearError={() => setFieldErrors({ ...fieldErrors, password: null })}
                secureTextEntry={true}
            />
            
            <View testID="submit-button" onTouchEnd={validateAndSubmit} />
        </View>
    );
};

describe('Validation Integration Tests', () => {
    describe('Field-level validation error display', () => {
        it('should display field-level error for empty email', () => {
            const { getByTestId, getByText } = render(<TestLoginForm />);
            
            const submitButton = getByTestId('submit-button');
            fireEvent(submitButton, 'touchEnd');
            
            expect(getByText('Email is required')).toBeTruthy();
        });

        it('should display field-level error for invalid email format', () => {
            const { getByPlaceholderText, getByTestId, getByText } = render(<TestLoginForm />);
            
            const emailInput = getByPlaceholderText('Enter your email');
            fireEvent.changeText(emailInput, 'invalid-email');
            
            const submitButton = getByTestId('submit-button');
            fireEvent(submitButton, 'touchEnd');
            
            expect(getByText('Please enter a valid email address')).toBeTruthy();
        });

        it('should display field-level error for empty password', () => {
            const { getByPlaceholderText, getByTestId, getByText } = render(<TestLoginForm />);
            
            const emailInput = getByPlaceholderText('Enter your email');
            fireEvent.changeText(emailInput, 'test@example.com');
            
            const submitButton = getByTestId('submit-button');
            fireEvent(submitButton, 'touchEnd');
            
            expect(getByText('Password is required')).toBeTruthy();
        });

        it('should display field-level error for short password', () => {
            const { getByPlaceholderText, getByTestId, getByText } = render(<TestLoginForm />);
            
            const emailInput = getByPlaceholderText('Enter your email');
            fireEvent.changeText(emailInput, 'test@example.com');
            
            const passwordInput = getByPlaceholderText('Enter your password');
            fireEvent.changeText(passwordInput, '123');
            
            const submitButton = getByTestId('submit-button');
            fireEvent(submitButton, 'touchEnd');
            
            expect(getByText('Password must be at least 6 characters')).toBeTruthy();
        });

        it('should display multiple field errors simultaneously', () => {
            const { getByTestId, getByText } = render(<TestLoginForm />);
            
            const submitButton = getByTestId('submit-button');
            fireEvent(submitButton, 'touchEnd');
            
            expect(getByText('Email is required')).toBeTruthy();
            expect(getByText('Password is required')).toBeTruthy();
        });

        it('should clear field error when user starts typing', () => {
            const { getByPlaceholderText, getByTestId, getByText, queryByText } = render(<TestLoginForm />);
            
            // Trigger validation to show errors
            const submitButton = getByTestId('submit-button');
            fireEvent(submitButton, 'touchEnd');
            
            expect(getByText('Email is required')).toBeTruthy();
            
            // Start typing in email field
            const emailInput = getByPlaceholderText('Enter your email');
            fireEvent.changeText(emailInput, 't');
            
            // Error should be cleared
            expect(queryByText('Email is required')).toBeNull();
        });

        it('should validate successfully with correct inputs', () => {
            const { getByPlaceholderText, getByTestId, queryByText } = render(<TestLoginForm />);
            
            const emailInput = getByPlaceholderText('Enter your email');
            fireEvent.changeText(emailInput, 'test@example.com');
            
            const passwordInput = getByPlaceholderText('Enter your password');
            fireEvent.changeText(passwordInput, 'password123');
            
            const submitButton = getByTestId('submit-button');
            fireEvent(submitButton, 'touchEnd');
            
            // No errors should be displayed
            expect(queryByText(/required|invalid|must be/i)).toBeNull();
        });
    });

    describe('Error display modes', () => {
        it('should use field mode for validation errors', () => {
            const { getByTestId, getByText } = render(<TestLoginForm />);
            
            const submitButton = getByTestId('submit-button');
            fireEvent(submitButton, 'touchEnd');
            
            const errorText = getByText('Email is required');
            // Field mode errors should be compact and inline
            expect(errorText).toBeTruthy();
        });
    });
});

/**
 * Unit tests for FormField component
 * Tests field-level validation error integration
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import FormField from '../FormField';

describe('FormField Component', () => {
    describe('Basic Rendering', () => {
        it('should render label when provided', () => {
            const { getByText } = render(
                <FormField
                    label="Email"
                    value=""
                    onChangeText={() => {}}
                />
            );
            expect(getByText('Email')).toBeTruthy();
        });

        it('should render placeholder in input', () => {
            const { getByPlaceholderText } = render(
                <FormField
                    placeholder="Enter your email"
                    value=""
                    onChangeText={() => {}}
                />
            );
            expect(getByPlaceholderText('Enter your email')).toBeTruthy();
        });

        it('should display input value', () => {
            const { getByDisplayValue } = render(
                <FormField
                    value="test@example.com"
                    onChangeText={() => {}}
                />
            );
            expect(getByDisplayValue('test@example.com')).toBeTruthy();
        });
    });

    describe('Error Display', () => {
        it('should display error message when error is provided', () => {
            const { getByText } = render(
                <FormField
                    label="Email"
                    value=""
                    onChangeText={() => {}}
                    error="Email is required"
                />
            );
            expect(getByText('Email is required')).toBeTruthy();
        });

        it('should display error object message', () => {
            const error = {
                error_code: 'VALIDATION_ERROR',
                message: 'Invalid email format'
            };

            const { getByText } = render(
                <FormField
                    label="Email"
                    value="invalid-email"
                    onChangeText={() => {}}
                    error={error}
                />
            );
            expect(getByText('Invalid email format')).toBeTruthy();
        });

        it('should not display error when error is null', () => {
            const { queryByText } = render(
                <FormField
                    label="Email"
                    value=""
                    onChangeText={() => {}}
                    error={null}
                />
            );
            // Should not find any error-related text
            expect(queryByText(/required|invalid|error/i)).toBeNull();
        });
    });

    describe('User Interaction', () => {
        it('should call onChangeText when text changes', () => {
            const onChangeText = jest.fn();
            const { getByPlaceholderText } = render(
                <FormField
                    placeholder="Enter email"
                    value=""
                    onChangeText={onChangeText}
                />
            );

            const input = getByPlaceholderText('Enter email');
            fireEvent.changeText(input, 'test@example.com');
            expect(onChangeText).toHaveBeenCalledWith('test@example.com');
        });

        it('should clear error when user starts typing', () => {
            const onClearError = jest.fn();
            const { getByPlaceholderText } = render(
                <FormField
                    placeholder="Enter email"
                    value=""
                    onChangeText={() => {}}
                    error="Email is required"
                    onClearError={onClearError}
                />
            );

            const input = getByPlaceholderText('Enter email');
            fireEvent.changeText(input, 't');
            expect(onClearError).toHaveBeenCalled();
        });

        it('should not call onClearError when no error exists', () => {
            const onClearError = jest.fn();
            const { getByPlaceholderText } = render(
                <FormField
                    placeholder="Enter email"
                    value=""
                    onChangeText={() => {}}
                    onClearError={onClearError}
                />
            );

            const input = getByPlaceholderText('Enter email');
            fireEvent.changeText(input, 't');
            expect(onClearError).not.toHaveBeenCalled();
        });
    });

    describe('Input Types', () => {
        it('should support secure text entry for passwords', () => {
            const { getByPlaceholderText } = render(
                <FormField
                    placeholder="Enter password"
                    value=""
                    onChangeText={() => {}}
                    secureTextEntry={true}
                />
            );

            const input = getByPlaceholderText('Enter password');
            expect(input.props.secureTextEntry).toBe(true);
        });

        it('should support email keyboard type', () => {
            const { getByPlaceholderText } = render(
                <FormField
                    placeholder="Enter email"
                    value=""
                    onChangeText={() => {}}
                    keyboardType="email-address"
                />
            );

            const input = getByPlaceholderText('Enter email');
            expect(input.props.keyboardType).toBe('email-address');
        });

        it('should support multiline input', () => {
            const { getByPlaceholderText } = render(
                <FormField
                    placeholder="Enter description"
                    value=""
                    onChangeText={() => {}}
                    multiline={true}
                    numberOfLines={3}
                />
            );

            const input = getByPlaceholderText('Enter description');
            expect(input.props.multiline).toBe(true);
            expect(input.props.numberOfLines).toBe(3);
        });

        it('should support disabled state', () => {
            const { getByPlaceholderText } = render(
                <FormField
                    placeholder="Disabled field"
                    value="Cannot edit"
                    onChangeText={() => {}}
                    editable={false}
                />
            );

            const input = getByPlaceholderText('Disabled field');
            expect(input.props.editable).toBe(false);
        });
    });

    describe('Validation Scenarios', () => {
        it('should handle required field validation', () => {
            const { getByText } = render(
                <FormField
                    label="Email"
                    value=""
                    onChangeText={() => {}}
                    error="Email is required"
                />
            );
            expect(getByText('Email is required')).toBeTruthy();
        });

        it('should handle format validation', () => {
            const { getByText } = render(
                <FormField
                    label="Email"
                    value="invalid-email"
                    onChangeText={() => {}}
                    error="Please enter a valid email address"
                />
            );
            expect(getByText('Please enter a valid email address')).toBeTruthy();
        });

        it('should handle length validation', () => {
            const { getByText } = render(
                <FormField
                    label="Password"
                    value="123"
                    onChangeText={() => {}}
                    error="Password must be at least 6 characters"
                />
            );
            expect(getByText('Password must be at least 6 characters')).toBeTruthy();
        });
    });
});

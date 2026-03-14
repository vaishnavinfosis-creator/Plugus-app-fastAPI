import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

/**
 * ErrorDisplay Component
 * 
 * Displays errors in two modes:
 * 1. Banner mode (default): Full-width error banner with icon, message, and actions
 * 2. Field mode: Compact inline error message for form field validation
 * 
 * @param {Object} error - Error object with error_code, message, details, request_id
 * @param {Function} onRetry - Callback for retry action
 * @param {Function} onDismiss - Callback for dismiss action
 * @param {Boolean} showRetry - Whether to show retry button
 * @param {Boolean} fieldMode - Whether to display as field-level error (compact)
 * @param {Object} style - Additional styles
 */
const ErrorDisplay = ({ 
    error, 
    onRetry, 
    onDismiss, 
    showRetry = false,
    fieldMode = false,
    style = {} 
}) => {
    if (!error) return null;

    const getErrorIcon = (errorCode) => {
        switch (errorCode) {
            case 'USER_NOT_FOUND':
                return 'person-outline';
            case 'INVALID_PASSWORD':
                return 'lock-closed-outline';
            case 'ACCOUNT_INACTIVE':
                return 'ban-outline';
            case 'CONNECTION_TIMEOUT':
            case 'SERVICE_UNAVAILABLE':
                return 'wifi-outline';
            case 'RATE_LIMIT_EXCEEDED':
                return 'time-outline';
            case 'VALIDATION_ERROR':
                return 'alert-circle-outline';
            default:
                return 'alert-circle-outline';
        }
    };

    const getErrorColor = (errorCode) => {
        switch (errorCode) {
            case 'USER_NOT_FOUND':
                return '#FF9800'; // Orange for info
            case 'INVALID_PASSWORD':
                return '#F44336'; // Red for error
            case 'ACCOUNT_INACTIVE':
                return '#9C27B0'; // Purple for warning
            case 'CONNECTION_TIMEOUT':
            case 'SERVICE_UNAVAILABLE':
                return '#2196F3'; // Blue for network
            case 'RATE_LIMIT_EXCEEDED':
                return '#FF5722'; // Deep orange for rate limit
            case 'VALIDATION_ERROR':
                return '#F44336'; // Red for validation
            default:
                return '#F44336'; // Red for generic error
        }
    };

    const errorColor = getErrorColor(error.error_code);
    const errorIcon = getErrorIcon(error.error_code);

    // Field-level error display (compact inline)
    if (fieldMode) {
        return (
            <View style={[styles.fieldErrorContainer, style]}>
                <Ionicons 
                    name="alert-circle" 
                    size={14} 
                    color={errorColor} 
                    style={styles.fieldErrorIcon}
                />
                <Text style={[styles.fieldErrorText, { color: errorColor }]}>
                    {error.message || error}
                </Text>
            </View>
        );
    }

    // Banner mode (full error display)
    return (
        <View style={[styles.container, { borderLeftColor: errorColor }, style]}>
            <View style={styles.content}>
                <View style={styles.iconContainer}>
                    <Ionicons 
                        name={errorIcon} 
                        size={24} 
                        color={errorColor} 
                    />
                </View>
                <View style={styles.textContainer}>
                    <Text style={[styles.message, { color: errorColor }]}>
                        {error.message}
                    </Text>
                    {error.details && error.details.email && (
                        <Text style={styles.details}>
                            Email: {error.details.email}
                        </Text>
                    )}
                    {error.request_id && (
                        <Text style={styles.requestId}>
                            ID: {error.request_id.substring(0, 8)}
                        </Text>
                    )}
                </View>
            </View>
            
            <View style={styles.actions}>
                {showRetry && onRetry && (
                    <TouchableOpacity 
                        style={[styles.retryButton, { backgroundColor: errorColor }]} 
                        onPress={onRetry}
                    >
                        <Ionicons name="refresh-outline" size={16} color="#fff" />
                        <Text style={styles.retryText}>Retry</Text>
                    </TouchableOpacity>
                )}
                {onDismiss && (
                    <TouchableOpacity 
                        style={styles.dismissButton} 
                        onPress={onDismiss}
                    >
                        <Ionicons name="close-outline" size={20} color="#666" />
                    </TouchableOpacity>
                )}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    // Banner mode styles
    container: {
        backgroundColor: '#fff',
        borderRadius: 8,
        borderLeftWidth: 4,
        marginVertical: 8,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    content: {
        flexDirection: 'row',
        padding: 16,
        alignItems: 'flex-start',
    },
    iconContainer: {
        marginRight: 12,
        marginTop: 2,
    },
    textContainer: {
        flex: 1,
    },
    message: {
        fontSize: 16,
        fontWeight: '600',
        marginBottom: 4,
    },
    details: {
        fontSize: 14,
        color: '#666',
        marginBottom: 2,
    },
    requestId: {
        fontSize: 12,
        color: '#999',
        fontFamily: 'monospace',
    },
    actions: {
        flexDirection: 'row',
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingHorizontal: 16,
        paddingBottom: 12,
    },
    retryButton: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 16,
        marginRight: 8,
    },
    retryText: {
        color: '#fff',
        fontSize: 14,
        fontWeight: '600',
        marginLeft: 4,
    },
    dismissButton: {
        padding: 4,
    },
    // Field mode styles (compact inline)
    fieldErrorContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 4,
        marginBottom: 8,
    },
    fieldErrorIcon: {
        marginRight: 4,
    },
    fieldErrorText: {
        fontSize: 13,
        flex: 1,
    },
});

export default ErrorDisplay;
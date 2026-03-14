import React from 'react';
import { View, Text, TextInput, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import ErrorDisplay from './ErrorDisplay';

/**
 * FormField Component
 * 
 * A reusable form field component with integrated validation error display.
 * Wraps TextInput with label, icon, and field-level error message support.
 * 
 * @param {String} label - Field label text
 * @param {String} icon - Ionicons icon name
 * @param {String} value - Input value
 * @param {Function} onChangeText - Callback when text changes
 * @param {String|Object} error - Error message (string) or error object
 * @param {Function} onClearError - Callback to clear error when user types
 * @param {String} placeholder - Input placeholder text
 * @param {Boolean} secureTextEntry - Whether to hide input (for passwords)
 * @param {String} keyboardType - Keyboard type (email-address, numeric, etc.)
 * @param {String} autoCapitalize - Auto-capitalization behavior
 * @param {Boolean} multiline - Whether input is multiline
 * @param {Number} numberOfLines - Number of lines for multiline input
 * @param {Boolean} editable - Whether input is editable
 * @param {Object} style - Additional container styles
 * @param {Object} inputStyle - Additional input styles
 */
const FormField = ({
    label,
    icon,
    value,
    onChangeText,
    error,
    onClearError,
    placeholder,
    secureTextEntry = false,
    keyboardType = 'default',
    autoCapitalize = 'sentences',
    multiline = false,
    numberOfLines = 1,
    editable = true,
    style = {},
    inputStyle = {},
    rightIcon,
    onRightIconPress,
}) => {
    const hasError = !!error;
    
    const handleTextChange = (text) => {
        if (onChangeText) {
            onChangeText(text);
        }
        // Clear error when user starts typing
        if (hasError && onClearError) {
            onClearError();
        }
    };

    return (
        <View style={[styles.container, style]}>
            {label && (
                <Text style={styles.label}>{label}</Text>
            )}
            
            <View style={[
                styles.inputContainer,
                hasError && styles.inputContainerError,
                !editable && styles.inputContainerDisabled,
                multiline && styles.inputContainerMultiline,
            ]}>
                {icon && (
                    <Ionicons 
                        name={icon} 
                        size={20} 
                        color={hasError ? '#F44336' : '#666'} 
                        style={styles.inputIcon} 
                    />
                )}
                
                <TextInput
                    style={[
                        styles.input,
                        multiline && styles.inputMultiline,
                        inputStyle,
                    ]}
                    placeholder={placeholder}
                    value={value}
                    onChangeText={handleTextChange}
                    secureTextEntry={secureTextEntry}
                    keyboardType={keyboardType}
                    autoCapitalize={autoCapitalize}
                    placeholderTextColor="#999"
                    multiline={multiline}
                    numberOfLines={numberOfLines}
                    editable={editable}
                />
                
                {rightIcon && (
                    <Ionicons 
                        name={rightIcon} 
                        size={20} 
                        color="#666" 
                        style={styles.rightIcon}
                        onPress={onRightIconPress}
                    />
                )}
            </View>
            
            {hasError && (
                <ErrorDisplay 
                    error={typeof error === 'string' ? { message: error } : error}
                    fieldMode={true}
                />
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        marginBottom: 16,
    },
    label: {
        fontSize: 14,
        fontWeight: '600',
        color: '#333',
        marginBottom: 8,
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
        borderRadius: 12,
        paddingHorizontal: 15,
        borderWidth: 1,
        borderColor: '#eee',
    },
    inputContainerError: {
        borderColor: '#F44336',
        backgroundColor: '#FFF5F5',
    },
    inputContainerDisabled: {
        backgroundColor: '#f9f9f9',
        opacity: 0.6,
    },
    inputContainerMultiline: {
        alignItems: 'flex-start',
        paddingVertical: 12,
    },
    inputIcon: {
        marginRight: 10,
    },
    rightIcon: {
        marginLeft: 10,
    },
    input: {
        flex: 1,
        paddingVertical: 16,
        fontSize: 16,
        color: '#333',
    },
    inputMultiline: {
        paddingVertical: 8,
        minHeight: 80,
        textAlignVertical: 'top',
    },
});

export default FormField;

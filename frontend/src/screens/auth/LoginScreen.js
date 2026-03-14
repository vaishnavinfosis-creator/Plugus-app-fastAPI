import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, Image, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client, { getStructuredError } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import ErrorDisplay from '../../components/ErrorDisplay';
import FormField from '../../components/FormField';

export default function LoginScreen({ navigation }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState(null);
    const [fieldErrors, setFieldErrors] = useState({});
    const { setToken } = useAuthStore();

    const handleLogin = async () => {
        // Clear previous errors
        setError(null);
        setFieldErrors({});

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

        setLoading(true);

        try {
            console.log('Attempting login for:', email.trim());

            // OAuth2 form expects application/x-www-form-urlencoded
            const params = new URLSearchParams();
            params.append('username', email.trim());
            params.append('password', password);

            const res = await client.post('/auth/login', params.toString(), {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                timeout: 10000 // 10 second timeout
            });

            console.log('Login successful, setting token');
            await setToken(res.data.access_token);
        } catch (e) {
            console.error('Login error:', e);
            
            // Use structured error helper
            const structuredError = getStructuredError(e);
            
            // Handle specific error codes with custom messages
            if (structuredError.error_code === 'UNKNOWN_ERROR' && e.response?.status) {
                const status = e.response.status;
                if (status === 404) {
                    structuredError.error_code = 'USER_NOT_FOUND';
                    structuredError.message = 'Email not found. Please register first.';
                    structuredError.details = { email: email.trim() };
                } else if (status === 401) {
                    structuredError.error_code = 'INVALID_PASSWORD';
                    structuredError.message = 'Incorrect password. Please try again.';
                    structuredError.details = { email: email.trim() };
                } else if (status === 400) {
                    structuredError.error_code = 'ACCOUNT_INACTIVE';
                    structuredError.message = 'Your account has been deactivated. Please contact support.';
                    structuredError.details = { email: email.trim() };
                }
            }
            
            setError(structuredError);
        } finally {
            setLoading(false);
        }
    };

    const handleRetry = () => {
        setError(null);
        handleLogin();
    };

    const handleDismissError = () => {
        setError(null);
    };

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <View style={styles.logoSection}>
                    <Image
                        source={require('../../../assets/logo.png')}
                        style={styles.logo}
                        resizeMode="contain"
                    />
                    <Text style={styles.appName}>Plugus</Text>
                    <Text style={styles.tagline}>Service at your fingertips</Text>
                </View>

                <View style={styles.formSection}>
                    <Text style={styles.title}>Welcome Back</Text>
                    <Text style={styles.subtitle}>Sign in to continue</Text>

                    {error && (
                        <ErrorDisplay
                            error={error}
                            onRetry={['CONNECTION_TIMEOUT', 'SERVICE_UNAVAILABLE'].includes(error.error_code) ? handleRetry : null}
                            onDismiss={handleDismissError}
                            showRetry={['CONNECTION_TIMEOUT', 'SERVICE_UNAVAILABLE'].includes(error.error_code)}
                            style={styles.errorContainer}
                        />
                    )}

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

                    <TouchableOpacity
                        style={[styles.loginButton, loading && styles.loginButtonDisabled]}
                        onPress={handleLogin}
                        disabled={loading}
                    >
                        <Text style={styles.loginButtonText}>
                            {loading ? 'Signing in...' : 'Sign In'}
                        </Text>
                    </TouchableOpacity>

                    <View style={styles.divider}>
                        <View style={styles.dividerLine} />
                        <Text style={styles.dividerText}>or</Text>
                        <View style={styles.dividerLine} />
                    </View>

                    <TouchableOpacity
                        style={styles.registerButton}
                        onPress={() => navigation.navigate('Register')}
                    >
                        <Text style={styles.registerButtonText}>Create New Account</Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#fff' },
    scrollContent: { flexGrow: 1 },
    logoSection: {
        alignItems: 'center',
        paddingTop: 60,
        paddingBottom: 40
    },
    logo: { width: 100, height: 100, marginBottom: 10 },
    appName: { fontSize: 32, fontWeight: 'bold', color: '#1E88E5' },
    tagline: { fontSize: 14, color: '#666', marginTop: 5 },
    formSection: { flex: 1, padding: 30 },
    title: { fontSize: 26, fontWeight: 'bold', color: '#333', marginBottom: 8 },
    subtitle: { fontSize: 16, color: '#666', marginBottom: 30 },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
        borderRadius: 12,
        paddingHorizontal: 15,
        marginBottom: 15,
        borderWidth: 1,
        borderColor: '#eee'
    },
    inputIcon: { marginRight: 10 },
    input: { flex: 1, paddingVertical: 16, fontSize: 16, color: '#333' },
    loginButton: {
        backgroundColor: '#1E88E5',
        padding: 18,
        borderRadius: 12,
        alignItems: 'center',
        marginTop: 10
    },
    loginButtonDisabled: { backgroundColor: '#90CAF9' },
    loginButtonText: { color: '#fff', fontSize: 18, fontWeight: '600' },
    divider: { flexDirection: 'row', alignItems: 'center', marginVertical: 25 },
    dividerLine: { flex: 1, height: 1, backgroundColor: '#eee' },
    dividerText: { marginHorizontal: 15, color: '#999' },
    registerButton: {
        padding: 18,
        borderRadius: 12,
        alignItems: 'center',
        borderWidth: 2,
        borderColor: '#1E88E5'
    },
    registerButtonText: { color: '#1E88E5', fontSize: 16, fontWeight: '600' },
    errorContainer: {
        marginBottom: 20,
    },
});

import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, Image, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import { useAuthStore } from '../../store/authStore';

export default function LoginScreen({ navigation }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const { setToken } = useAuthStore();

    const handleLogin = async () => {
        if (!email.trim() || !password) {
            Alert.alert('Error', 'Please enter email and password');
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
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            console.log('Login successful, setting token');
            await setToken(res.data.access_token);
        } catch (e) {
            console.error('Login error:', e);
            const status = e.response?.status;
            const detail = e.response?.data?.detail;

            if (status === 404) {
                Alert.alert('User Not Found', 'This email is not registered. Please register first.');
            } else if (status === 401) {
                Alert.alert('Login Failed', 'Incorrect password. Please try again.');
            } else if (e.code === 'ERR_NETWORK') {
                Alert.alert('Network Error', 'Cannot connect to server. Make sure backend is running on port 8000.');
            } else {
                Alert.alert('Error', detail || e.message || 'Login failed. Please try again.');
            }
        } finally {
            setLoading(false);
        }
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

                    <View style={styles.inputContainer}>
                        <Ionicons name="mail-outline" size={20} color="#666" style={styles.inputIcon} />
                        <TextInput
                            style={styles.input}
                            placeholder="Email"
                            value={email}
                            onChangeText={setEmail}
                            keyboardType="email-address"
                            autoCapitalize="none"
                            placeholderTextColor="#999"
                        />
                    </View>

                    <View style={styles.inputContainer}>
                        <Ionicons name="lock-closed-outline" size={20} color="#666" style={styles.inputIcon} />
                        <TextInput
                            style={styles.input}
                            placeholder="Password"
                            value={password}
                            onChangeText={setPassword}
                            secureTextEntry={!showPassword}
                            placeholderTextColor="#999"
                        />
                        <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                            <Ionicons
                                name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                                size={20}
                                color="#666"
                            />
                        </TouchableOpacity>
                    </View>

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
    registerButtonText: { color: '#1E88E5', fontSize: 16, fontWeight: '600' }
});

import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, Image, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import { useAuthStore } from '../../store/authStore';

export default function RegisterScreen({ navigation }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [role, setRole] = useState('CUSTOMER');
    const [businessName, setBusinessName] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [regions, setRegions] = useState([]);
    const [selectedRegion, setSelectedRegion] = useState(null);
    const [loadingRegions, setLoadingRegions] = useState(false);
    const { setToken } = useAuthStore();

    useEffect(() => {
        if (role === 'VENDOR') {
            fetchRegions();
        }
    }, [role]);

    const fetchRegions = async () => {
        setLoadingRegions(true);
        try {
            const res = await client.get('/auth/regions');
            setRegions(res.data || []);
        } catch (e) {
            console.error('Failed to fetch regions:', e);
            Alert.alert('Error', 'Failed to load regions. Please try again.');
        } finally {
            setLoadingRegions(false);
        }
    };

    const handleRegister = async () => {
        if (!email.trim() || !password) {
            Alert.alert('Error', 'Please fill all required fields');
            return;
        }
        if (password !== confirmPassword) {
            Alert.alert('Error', 'Passwords do not match');
            return;
        }
        if (password.length < 6) {
            Alert.alert('Error', 'Password must be at least 6 characters');
            return;
        }
        if (role === 'VENDOR') {
            if (!businessName.trim()) {
                Alert.alert('Error', 'Please enter business name');
                return;
            }
            if (!selectedRegion) {
                Alert.alert('Error', 'Please select a region');
                return;
            }
        }

        setLoading(true);
        try {
            const payload = {
                email: email.trim(),
                password,
                full_name: fullName.trim() || null,
                role
            };

            if (role === 'VENDOR') {
                payload.business_name = businessName.trim();
                payload.region_id = selectedRegion;
            }

            const res = await client.post('/auth/register', payload);

            // Auto-login after registration
            const formData = new FormData();
            formData.append('username', email.trim());
            formData.append('password', password);

            const loginRes = await client.post('/auth/login', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            await setToken(loginRes.data.access_token);
        } catch (e) {
            const detail = e.response?.data?.detail;
            Alert.alert('Registration Failed', detail || 'Something went wrong');
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
                <View style={styles.header}>
                    <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                        <Ionicons name="arrow-back" size={24} color="#333" />
                    </TouchableOpacity>
                    <Image
                        source={require('../../../assets/logo.png')}
                        style={styles.logo}
                        resizeMode="contain"
                    />
                </View>

                <View style={styles.formSection}>
                    <Text style={styles.title}>Create Account</Text>
                    <Text style={styles.subtitle}>Sign up to get started</Text>

                    {/* Role Selection */}
                    <View style={styles.roleContainer}>
                        <TouchableOpacity
                            style={[styles.roleButton, role === 'CUSTOMER' && styles.roleButtonActive]}
                            onPress={() => setRole('CUSTOMER')}
                        >
                            <Ionicons
                                name="person-outline"
                                size={20}
                                color={role === 'CUSTOMER' ? '#fff' : '#1E88E5'}
                            />
                            <Text style={[styles.roleText, role === 'CUSTOMER' && styles.roleTextActive]}>
                                Customer
                            </Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={[styles.roleButton, role === 'VENDOR' && styles.roleButtonActive]}
                            onPress={() => setRole('VENDOR')}
                        >
                            <Ionicons
                                name="storefront-outline"
                                size={20}
                                color={role === 'VENDOR' ? '#fff' : '#1E88E5'}
                            />
                            <Text style={[styles.roleText, role === 'VENDOR' && styles.roleTextActive]}>
                                Vendor
                            </Text>
                        </TouchableOpacity>
                    </View>

                    <View style={styles.inputContainer}>
                        <Ionicons name="mail-outline" size={20} color="#666" style={styles.inputIcon} />
                        <TextInput
                            style={styles.input}
                            placeholder="Email *"
                            value={email}
                            onChangeText={setEmail}
                            keyboardType="email-address"
                            autoCapitalize="none"
                            placeholderTextColor="#999"
                        />
                    </View>

                    <View style={styles.inputContainer}>
                        <Ionicons name="person-outline" size={20} color="#666" style={styles.inputIcon} />
                        <TextInput
                            style={styles.input}
                            placeholder="Full Name"
                            value={fullName}
                            onChangeText={setFullName}
                            placeholderTextColor="#999"
                        />
                    </View>

                    {role === 'VENDOR' && (
                        <>
                            <View style={styles.inputContainer}>
                                <Ionicons name="storefront-outline" size={20} color="#666" style={styles.inputIcon} />
                                <TextInput
                                    style={styles.input}
                                    placeholder="Business Name *"
                                    value={businessName}
                                    onChangeText={setBusinessName}
                                    placeholderTextColor="#999"
                                />
                            </View>

                            <View style={styles.regionSection}>
                                <Text style={styles.regionLabel}>Select Region *</Text>
                                {loadingRegions ? (
                                    <ActivityIndicator size="small" color="#1E88E5" style={styles.regionLoader} />
                                ) : regions.length === 0 ? (
                                    <Text style={styles.noRegionsText}>No regions available</Text>
                                ) : (
                                    <View style={styles.regionsList}>
                                        {regions.map(region => (
                                            <TouchableOpacity
                                                key={region.id}
                                                style={[
                                                    styles.regionChip,
                                                    selectedRegion === region.id && styles.regionChipSelected
                                                ]}
                                                onPress={() => setSelectedRegion(region.id)}
                                            >
                                                <Text style={[
                                                    styles.regionChipText,
                                                    selectedRegion === region.id && styles.regionChipTextSelected
                                                ]}>
                                                    {region.name}
                                                </Text>
                                            </TouchableOpacity>
                                        ))}
                                    </View>
                                )}
                            </View>
                        </>
                    )}

                    <View style={styles.inputContainer}>
                        <Ionicons name="lock-closed-outline" size={20} color="#666" style={styles.inputIcon} />
                        <TextInput
                            style={styles.input}
                            placeholder="Password *"
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

                    <View style={styles.inputContainer}>
                        <Ionicons name="lock-closed-outline" size={20} color="#666" style={styles.inputIcon} />
                        <TextInput
                            style={styles.input}
                            placeholder="Confirm Password *"
                            value={confirmPassword}
                            onChangeText={setConfirmPassword}
                            secureTextEntry={!showPassword}
                            placeholderTextColor="#999"
                        />
                    </View>

                    {role === 'VENDOR' && (
                        <View style={styles.noteContainer}>
                            <Ionicons name="information-circle" size={18} color="#FF9800" />
                            <Text style={styles.noteText}>
                                Vendor accounts require admin approval before activation.
                            </Text>
                        </View>
                    )}

                    <TouchableOpacity
                        style={[styles.registerButton, loading && styles.registerButtonDisabled]}
                        onPress={handleRegister}
                        disabled={loading}
                    >
                        <Text style={styles.registerButtonText}>
                            {loading ? 'Creating Account...' : 'Create Account'}
                        </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.loginLink}
                        onPress={() => navigation.goBack()}
                    >
                        <Text style={styles.loginLinkText}>
                            Already have an account? <Text style={styles.loginLinkBold}>Sign In</Text>
                        </Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#fff' },
    scrollContent: { flexGrow: 1 },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        paddingTop: 50
    },
    backButton: { marginRight: 15 },
    logo: { width: 50, height: 50 },
    formSection: { flex: 1, padding: 30, paddingTop: 10 },
    title: { fontSize: 26, fontWeight: 'bold', color: '#333', marginBottom: 8 },
    subtitle: { fontSize: 16, color: '#666', marginBottom: 25 },
    roleContainer: { flexDirection: 'row', gap: 15, marginBottom: 20 },
    roleButton: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 14,
        borderRadius: 12,
        borderWidth: 2,
        borderColor: '#1E88E5'
    },
    roleButtonActive: { backgroundColor: '#1E88E5' },
    roleText: { marginLeft: 8, fontWeight: '600', color: '#1E88E5' },
    roleTextActive: { color: '#fff' },
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
    noteContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFF3E0',
        padding: 12,
        borderRadius: 10,
        marginBottom: 15
    },
    noteText: { marginLeft: 8, color: '#E65100', fontSize: 13, flex: 1 },
    registerButton: {
        backgroundColor: '#1E88E5',
        padding: 18,
        borderRadius: 12,
        alignItems: 'center',
        marginTop: 10
    },
    registerButtonDisabled: { backgroundColor: '#90CAF9' },
    registerButtonText: { color: '#fff', fontSize: 18, fontWeight: '600' },
    loginLink: { alignItems: 'center', marginTop: 25 },
    loginLinkText: { color: '#666', fontSize: 15 },
    loginLinkBold: { color: '#1E88E5', fontWeight: '600' },
    regionSection: { marginBottom: 15 },
    regionLabel: { fontSize: 15, fontWeight: '600', color: '#333', marginBottom: 10 },
    regionLoader: { marginVertical: 10 },
    noRegionsText: { color: '#999', fontSize: 14, textAlign: 'center', paddingVertical: 10 },
    regionsList: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
    regionChip: {
        paddingHorizontal: 16,
        paddingVertical: 10,
        borderRadius: 20,
        borderWidth: 1.5,
        borderColor: '#1E88E5',
        backgroundColor: '#fff'
    },
    regionChipSelected: { backgroundColor: '#1E88E5' },
    regionChipText: { fontSize: 14, fontWeight: '500', color: '#1E88E5' },
    regionChipTextSelected: { color: '#fff' }
});

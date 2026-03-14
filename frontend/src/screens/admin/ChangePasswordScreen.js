import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, Image, Platform, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import FormField from '../../components/FormField';
import ErrorDisplay from '../../components/ErrorDisplay';
import { apiClient } from '../../api/client';

export default function ChangePasswordScreen({ navigation }) {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    const handleChangePassword = async () => {
        setError(null);
        setSuccess(false);

        // Validation
        if (!currentPassword || !newPassword || !confirmPassword) {
            setError({ message: 'All fields are required' });
            return;
        }

        if (newPassword.length < 6) {
            setError({ message: 'New password must be at least 6 characters' });
            return;
        }

        if (newPassword !== confirmPassword) {
            setError({ message: 'New passwords do not match' });
            return;
        }

        if (currentPassword === newPassword) {
            setError({ message: 'New password must be different from current password' });
            return;
        }

        setLoading(true);

        try {
            await apiClient.post('/auth/change-password', {
                current_password: currentPassword,
                new_password: newPassword
            });

            setSuccess(true);
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');

            if (Platform.OS === 'web') {
                alert('Password changed successfully!');
            } else {
                Alert.alert('Success', 'Password changed successfully!');
            }

            // Navigate back after a short delay
            setTimeout(() => {
                navigation.goBack();
            }, 1500);

        } catch (err) {
            console.error('Password change error:', err);
            setError(err.response?.data || { message: 'Failed to change password' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#333" />
                </TouchableOpacity>
                <Image
                    source={require('../../../assets/logo.png')}
                    style={styles.logo}
                    resizeMode="contain"
                />
                <Text style={styles.title}>Change Password</Text>
            </View>

            <View style={styles.content}>
                <View style={styles.form}>
                    <Text style={styles.description}>
                        Enter your current password and choose a new password
                    </Text>

                    {error && <ErrorDisplay error={error} />}

                    {success && (
                        <View style={styles.successMessage}>
                            <Ionicons name="checkmark-circle" size={20} color="#4CAF50" />
                            <Text style={styles.successText}>Password changed successfully!</Text>
                        </View>
                    )}

                    <FormField
                        label="Current Password"
                        value={currentPassword}
                        onChangeText={setCurrentPassword}
                        placeholder="Enter current password"
                        secureTextEntry
                        icon="lock-closed-outline"
                    />

                    <FormField
                        label="New Password"
                        value={newPassword}
                        onChangeText={setNewPassword}
                        placeholder="Enter new password (min 6 characters)"
                        secureTextEntry
                        icon="key-outline"
                    />

                    <FormField
                        label="Confirm New Password"
                        value={confirmPassword}
                        onChangeText={setConfirmPassword}
                        placeholder="Re-enter new password"
                        secureTextEntry
                        icon="key-outline"
                    />

                    <TouchableOpacity
                        style={[styles.button, loading && styles.buttonDisabled]}
                        onPress={handleChangePassword}
                        disabled={loading}
                    >
                        {loading ? (
                            <ActivityIndicator color="#fff" />
                        ) : (
                            <>
                                <Ionicons name="shield-checkmark" size={20} color="#fff" />
                                <Text style={styles.buttonText}>Change Password</Text>
                            </>
                        )}
                    </TouchableOpacity>

                    <View style={styles.infoBox}>
                        <Ionicons name="information-circle-outline" size={20} color="#1E88E5" />
                        <Text style={styles.infoText}>
                            Password must be at least 6 characters long
                        </Text>
                    </View>
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    backButton: { marginRight: 12 },
    logo: { width: 40, height: 40, marginRight: 12 },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    content: { flex: 1, padding: 15 },
    form: { backgroundColor: '#fff', borderRadius: 12, padding: 20 },
    description: {
        fontSize: 14,
        color: '#666',
        marginBottom: 20,
        textAlign: 'center'
    },
    button: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#1E88E5',
        padding: 15,
        borderRadius: 12,
        marginTop: 10
    },
    buttonDisabled: { opacity: 0.6 },
    buttonText: {
        color: '#fff',
        fontWeight: '600',
        marginLeft: 8,
        fontSize: 16
    },
    successMessage: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#E8F5E9',
        padding: 12,
        borderRadius: 8,
        marginBottom: 15
    },
    successText: {
        color: '#4CAF50',
        marginLeft: 8,
        fontWeight: '500'
    },
    infoBox: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#E3F2FD',
        padding: 12,
        borderRadius: 8,
        marginTop: 15
    },
    infoText: {
        color: '#1E88E5',
        marginLeft: 8,
        fontSize: 13,
        flex: 1
    }
});

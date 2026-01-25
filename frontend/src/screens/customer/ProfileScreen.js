import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, TextInput, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';

export default function ProfileScreen({ navigation }) {
    const { user, logout } = useAuthStore();
    const [isEditing, setIsEditing] = useState(false);
    const [fullName, setFullName] = useState(user?.full_name || '');

    const handleLogout = () => {
        Alert.alert(
            'Logout',
            'Are you sure you want to logout?',
            [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Logout', style: 'destructive', onPress: () => logout() }
            ]
        );
    };

    const handleSave = async () => {
        // TODO: Implement profile update API
        setIsEditing(false);
        Alert.alert('Success', 'Profile updated');
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Image
                    source={require('../../../assets/logo.png')}
                    style={styles.logo}
                    resizeMode="contain"
                />
                <Text style={styles.title}>Profile</Text>
            </View>

            <ScrollView style={styles.content}>
                {/* Avatar */}
                <View style={styles.avatarSection}>
                    <View style={styles.avatar}>
                        <Ionicons name="person" size={50} color="#1E88E5" />
                    </View>
                    <Text style={styles.email}>{user?.email}</Text>
                    <View style={styles.roleBadge}>
                        <Text style={styles.roleText}>{user?.role}</Text>
                    </View>
                </View>

                {/* Info Cards */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardTitle}>Personal Information</Text>
                        <TouchableOpacity onPress={() => setIsEditing(!isEditing)}>
                            <Ionicons
                                name={isEditing ? 'close' : 'create-outline'}
                                size={22}
                                color="#1E88E5"
                            />
                        </TouchableOpacity>
                    </View>

                    <View style={styles.infoRow}>
                        <Text style={styles.infoLabel}>Email</Text>
                        <Text style={styles.infoValue}>{user?.email}</Text>
                    </View>

                    <View style={styles.infoRow}>
                        <Text style={styles.infoLabel}>Full Name</Text>
                        {isEditing ? (
                            <TextInput
                                style={styles.input}
                                value={fullName}
                                onChangeText={setFullName}
                                placeholder="Enter full name"
                            />
                        ) : (
                            <Text style={styles.infoValue}>{user?.full_name || 'Not set'}</Text>
                        )}
                    </View>

                    {isEditing && (
                        <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
                            <Text style={styles.saveButtonText}>Save Changes</Text>
                        </TouchableOpacity>
                    )}
                </View>

                {/* Menu Items */}
                <View style={styles.menuCard}>
                    <TouchableOpacity style={styles.menuItem}>
                        <Ionicons name="location-outline" size={22} color="#666" />
                        <Text style={styles.menuText}>Manage Addresses</Text>
                        <Ionicons name="chevron-forward" size={20} color="#ccc" />
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.menuItem}>
                        <Ionicons name="call-outline" size={22} color="#666" />
                        <Text style={styles.menuText}>Manage Phone Numbers</Text>
                        <Ionicons name="chevron-forward" size={20} color="#ccc" />
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.menuItem}>
                        <Ionicons name="notifications-outline" size={22} color="#666" />
                        <Text style={styles.menuText}>Notifications</Text>
                        <Ionicons name="chevron-forward" size={20} color="#ccc" />
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.menuItem}>
                        <Ionicons name="help-circle-outline" size={22} color="#666" />
                        <Text style={styles.menuText}>Help & Support</Text>
                        <Ionicons name="chevron-forward" size={20} color="#ccc" />
                    </TouchableOpacity>
                </View>

                {/* Logout */}
                <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
                    <Ionicons name="log-out-outline" size={22} color="#E53935" />
                    <Text style={styles.logoutText}>Logout</Text>
                </TouchableOpacity>

                <Text style={styles.version}>Version 2.0.0</Text>
            </ScrollView>
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
    logo: { width: 40, height: 40, marginRight: 12 },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    content: { flex: 1 },
    avatarSection: {
        alignItems: 'center',
        paddingVertical: 30,
        backgroundColor: '#fff',
        marginBottom: 15
    },
    avatar: {
        width: 100,
        height: 100,
        borderRadius: 50,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 15
    },
    email: { fontSize: 16, color: '#333', fontWeight: '500' },
    roleBadge: {
        marginTop: 8,
        backgroundColor: '#E3F2FD',
        paddingHorizontal: 16,
        paddingVertical: 6,
        borderRadius: 20
    },
    roleText: { color: '#1E88E5', fontWeight: '600', fontSize: 12 },
    card: {
        backgroundColor: '#fff',
        marginHorizontal: 15,
        marginBottom: 15,
        borderRadius: 12,
        padding: 15,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 15
    },
    cardTitle: { fontSize: 16, fontWeight: '600', color: '#333' },
    infoRow: { marginBottom: 15 },
    infoLabel: { fontSize: 12, color: '#999', marginBottom: 4 },
    infoValue: { fontSize: 16, color: '#333' },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 10,
        fontSize: 16
    },
    saveButton: {
        backgroundColor: '#1E88E5',
        padding: 12,
        borderRadius: 8,
        alignItems: 'center',
        marginTop: 10
    },
    saveButtonText: { color: '#fff', fontWeight: '600' },
    menuCard: {
        backgroundColor: '#fff',
        marginHorizontal: 15,
        marginBottom: 15,
        borderRadius: 12,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2
    },
    menuItem: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 15,
        borderBottomWidth: 1,
        borderBottomColor: '#f0f0f0'
    },
    menuText: { flex: 1, marginLeft: 12, fontSize: 15, color: '#333' },
    logoutButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#fff',
        marginHorizontal: 15,
        marginBottom: 15,
        padding: 15,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#FFCDD2'
    },
    logoutText: { color: '#E53935', fontWeight: '600', marginLeft: 8, fontSize: 16 },
    version: { textAlign: 'center', color: '#999', marginBottom: 30 }
});

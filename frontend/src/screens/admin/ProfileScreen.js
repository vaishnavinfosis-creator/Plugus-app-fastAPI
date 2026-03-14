import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, Image, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';

export default function ProfileScreen({ navigation }) {
    const { user, logout } = useAuthStore();

    const handleLogout = () => {
        if (Platform.OS === 'web') {
            if (window.confirm('Are you sure you want to logout?')) {
                logout();
            }
        } else {
            Alert.alert('Logout', 'Are you sure?', [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Logout', style: 'destructive', onPress: logout }
            ]);
        }
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

            <View style={styles.content}>
                <View style={styles.avatarSection}>
                    <View style={styles.avatar}>
                        <Ionicons name="shield" size={50} color="#1E88E5" />
                    </View>
                    <Text style={styles.email}>{user?.email}</Text>
                    <View style={styles.roleBadge}>
                        <Text style={styles.roleText}>
                            {user?.role === 'SUPER_ADMIN' ? 'SUPER ADMIN' : 'REGIONAL ADMIN'}
                        </Text>
                    </View>
                </View>

                <TouchableOpacity 
                    style={styles.changePasswordButton} 
                    onPress={() => navigation.navigate('ChangePassword')}
                >
                    <Ionicons name="key-outline" size={22} color="#1E88E5" />
                    <Text style={styles.changePasswordText}>Change Password</Text>
                    <Ionicons name="chevron-forward" size={20} color="#999" />
                </TouchableOpacity>

                <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
                    <Ionicons name="log-out-outline" size={22} color="#E53935" />
                    <Text style={styles.logoutText}>Logout</Text>
                </TouchableOpacity>
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
    logo: { width: 40, height: 40, marginRight: 12 },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    content: { flex: 1, padding: 15 },
    avatarSection: { alignItems: 'center', paddingVertical: 40 },
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
    changePasswordButton: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#E3F2FD',
        marginBottom: 10
    },
    changePasswordText: { 
        color: '#1E88E5', 
        fontWeight: '600', 
        marginLeft: 8, 
        fontSize: 16,
        flex: 1
    },
    logoutButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#FFCDD2'
    },
    logoutText: { color: '#E53935', fontWeight: '600', marginLeft: 8, fontSize: 16 }
});

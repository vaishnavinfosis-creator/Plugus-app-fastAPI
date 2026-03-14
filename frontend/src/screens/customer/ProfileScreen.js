import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, TextInput, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';
import client from '../../api/client';

export default function ProfileScreen({ navigation }) {
    const { user, logout, setUser } = useAuthStore();
    const [isEditing, setIsEditing] = useState(false);
    const [fullName, setFullName] = useState('');
    const [loading, setLoading] = useState(false);
    const [addresses, setAddresses] = useState([]);
    const [phoneNumbers, setPhoneNumbers] = useState([]);

    useEffect(() => {
        fetchProfile();
        fetchAddresses();
        fetchPhoneNumbers();
    }, []);

    const fetchProfile = async () => {
        try {
            const response = await client.get('/customer/profile');
            setFullName(response.data.full_name || '');
            setUser(response.data);
        } catch (error) {
            console.error('Error fetching profile:', error);
        }
    };

    const fetchAddresses = async () => {
        try {
            const response = await client.get('/customer/addresses');
            setAddresses(response.data);
        } catch (error) {
            console.error('Error fetching addresses:', error);
        }
    };

    const fetchPhoneNumbers = async () => {
        try {
            const response = await client.get('/customer/phones');
            setPhoneNumbers(response.data);
        } catch (error) {
            console.error('Error fetching phone numbers:', error);
        }
    };

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
        if (!fullName.trim()) {
            Alert.alert('Error', 'Please enter your full name');
            return;
        }

        setLoading(true);
        try {
            const response = await client.put('/customer/profile', null, {
                params: { full_name: fullName }
            });
            
            // Update user in auth store
            if (response.data.profile) {
                setUser(response.data.profile);
            }
            
            setIsEditing(false);
            Alert.alert('Success', 'Profile updated successfully');
        } catch (error) {
            console.error('Error updating profile:', error);
            Alert.alert('Error', error.response?.data?.detail || 'Failed to update profile');
        } finally {
            setLoading(false);
        }
    };

    const handleAddAddress = () => {
        if (addresses.length >= 2) {
            Alert.alert('Limit Reached', 'You can only have up to 2 addresses');
            return;
        }
        navigation.navigate('AddAddress', { onSuccess: fetchAddresses });
    };

    const handleEditAddress = (address) => {
        navigation.navigate('EditAddress', { address, onSuccess: fetchAddresses });
    };

    const handleDeleteAddress = (addressId) => {
        Alert.alert(
            'Delete Address',
            'Are you sure you want to delete this address?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Delete',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await client.delete(`/customer/addresses/${addressId}`);
                            Alert.alert('Success', 'Address deleted successfully');
                            fetchAddresses();
                        } catch (error) {
                            console.error('Error deleting address:', error);
                            Alert.alert('Error', error.response?.data?.detail || 'Failed to delete address');
                        }
                    }
                }
            ]
        );
    };

    const handleAddPhone = () => {
        if (phoneNumbers.length >= 2) {
            Alert.alert('Limit Reached', 'You can only have up to 2 phone numbers');
            return;
        }
        navigation.navigate('AddPhone', { onSuccess: fetchPhoneNumbers });
    };

    const handleEditPhone = (phone) => {
        navigation.navigate('EditPhone', { phone, onSuccess: fetchPhoneNumbers });
    };

    const handleDeletePhone = (phoneId) => {
        Alert.alert(
            'Delete Phone Number',
            'Are you sure you want to delete this phone number?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Delete',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await client.delete(`/customer/phones/${phoneId}`);
                            Alert.alert('Success', 'Phone number deleted successfully');
                            fetchPhoneNumbers();
                        } catch (error) {
                            console.error('Error deleting phone:', error);
                            Alert.alert('Error', error.response?.data?.detail || 'Failed to delete phone number');
                        }
                    }
                }
            ]
        );
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
                            <Text style={styles.infoValue}>{fullName || 'Not set'}</Text>
                        )}
                    </View>

                    {isEditing && (
                        <TouchableOpacity 
                            style={[styles.saveButton, loading && styles.saveButtonDisabled]} 
                            onPress={handleSave}
                            disabled={loading}
                        >
                            <Text style={styles.saveButtonText}>
                                {loading ? 'Saving...' : 'Save Changes'}
                            </Text>
                        </TouchableOpacity>
                    )}
                </View>

                {/* Addresses Section */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardTitle}>Addresses</Text>
                        {addresses.length < 2 && (
                            <TouchableOpacity onPress={handleAddAddress}>
                                <Ionicons name="add-circle" size={24} color="#1E88E5" />
                            </TouchableOpacity>
                        )}
                    </View>

                    {addresses.length === 0 ? (
                        <Text style={styles.emptyText}>No addresses added yet</Text>
                    ) : (
                        addresses.map((address) => (
                            <View key={address.id} style={styles.itemRow}>
                                <View style={styles.itemContent}>
                                    <Text style={styles.itemLabel}>{address.label}</Text>
                                    <Text style={styles.itemValue}>{address.address_text}</Text>
                                    {address.is_default && (
                                        <View style={styles.defaultBadge}>
                                            <Text style={styles.defaultText}>Default</Text>
                                        </View>
                                    )}
                                </View>
                                <View style={styles.itemActions}>
                                    <TouchableOpacity 
                                        onPress={() => handleEditAddress(address)}
                                        style={styles.actionButton}
                                    >
                                        <Ionicons name="create-outline" size={20} color="#1E88E5" />
                                    </TouchableOpacity>
                                    <TouchableOpacity 
                                        onPress={() => handleDeleteAddress(address.id)}
                                        style={styles.actionButton}
                                    >
                                        <Ionicons name="trash-outline" size={20} color="#E53935" />
                                    </TouchableOpacity>
                                </View>
                            </View>
                        ))
                    )}
                </View>

                {/* Phone Numbers Section */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardTitle}>Phone Numbers</Text>
                        {phoneNumbers.length < 2 && (
                            <TouchableOpacity onPress={handleAddPhone}>
                                <Ionicons name="add-circle" size={24} color="#1E88E5" />
                            </TouchableOpacity>
                        )}
                    </View>

                    {phoneNumbers.length === 0 ? (
                        <Text style={styles.emptyText}>No phone numbers added yet</Text>
                    ) : (
                        phoneNumbers.map((phone) => (
                            <View key={phone.id} style={styles.itemRow}>
                                <View style={styles.itemContent}>
                                    <Text style={styles.itemValue}>{phone.number}</Text>
                                    {phone.is_default && (
                                        <View style={styles.defaultBadge}>
                                            <Text style={styles.defaultText}>Default</Text>
                                        </View>
                                    )}
                                </View>
                                <View style={styles.itemActions}>
                                    <TouchableOpacity 
                                        onPress={() => handleEditPhone(phone)}
                                        style={styles.actionButton}
                                    >
                                        <Ionicons name="create-outline" size={20} color="#1E88E5" />
                                    </TouchableOpacity>
                                    <TouchableOpacity 
                                        onPress={() => handleDeletePhone(phone.id)}
                                        style={styles.actionButton}
                                    >
                                        <Ionicons name="trash-outline" size={20} color="#E53935" />
                                    </TouchableOpacity>
                                </View>
                            </View>
                        ))
                    )}
                </View>

                {/* Menu Items */}
                <View style={styles.menuCard}>
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
    saveButtonDisabled: {
        backgroundColor: '#90CAF9'
    },
    saveButtonText: { color: '#fff', fontWeight: '600' },
    itemRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: '#f0f0f0'
    },
    itemContent: {
        flex: 1,
        marginRight: 10
    },
    itemLabel: {
        fontSize: 14,
        fontWeight: '600',
        color: '#333',
        marginBottom: 4
    },
    itemValue: {
        fontSize: 14,
        color: '#666'
    },
    itemActions: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    actionButton: {
        padding: 8,
        marginLeft: 4
    },
    defaultBadge: {
        marginTop: 4,
        backgroundColor: '#E3F2FD',
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 4,
        alignSelf: 'flex-start'
    },
    defaultText: {
        fontSize: 10,
        color: '#1E88E5',
        fontWeight: '600'
    },
    emptyText: {
        fontSize: 14,
        color: '#999',
        fontStyle: 'italic',
        textAlign: 'center',
        paddingVertical: 10
    },
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

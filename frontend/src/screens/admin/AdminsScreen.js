import React, { useEffect, useState } from 'react';
import {
    View, Text, StyleSheet, FlatList, TouchableOpacity,
    Modal, TextInput, Alert, ActivityIndicator
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import { useAuthStore } from '../../store/authStore';

export default function AdminsScreen() {
    const [admins, setAdmins] = useState([]);
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalVisible, setModalVisible] = useState(false);

    // Form state
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [selectedRegion, setSelectedRegion] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [adminsRes, regionsRes] = await Promise.all([
                client.get('/admin/admins'),
                client.get('/admin/regions')
            ]);
            setAdmins(adminsRes.data);
            setRegions(regionsRes.data);
        } catch (e) {
            console.log('Error fetching admins:', e);
            Alert.alert('Error', 'Failed to load data');
        } finally {
            setLoading(false);
        }
    };

    const handleAddAdmin = async () => {
        if (!email || !password || !selectedRegion) {
            Alert.alert('Error', 'Please fill all fields');
            return;
        }

        try {
            setSubmitting(true);
            await client.post('/admin/admins', {
                admin_in: {
                    email,
                    password,
                    role: 'REGIONAL_ADMIN'
                },
                region_id: selectedRegion
            });

            setModalVisible(false);
            resetForm();
            fetchData();
            Alert.alert('Success', 'Regional Admin created');
        } catch (e) {
            console.log('Error adding admin:', e);
            Alert.alert('Error', e.response?.data?.detail || 'Failed to create admin');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteAdmin = async (id) => {
        Alert.alert(
            'Confirm Delete',
            'Are you sure you want to remove this admin?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Delete',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await client.delete(`/admin/admins/${id}`);
                            fetchData();
                        } catch (e) {
                            Alert.alert('Error', 'Failed to delete admin');
                        }
                    }
                }
            ]
        );
    };

    const resetForm = () => {
        setEmail('');
        setPassword('');
        setSelectedRegion(null);
    };

    const renderAdminItem = ({ item }) => {
        // Find region for this admin
        const region = regions.find(r => r.admin_id === item.id);

        return (
            <View style={styles.card}>
                <View style={styles.cardContent}>
                    <View style={styles.avatar}>
                        <Text style={styles.avatarText}>{item.email[0].toUpperCase()}</Text>
                    </View>
                    <View style={styles.info}>
                        <Text style={styles.email}>{item.email}</Text>
                        <Text style={styles.region}>
                            {region ? `Region: ${region.name}` : 'No Region Assigned'}
                        </Text>
                    </View>
                </View>
                <TouchableOpacity
                    onPress={() => handleDeleteAdmin(item.id)}
                    style={styles.deleteBtn}
                >
                    <Ionicons name="trash-outline" size={20} color="#FF5252" />
                </TouchableOpacity>
            </View>
        );
    };

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#1E88E5" />
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>Regional Admins</Text>
                <TouchableOpacity
                    style={styles.addBtn}
                    onPress={() => setModalVisible(true)}
                >
                    <Ionicons name="add" size={24} color="#fff" />
                    <Text style={styles.addBtnText}>Add New</Text>
                </TouchableOpacity>
            </View>

            <FlatList
                data={admins}
                renderItem={renderAdminItem}
                keyExtractor={item => item.id.toString()}
                contentContainerStyle={styles.list}
                ListEmptyComponent={
                    <Text style={styles.emptyText}>No regional admins found</Text>
                }
            />

            <Modal
                visible={modalVisible}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setModalVisible(false)}
            >
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>Add Regional Admin</Text>
                            <TouchableOpacity onPress={() => setModalVisible(false)}>
                                <Ionicons name="close" size={24} color="#666" />
                            </TouchableOpacity>
                        </View>

                        <View style={styles.form}>
                            <Text style={styles.label}>Email</Text>
                            <TextInput
                                style={styles.input}
                                value={email}
                                onChangeText={setEmail}
                                placeholder="admin@example.com"
                                autoCapitalize="none"
                                keyboardType="email-address"
                            />

                            <Text style={styles.label}>Password</Text>
                            <TextInput
                                style={styles.input}
                                value={password}
                                onChangeText={setPassword}
                                placeholder="Password"
                                secureTextEntry
                            />

                            <Text style={styles.label}>Assign Region</Text>
                            <View style={styles.regionsList}>
                                {regions.map(region => (
                                    <TouchableOpacity
                                        key={region.id}
                                        style={[
                                            styles.regionChip,
                                            selectedRegion === region.id && styles.regionChipSelected,
                                            region.admin_id && styles.regionChipDisabled
                                        ]}
                                        onPress={() => !region.admin_id && setSelectedRegion(region.id)}
                                        disabled={!!region.admin_id}
                                    >
                                        <Text style={[
                                            styles.regionChipText,
                                            selectedRegion === region.id && styles.regionChipTextSelected,
                                            region.admin_id && styles.regionChipTextDisabled
                                        ]}>
                                            {region.name}
                                            {region.admin_id ? ' (Assigned)' : ''}
                                        </Text>
                                    </TouchableOpacity>
                                ))}
                            </View>

                            <TouchableOpacity
                                style={[styles.submitBtn, submitting && styles.disabledBtn]}
                                onPress={handleAddAdmin}
                                disabled={submitting}
                            >
                                {submitting ? (
                                    <ActivityIndicator color="#fff" />
                                ) : (
                                    <Text style={styles.submitBtnText}>Create Admin</Text>
                                )}
                            </TouchableOpacity>
                        </View>
                    </View>
                </View>
            </Modal>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    header: {
        padding: 20,
        backgroundColor: '#fff',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    addBtn: {
        backgroundColor: '#1E88E5',
        flexDirection: 'row',
        alignItems: 'center',
        padding: 8,
        paddingHorizontal: 12,
        borderRadius: 8
    },
    addBtnText: { color: '#fff', fontWeight: '600', marginLeft: 4 },
    list: { padding: 15 },
    card: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 15,
        marginBottom: 10,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        elevation: 2
    },
    cardContent: { flexDirection: 'row', alignItems: 'center', flex: 1 },
    avatar: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12
    },
    avatarText: { fontSize: 18, fontWeight: 'bold', color: '#1E88E5' },
    info: { flex: 1 },
    email: { fontSize: 16, fontWeight: '500', color: '#333' },
    region: { fontSize: 14, color: '#666', marginTop: 2 },
    deleteBtn: { padding: 8 },
    emptyText: { textAlign: 'center', color: '#999', marginTop: 50 },

    // Modal
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'flex-end'
    },
    modalContent: {
        backgroundColor: '#fff',
        borderTopLeftRadius: 20,
        borderTopRightRadius: 20,
        padding: 20,
        maxHeight: '80%'
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20
    },
    modalTitle: { fontSize: 20, fontWeight: 'bold', color: '#333' },
    form: { gap: 15 },
    label: { fontSize: 14, fontWeight: '600', color: '#666', marginBottom: 5 },
    input: {
        backgroundColor: '#f5f5f5',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        borderWidth: 1,
        borderColor: '#eee'
    },
    regionsList: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
    regionChip: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 20,
        backgroundColor: '#f5f5f5',
        borderWidth: 1,
        borderColor: '#ddd'
    },
    regionChipSelected: {
        backgroundColor: '#E3F2FD',
        borderColor: '#1E88E5'
    },
    regionChipDisabled: {
        opacity: 0.5,
        backgroundColor: '#eee'
    },
    regionChipText: { fontSize: 14, color: '#333' },
    regionChipTextSelected: { color: '#1E88E5', fontWeight: '600' },
    regionChipTextDisabled: { color: '#999' },
    submitBtn: {
        backgroundColor: '#1E88E5',
        padding: 15,
        borderRadius: 10,
        alignItems: 'center',
        marginTop: 10
    },
    disabledBtn: { opacity: 0.7 },
    submitBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' }
});

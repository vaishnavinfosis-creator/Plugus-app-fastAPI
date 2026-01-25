import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

export default function VendorsScreen() {
    const [vendors, setVendors] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchVendors();
    }, []);

    const fetchVendors = async () => {
        try {
            const res = await client.get('/admin/vendors');
            setVendors(res.data);
        } catch (e) {
            console.log('Error:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (vendorId) => {
        try {
            await client.put(`/admin/vendors/${vendorId}/approve`);
            Alert.alert('Success', 'Vendor approved');
            fetchVendors();
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to approve');
        }
    };

    const handleReject = async (vendorId) => {
        try {
            await client.put(`/admin/vendors/${vendorId}/reject`);
            Alert.alert('Success', 'Vendor rejected');
            fetchVendors();
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to reject');
        }
    };

    const handleToggleVisibility = async (vendor) => {
        try {
            await client.put(`/admin/vendors/${vendor.id}/visibility?visible=${!vendor.is_visible}`);
            fetchVendors();
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to update');
        }
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
                <Text style={styles.title}>Vendors</Text>
            </View>

            <FlatList
                data={vendors}
                keyExtractor={(item) => item.id.toString()}
                contentContainerStyle={styles.list}
                renderItem={({ item }) => (
                    <View style={styles.vendorCard}>
                        <View style={styles.vendorHeader}>
                            <View style={styles.vendorIcon}>
                                <Ionicons name="storefront" size={24} color="#1E88E5" />
                            </View>
                            <View style={styles.vendorInfo}>
                                <Text style={styles.vendorName}>{item.business_name}</Text>
                                <View style={styles.badgesRow}>
                                    <View style={[
                                        styles.badge,
                                        { backgroundColor: item.is_approved ? '#E8F5E9' : '#FFF3E0' }
                                    ]}>
                                        <Text style={[
                                            styles.badgeText,
                                            { color: item.is_approved ? '#2E7D32' : '#E65100' }
                                        ]}>
                                            {item.is_approved ? 'Approved' : 'Pending'}
                                        </Text>
                                    </View>
                                    {item.is_approved && (
                                        <View style={[
                                            styles.badge,
                                            { backgroundColor: item.is_visible ? '#E3F2FD' : '#ECEFF1' }
                                        ]}>
                                            <Text style={[
                                                styles.badgeText,
                                                { color: item.is_visible ? '#1565C0' : '#546E7A' }
                                            ]}>
                                                {item.is_visible ? 'Visible' : 'Hidden'}
                                            </Text>
                                        </View>
                                    )}
                                </View>
                            </View>
                        </View>

                        <View style={styles.actionsRow}>
                            {!item.is_approved && (
                                <>
                                    <TouchableOpacity
                                        style={[styles.actionBtn, { backgroundColor: '#4CAF50' }]}
                                        onPress={() => handleApprove(item.id)}
                                    >
                                        <Ionicons name="checkmark" size={18} color="#fff" />
                                        <Text style={styles.actionBtnText}>Approve</Text>
                                    </TouchableOpacity>
                                    <TouchableOpacity
                                        style={[styles.actionBtn, { backgroundColor: '#E53935' }]}
                                        onPress={() => handleReject(item.id)}
                                    >
                                        <Ionicons name="close" size={18} color="#fff" />
                                        <Text style={styles.actionBtnText}>Reject</Text>
                                    </TouchableOpacity>
                                </>
                            )}
                            {item.is_approved && (
                                <TouchableOpacity
                                    style={[styles.actionBtn, {
                                        backgroundColor: item.is_visible ? '#FF9800' : '#1E88E5'
                                    }]}
                                    onPress={() => handleToggleVisibility(item)}
                                >
                                    <Ionicons
                                        name={item.is_visible ? 'eye-off' : 'eye'}
                                        size={18} color="#fff"
                                    />
                                    <Text style={styles.actionBtnText}>
                                        {item.is_visible ? 'Hide' : 'Show'}
                                    </Text>
                                </TouchableOpacity>
                            )}
                        </View>
                    </View>
                )}
                ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                        <Ionicons name="storefront-outline" size={60} color="#ccc" />
                        <Text style={styles.emptyText}>No vendors yet</Text>
                    </View>
                }
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    header: { padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#eee' },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    list: { padding: 15 },
    vendorCard: { backgroundColor: '#fff', borderRadius: 12, padding: 15, marginBottom: 12, elevation: 2 },
    vendorHeader: { flexDirection: 'row', marginBottom: 12 },
    vendorIcon: {
        width: 50,
        height: 50,
        borderRadius: 25,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center'
    },
    vendorInfo: { flex: 1, marginLeft: 12 },
    vendorName: { fontSize: 16, fontWeight: '600', color: '#333' },
    badgesRow: { flexDirection: 'row', marginTop: 6, gap: 8 },
    badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 },
    badgeText: { fontSize: 11, fontWeight: '600' },
    actionsRow: { flexDirection: 'row', gap: 10, borderTopWidth: 1, borderTopColor: '#f0f0f0', paddingTop: 12 },
    actionBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 8
    },
    actionBtnText: { color: '#fff', fontWeight: '600', marginLeft: 4 },
    emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 100 },
    emptyText: { marginTop: 15, fontSize: 16, color: '#999' }
});

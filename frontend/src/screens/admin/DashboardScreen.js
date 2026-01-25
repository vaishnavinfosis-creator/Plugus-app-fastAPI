import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import { useAuthStore } from '../../store/authStore';

export default function DashboardScreen({ navigation }) {
    const { user } = useAuthStore();
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const isSuperAdmin = user?.role === 'SUPER_ADMIN';

    useEffect(() => {
        console.log('DashboardScreen mounted');
        fetchStats();
    }, []);

    const fetchStats = async () => {
        console.log('Fetching dashboard stats...');
        try {
            const [vendorsRes, categoriesRes] = await Promise.all([
                client.get('/admin/vendors'),
                client.get('/admin/categories')
            ]);

            setStats({
                vendors: vendorsRes.data,
                categories: categoriesRes.data,
                pendingVendors: vendorsRes.data.filter(v => !v.is_approved).length
            });
        } catch (e) {
            console.log('Error:', e);
        } finally {
            setLoading(false);
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
                <Text style={styles.title}>Admin Dashboard</Text>
                <Text style={styles.subtitle}>
                    {isSuperAdmin ? 'Super Admin' : 'Regional Admin'}
                </Text>
            </View>

            <ScrollView style={styles.content}>
                {/* Quick Stats */}
                <View style={styles.statsRow}>
                    <View style={styles.statCard}>
                        <Ionicons name="storefront" size={28} color="#1E88E5" />
                        <Text style={styles.statNumber}>{stats?.vendors?.length || 0}</Text>
                        <Text style={styles.statLabel}>Total Vendors</Text>
                    </View>
                    <View style={[styles.statCard, { backgroundColor: '#FFF3E0' }]}>
                        <Ionicons name="hourglass" size={28} color="#E65100" />
                        <Text style={styles.statNumber}>{stats?.pendingVendors || 0}</Text>
                        <Text style={styles.statLabel}>Pending Approval</Text>
                    </View>
                </View>

                <View style={styles.statsRow}>
                    <View style={[styles.statCard, { backgroundColor: '#E8F5E9' }]}>
                        <Ionicons name="apps" size={28} color="#2E7D32" />
                        <Text style={styles.statNumber}>{stats?.categories?.length || 0}</Text>
                        <Text style={styles.statLabel}>Categories</Text>
                    </View>
                    {isSuperAdmin && (
                        <View style={[styles.statCard, { backgroundColor: '#EDE7F6' }]}>
                            <Ionicons name="people" size={28} color="#5E35B1" />
                            <Text style={styles.statNumber}>-</Text>
                            <Text style={styles.statLabel}>Regional Admins</Text>
                        </View>
                    )}
                </View>

                {/* Quick Actions */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Quick Actions</Text>
                    <View style={styles.actionCard}>
                        <Ionicons name="checkmark-circle-outline" size={24} color="#1E88E5" />
                        <View style={styles.actionInfo}>
                            <Text style={styles.actionTitle}>Approve Vendors</Text>
                            <Text style={styles.actionDesc}>{stats?.pendingVendors || 0} pending</Text>
                        </View>
                    </View>
                    {isSuperAdmin && (
                        <>
                            <TouchableOpacity
                                style={styles.actionCard}
                                onPress={() => navigation.navigate('Categories')}
                            >
                                <Ionicons name="add-circle-outline" size={24} color="#4CAF50" />
                                <View style={styles.actionInfo}>
                                    <Text style={styles.actionTitle}>Manage Categories</Text>
                                    <Text style={styles.actionDesc}>Create new service category</Text>
                                </View>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={styles.actionCard}
                                onPress={() => navigation.navigate('Admins')}
                            >
                                <Ionicons name="people-outline" size={24} color="#5E35B1" />
                                <View style={styles.actionInfo}>
                                    <Text style={styles.actionTitle}>Manage Admins</Text>
                                    <Text style={styles.actionDesc}>Add or remove regional admins</Text>
                                </View>
                            </TouchableOpacity>
                        </>
                    )}
                </View>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    header: { padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#eee' },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    subtitle: { fontSize: 14, color: '#1E88E5', marginTop: 4 },
    content: { flex: 1, padding: 15 },
    statsRow: { flexDirection: 'row', gap: 15, marginBottom: 15 },
    statCard: {
        flex: 1,
        backgroundColor: '#E3F2FD',
        padding: 20,
        borderRadius: 12,
        alignItems: 'center',
        elevation: 2
    },
    statNumber: { fontSize: 28, fontWeight: 'bold', color: '#333', marginTop: 8 },
    statLabel: { fontSize: 12, color: '#666', marginTop: 4, textAlign: 'center' },
    section: { marginTop: 10 },
    sectionTitle: { fontSize: 18, fontWeight: '600', color: '#333', marginBottom: 15 },
    actionCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 12,
        marginBottom: 10,
        elevation: 1
    },
    actionInfo: { marginLeft: 15 },
    actionTitle: { fontSize: 16, fontWeight: '500', color: '#333' },
    actionDesc: { fontSize: 13, color: '#666', marginTop: 2 }
});

import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity, RefreshControl, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

const STATUS_COLORS = {
    'CREATED': { bg: '#FFF3E0', text: '#E65100' },
    'VENDOR_ACCEPTED': { bg: '#E3F2FD', text: '#1565C0' },
    'WORKER_ASSIGNED': { bg: '#E8F5E9', text: '#2E7D32' },
    'IN_PROGRESS': { bg: '#E1F5FE', text: '#0277BD' },
    'COMPLETED': { bg: '#E8F5E9', text: '#388E3C' },
    'PAYMENT_UPLOADED': { bg: '#C8E6C9', text: '#1B5E20' }
};

export default function OrdersScreen({ navigation }) {
    const [orders, setOrders] = useState([]);
    const [workers, setWorkers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [ordersRes, workersRes] = await Promise.all([
                client.get('/vendor/orders'),
                client.get('/vendor/workers')
            ]);
            setOrders(ordersRes.data);
            setWorkers(workersRes.data);
        } catch (e) {
            console.log('Error:', e);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchData();
    }, []);

    const handleAccept = async (orderId) => {
        try {
            await client.put(`/vendor/orders/${orderId}/accept`);
            Alert.alert('Success', 'Order accepted');
            fetchData();
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to accept');
        }
    };

    const handleAssignWorker = (orderId) => {
        const availableWorkers = workers.filter(w => w.is_available);
        if (availableWorkers.length === 0) {
            Alert.alert('No Workers', 'No available workers to assign');
            return;
        }

        Alert.alert(
            'Assign Worker',
            'Select a worker',
            availableWorkers.map(w => ({
                text: `Worker #${w.id}`,
                onPress: () => assignWorker(orderId, w.id)
            })).concat([{ text: 'Cancel', style: 'cancel' }])
        );
    };

    const assignWorker = async (orderId, workerId) => {
        try {
            await client.put(`/vendor/orders/${orderId}/assign-worker?worker_id=${workerId}`);
            Alert.alert('Success', 'Worker assigned');
            fetchData();
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to assign');
        }
    };

    const formatDate = (dateStr) => {
        return new Date(dateStr).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
        });
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
                <Text style={styles.title}>Orders</Text>
            </View>

            {orders.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Ionicons name="receipt-outline" size={70} color="#ccc" />
                    <Text style={styles.emptyText}>No orders yet</Text>
                </View>
            ) : (
                <FlatList
                    data={orders}
                    keyExtractor={(item) => item.id.toString()}
                    contentContainerStyle={styles.list}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#1E88E5']} />
                    }
                    renderItem={({ item }) => (
                        <View style={styles.orderCard}>
                            <View style={styles.orderHeader}>
                                <Text style={styles.orderId}>Order #{item.id}</Text>
                                <View style={[
                                    styles.statusBadge,
                                    { backgroundColor: STATUS_COLORS[item.status]?.bg || '#eee' }
                                ]}>
                                    <Text style={[
                                        styles.statusText,
                                        { color: STATUS_COLORS[item.status]?.text || '#666' }
                                    ]}>
                                        {item.status.replace(/_/g, ' ')}
                                    </Text>
                                </View>
                            </View>

                            <View style={styles.orderDetails}>
                                <Text style={styles.dateText}>{formatDate(item.scheduled_time)}</Text>
                                <Text style={styles.priceText}>₹{item.total_cost}</Text>
                            </View>

                            {/* Action Buttons */}
                            {item.status === 'CREATED' && (
                                <TouchableOpacity
                                    style={styles.actionButton}
                                    onPress={() => handleAccept(item.id)}
                                >
                                    <Ionicons name="checkmark-circle" size={20} color="#fff" />
                                    <Text style={styles.actionButtonText}>Accept Order</Text>
                                </TouchableOpacity>
                            )}

                            {item.status === 'VENDOR_ACCEPTED' && (
                                <TouchableOpacity
                                    style={[styles.actionButton, { backgroundColor: '#4CAF50' }]}
                                    onPress={() => handleAssignWorker(item.id)}
                                >
                                    <Ionicons name="person-add" size={20} color="#fff" />
                                    <Text style={styles.actionButtonText}>Assign Worker</Text>
                                </TouchableOpacity>
                            )}

                            {item.worker_id && (
                                <View style={styles.workerInfo}>
                                    <Ionicons name="person" size={16} color="#666" />
                                    <Text style={styles.workerText}>Worker #{item.worker_id}</Text>
                                </View>
                            )}
                        </View>
                    )}
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    header: { padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#eee' },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    emptyText: { marginTop: 15, fontSize: 16, color: '#999' },
    list: { padding: 15 },
    orderCard: { backgroundColor: '#fff', borderRadius: 12, padding: 15, marginBottom: 12, elevation: 2 },
    orderHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
    orderId: { fontSize: 16, fontWeight: '600', color: '#333' },
    statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
    statusText: { fontSize: 11, fontWeight: '600' },
    orderDetails: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
    dateText: { color: '#666' },
    priceText: { fontSize: 18, fontWeight: 'bold', color: '#1E88E5' },
    actionButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#1E88E5',
        padding: 12,
        borderRadius: 8,
        marginTop: 10
    },
    actionButtonText: { color: '#fff', fontWeight: '600', marginLeft: 8 },
    workerInfo: { flexDirection: 'row', alignItems: 'center', marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#f0f0f0' },
    workerText: { marginLeft: 8, color: '#666' }
});

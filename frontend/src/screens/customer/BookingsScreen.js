import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

const STATUS_COLORS = {
    'CREATED': { bg: '#FFF3E0', text: '#E65100' },
    'VENDOR_ACCEPTED': { bg: '#E3F2FD', text: '#1565C0' },
    'VENDOR_REJECTED': { bg: '#FFEBEE', text: '#C62828' },
    'WORKER_ASSIGNED': { bg: '#E8F5E9', text: '#2E7D32' },
    'IN_PROGRESS': { bg: '#E1F5FE', text: '#0277BD' },
    'COMPLETED': { bg: '#E8F5E9', text: '#388E3C' },
    'PAYMENT_UPLOADED': { bg: '#C8E6C9', text: '#1B5E20' },
    'CANCELLED': { bg: '#ECEFF1', text: '#546E7A' }
};

const STATUS_LABELS = {
    'CREATED': 'Pending',
    'VENDOR_ACCEPTED': 'Accepted',
    'VENDOR_REJECTED': 'Rejected',
    'WORKER_ASSIGNED': 'Worker Assigned',
    'IN_PROGRESS': 'In Progress',
    'COMPLETED': 'Completed',
    'PAYMENT_UPLOADED': 'Payment Done',
    'CANCELLED': 'Cancelled'
};

export default function BookingsScreen({ navigation }) {
    const [bookings, setBookings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        fetchBookings();
    }, []);

    const fetchBookings = async () => {
        try {
            const res = await client.get('/customer/bookings');
            setBookings(res.data);
        } catch (e) {
            console.log('Error fetching bookings:', e);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchBookings();
    }, []);

    const handleBookingPress = (booking) => {
        navigation.navigate('BookingDetail', { bookingId: booking.id });
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatPrice = (price) => `₹${price?.toLocaleString('en-IN') || 0}`;

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
                <Text style={styles.title}>My Bookings</Text>
            </View>

            {bookings.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Ionicons name="calendar-outline" size={70} color="#ccc" />
                    <Text style={styles.emptyText}>No bookings yet</Text>
                    <Text style={styles.emptySubtext}>Book a service to get started</Text>
                </View>
            ) : (
                <FlatList
                    data={bookings}
                    keyExtractor={(item) => item.id.toString()}
                    contentContainerStyle={styles.list}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#1E88E5']} />
                    }
                    renderItem={({ item }) => (
                        <TouchableOpacity
                            style={styles.bookingCard}
                            onPress={() => handleBookingPress(item)}
                        >
                            <View style={styles.bookingHeader}>
                                <Text style={styles.bookingId}>#{item.id}</Text>
                                <View style={[
                                    styles.statusBadge,
                                    { backgroundColor: STATUS_COLORS[item.status]?.bg || '#eee' }
                                ]}>
                                    <Text style={[
                                        styles.statusText,
                                        { color: STATUS_COLORS[item.status]?.text || '#666' }
                                    ]}>
                                        {STATUS_LABELS[item.status] || item.status}
                                    </Text>
                                </View>
                            </View>

                            <View style={styles.bookingDetails}>
                                <View style={styles.detailRow}>
                                    <Ionicons name="calendar-outline" size={16} color="#666" />
                                    <Text style={styles.detailText}>{formatDate(item.scheduled_time)}</Text>
                                </View>
                            </View>

                            <View style={styles.bookingFooter}>
                                <Text style={styles.bookingPrice}>{formatPrice(item.total_cost)}</Text>
                                <Ionicons name="chevron-forward" size={20} color="#ccc" />
                            </View>
                        </TouchableOpacity>
                    )}
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    header: {
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20
    },
    emptyText: {
        marginTop: 15,
        fontSize: 18,
        fontWeight: '600',
        color: '#666'
    },
    emptySubtext: {
        marginTop: 5,
        fontSize: 14,
        color: '#999'
    },
    list: { padding: 15 },
    bookingCard: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 15,
        marginBottom: 12,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2
    },
    bookingHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12
    },
    bookingId: { fontSize: 16, fontWeight: '600', color: '#333' },
    statusBadge: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12
    },
    statusText: { fontSize: 12, fontWeight: '600' },
    bookingDetails: { marginBottom: 12 },
    detailRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 6
    },
    detailText: { marginLeft: 8, color: '#666', fontSize: 14 },
    bookingFooter: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderTopWidth: 1,
        borderTopColor: '#f0f0f0',
        paddingTop: 12
    },
    bookingPrice: { fontSize: 18, fontWeight: 'bold', color: '#1E88E5' }
});

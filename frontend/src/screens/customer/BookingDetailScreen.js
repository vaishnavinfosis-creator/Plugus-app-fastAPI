import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, Alert } from 'react-native';
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
    'CREATED': 'Pending Vendor Confirmation',
    'VENDOR_ACCEPTED': 'Vendor Accepted',
    'VENDOR_REJECTED': 'Vendor Rejected',
    'WORKER_ASSIGNED': 'Worker Assigned',
    'IN_PROGRESS': 'Service In Progress',
    'COMPLETED': 'Service Completed',
    'PAYMENT_UPLOADED': 'Payment Confirmed',
    'CANCELLED': 'Cancelled'
};

export default function BookingDetailScreen({ route, navigation }) {
    const { bookingId } = route.params;
    const [booking, setBooking] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchBookingDetails();
    }, []);

    const fetchBookingDetails = async () => {
        try {
            const res = await client.get(`/customer/bookings/${bookingId}`);
            setBooking(res.data);
        } catch (e) {
            console.log('Error fetching booking:', e);
            Alert.alert('Error', 'Failed to load booking details');
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatPrice = (price) => `₹${price?.toLocaleString('en-IN') || 0}`;

    const canReview = booking?.status === 'COMPLETED' || booking?.status === 'PAYMENT_UPLOADED';
    const canComplain = ['COMPLETED', 'PAYMENT_UPLOADED'].includes(booking?.status);

    const handleReview = () => {
        // Navigate to review screen
        Alert.alert('Review', 'Review functionality coming soon!');
    };

    const handleComplaint = () => {
        // Navigate to complaint screen with booking ID
        navigation.navigate('Complaints', {
            screen: 'CreateComplaint',
            params: { bookingId: booking.id }
        });
    };

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#1E88E5" />
            </View>
        );
    }

    if (!booking) {
        return (
            <View style={styles.errorContainer}>
                <Text style={styles.errorText}>Booking not found</Text>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#333" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Booking #{booking.id}</Text>
            </View>

            <ScrollView style={styles.content}>
                {/* Status */}
                <View style={[
                    styles.statusCard,
                    { backgroundColor: STATUS_COLORS[booking.status]?.bg || '#f0f0f0' }
                ]}>
                    <Ionicons
                        name={booking.status === 'COMPLETED' || booking.status === 'PAYMENT_UPLOADED'
                            ? 'checkmark-circle'
                            : 'time'}
                        size={28}
                        color={STATUS_COLORS[booking.status]?.text || '#666'}
                    />
                    <Text style={[
                        styles.statusText,
                        { color: STATUS_COLORS[booking.status]?.text || '#666' }
                    ]}>
                        {STATUS_LABELS[booking.status] || booking.status}
                    </Text>
                </View>

                {/* Service Details */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Service</Text>
                    <Text style={styles.serviceName}>{booking.service_name}</Text>
                    <Text style={styles.vendorName}>{booking.vendor_name}</Text>
                </View>

                {/* Schedule */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Schedule</Text>
                    <View style={styles.infoRow}>
                        <Ionicons name="calendar-outline" size={20} color="#666" />
                        <Text style={styles.infoText}>{formatDate(booking.scheduled_time)}</Text>
                    </View>
                </View>

                {/* Address & Phone */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Contact Details</Text>
                    {booking.address_text && (
                        <View style={styles.infoRow}>
                            <Ionicons name="location-outline" size={20} color="#666" />
                            <Text style={styles.infoText}>{booking.address_text}</Text>
                        </View>
                    )}
                    {booking.phone_number && (
                        <View style={styles.infoRow}>
                            <Ionicons name="call-outline" size={20} color="#666" />
                            <Text style={styles.infoText}>{booking.phone_number}</Text>
                        </View>
                    )}
                </View>

                {/* Worker */}
                {booking.worker_name && (
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Assigned Worker</Text>
                        <View style={styles.workerRow}>
                            <View style={styles.workerAvatar}>
                                <Ionicons name="person" size={24} color="#1E88E5" />
                            </View>
                            <Text style={styles.workerName}>{booking.worker_name}</Text>
                        </View>

                        {/* Track Worker Button - only for IN_PROGRESS status */}
                        {booking.status === 'IN_PROGRESS' && (
                            <TouchableOpacity
                                style={styles.trackButton}
                                onPress={() => navigation.navigate('WorkerTracking', {
                                    bookingId: booking.id,
                                    workerName: booking.worker_name
                                })}
                            >
                                <Ionicons name="navigate" size={18} color="#fff" />
                                <Text style={styles.trackButtonText}>Track Worker Live</Text>
                            </TouchableOpacity>
                        )}
                    </View>
                )}

                {/* Payment Summary */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Payment Summary</Text>
                    <View style={styles.paymentRow}>
                        <Text style={styles.paymentLabel}>Service Charge</Text>
                        <Text style={styles.paymentValue}>{formatPrice(booking.fixed_charge)}</Text>
                    </View>
                    {booking.additional_cost > 0 && (
                        <View style={styles.paymentRow}>
                            <Text style={styles.paymentLabel}>Additional Cost</Text>
                            <Text style={styles.paymentValue}>{formatPrice(booking.additional_cost)}</Text>
                        </View>
                    )}
                    <View style={[styles.paymentRow, styles.totalRow]}>
                        <Text style={styles.totalLabel}>Total</Text>
                        <Text style={styles.totalValue}>{formatPrice(booking.total_cost)}</Text>
                    </View>
                </View>

                {/* Actions */}
                {(canReview || canComplain) && (
                    <View style={styles.actionsRow}>
                        {canReview && (
                            <TouchableOpacity style={styles.reviewBtn} onPress={handleReview}>
                                <Ionicons name="star" size={20} color="#fff" />
                                <Text style={styles.reviewBtnText}>Rate & Review</Text>
                            </TouchableOpacity>
                        )}
                        {canComplain && (
                            <TouchableOpacity style={styles.complainBtn} onPress={handleComplaint}>
                                <Ionicons name="warning" size={20} color="#E65100" />
                                <Text style={styles.complainBtnText}>File Complaint</Text>
                            </TouchableOpacity>
                        )}
                    </View>
                )}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    errorContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    errorText: { fontSize: 16, color: '#999' },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    backButton: { marginRight: 15 },
    headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#333' },
    content: { flex: 1, padding: 15 },
    statusCard: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 15,
        borderRadius: 12,
        marginBottom: 15
    },
    statusText: { fontSize: 16, fontWeight: '600', marginLeft: 10 },
    card: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 15,
        marginBottom: 15,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2
    },
    cardTitle: { fontSize: 14, fontWeight: '600', color: '#999', marginBottom: 10 },
    serviceName: { fontSize: 18, fontWeight: '600', color: '#333' },
    vendorName: { fontSize: 14, color: '#666', marginTop: 4 },
    infoRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
    infoText: { marginLeft: 10, color: '#333', flex: 1 },
    workerRow: { flexDirection: 'row', alignItems: 'center' },
    workerAvatar: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center'
    },
    workerName: { marginLeft: 12, fontSize: 16, fontWeight: '500', color: '#333' },
    paymentRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
    paymentLabel: { color: '#666' },
    paymentValue: { color: '#333', fontWeight: '500' },
    totalRow: { borderTopWidth: 1, borderTopColor: '#eee', paddingTop: 10, marginTop: 5 },
    totalLabel: { fontSize: 16, fontWeight: '600', color: '#333' },
    totalValue: { fontSize: 20, fontWeight: 'bold', color: '#1E88E5' },
    actionsRow: { flexDirection: 'row', gap: 10, marginBottom: 30 },
    reviewBtn: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#1E88E5',
        padding: 14,
        borderRadius: 10
    },
    reviewBtnText: { color: '#fff', fontWeight: '600', marginLeft: 8 },
    complainBtn: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#FFF3E0',
        padding: 14,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: '#FFB74D'
    },
    complainBtnText: { color: '#E65100', fontWeight: '600', marginLeft: 8 },
    trackButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#4CAF50',
        padding: 12,
        borderRadius: 10,
        marginTop: 12
    },
    trackButtonText: { color: '#fff', fontWeight: '600', marginLeft: 8 }
});

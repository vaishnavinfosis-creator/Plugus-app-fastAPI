import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    FlatList,
    TouchableOpacity,
    StyleSheet,
    Image,
    Alert,
    ActivityIndicator,
    RefreshControl
} from 'react-native';
import client from '../../api/client';

const PaymentVerificationScreen = ({ navigation }) => {
    const [pendingPayments, setPendingPayments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadPendingPayments();
    }, []);

    const loadPendingPayments = async () => {
        try {
            const response = await client.get('/payments/admin/payments/pending');
            setPendingPayments(response.data.bookings || []);
        } catch (error) {
            Alert.alert('Error', 'Failed to load pending payments');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const handleVerify = async (bookingId, approved) => {
        Alert.alert(
            approved ? 'Approve Payment' : 'Reject Payment',
            `Are you sure you want to ${approved ? 'approve' : 'reject'} this payment?`,
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: approved ? 'Approve' : 'Reject',
                    style: approved ? 'default' : 'destructive',
                    onPress: async () => {
                        try {
                            await client.put(
                                `/payments/admin/bookings/${bookingId}/verify-payment`,
                                { approved }
                            );
                            Alert.alert('Success', `Payment ${approved ? 'approved' : 'rejected'} successfully`);
                            loadPendingPayments();
                        } catch (error) {
                            Alert.alert('Error', 'Failed to verify payment');
                        }
                    }
                }
            ]
        );
    };

    const viewReceipt = async (bookingId) => {
        try {
            const response = await client.get(`/payments/bookings/${bookingId}/payment-receipt-url`);
            // In a real app, open the secure URL
            Alert.alert('Receipt', `File: ${response.data.file_path}`);
        } catch (error) {
            Alert.alert('Error', 'Failed to load receipt');
        }
    };

    const renderPaymentItem = ({ item }) => (
        <View style={styles.paymentCard}>
            <View style={styles.paymentHeader}>
                <Text style={styles.bookingId}>Booking #{item.id}</Text>
                <Text style={styles.amount}>${item.total_cost}</Text>
            </View>
            
            <Text style={styles.customerInfo}>Customer ID: {item.customer_id}</Text>
            <Text style={styles.date}>
                Uploaded: {new Date(item.created_at).toLocaleDateString()}
            </Text>

            <View style={styles.buttonRow}>
                <TouchableOpacity
                    style={[styles.button, styles.viewButton]}
                    onPress={() => viewReceipt(item.id)}
                >
                    <Text style={styles.buttonText}>View Receipt</Text>
                </TouchableOpacity>

                <TouchableOpacity
                    style={[styles.button, styles.approveButton]}
                    onPress={() => handleVerify(item.id, true)}
                >
                    <Text style={styles.buttonText}>✓ Approve</Text>
                </TouchableOpacity>

                <TouchableOpacity
                    style={[styles.button, styles.rejectButton]}
                    onPress={() => handleVerify(item.id, false)}
                >
                    <Text style={styles.buttonText}>✗ Reject</Text>
                </TouchableOpacity>
            </View>
        </View>
    );

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#007AFF" />
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Payment Verification</Text>
            <Text style={styles.subtitle}>
                {pendingPayments.length} pending payment{pendingPayments.length !== 1 ? 's' : ''}
            </Text>

            <FlatList
                data={pendingPayments}
                renderItem={renderPaymentItem}
                keyExtractor={(item) => item.id.toString()}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={() => {
                        setRefreshing(true);
                        loadPendingPayments();
                    }} />
                }
                ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                        <Text style={styles.emptyText}>No pending payments</Text>
                    </View>
                }
            />
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
        padding: 15,
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 5,
    },
    subtitle: {
        fontSize: 16,
        color: '#666',
        marginBottom: 15,
    },
    paymentCard: {
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 8,
        marginBottom: 10,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    paymentHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 10,
    },
    bookingId: {
        fontSize: 18,
        fontWeight: 'bold',
    },
    amount: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#007AFF',
    },
    customerInfo: {
        fontSize: 14,
        color: '#666',
        marginBottom: 5,
    },
    date: {
        fontSize: 12,
        color: '#999',
        marginBottom: 15,
    },
    buttonRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    button: {
        flex: 1,
        padding: 10,
        borderRadius: 6,
        alignItems: 'center',
        marginHorizontal: 3,
    },
    viewButton: {
        backgroundColor: '#5856D6',
    },
    approveButton: {
        backgroundColor: '#34C759',
    },
    rejectButton: {
        backgroundColor: '#FF3B30',
    },
    buttonText: {
        color: '#fff',
        fontSize: 14,
        fontWeight: '600',
    },
    emptyContainer: {
        padding: 40,
        alignItems: 'center',
    },
    emptyText: {
        fontSize: 16,
        color: '#999',
    },
});

export default PaymentVerificationScreen;

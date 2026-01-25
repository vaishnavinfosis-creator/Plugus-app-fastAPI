import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator, TextInput } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

export default function TaskDetailScreen({ route, navigation }) {
    const { taskId } = route.params;
    const [task, setTask] = useState(null);
    const [loading, setLoading] = useState(true);
    const [additionalCost, setAdditionalCost] = useState('0');
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        fetchTask();
    }, []);

    const fetchTask = async () => {
        try {
            const res = await client.get(`/worker/tasks/${taskId}`);
            setTask(res.data);
        } catch (e) {
            console.log('Error:', e);
            Alert.alert('Error', 'Failed to load task');
        } finally {
            setLoading(false);
        }
    };

    const handleComplete = async () => {
        setSubmitting(true);
        try {
            await client.put(`/worker/tasks/${taskId}/complete`, {
                additional_cost: parseFloat(additionalCost) || 0,
                payment_screenshot_url: null // Would be uploaded in real app
            });
            Alert.alert('Success', 'Task completed!', [
                { text: 'OK', onPress: () => navigation.goBack() }
            ]);
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to complete task');
        } finally {
            setSubmitting(false);
        }
    };

    const formatDate = (dateStr) => {
        return new Date(dateStr).toLocaleDateString('en-IN', {
            weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit'
        });
    };

    const formatPrice = (price) => `₹${(price || 0).toLocaleString('en-IN')}`;

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#1E88E5" />
            </View>
        );
    }

    if (!task) {
        return (
            <View style={styles.errorContainer}>
                <Text>Task not found</Text>
            </View>
        );
    }

    const canComplete = task.status === 'IN_PROGRESS';

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#333" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Task #{task.id}</Text>
            </View>

            <ScrollView style={styles.content}>
                {/* Service Info */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Service</Text>
                    <Text style={styles.serviceName}>{task.service_name}</Text>
                    <Text style={styles.vendorName}>{task.vendor_name}</Text>
                </View>

                {/* Schedule */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Schedule</Text>
                    <View style={styles.infoRow}>
                        <Ionicons name="calendar-outline" size={20} color="#666" />
                        <Text style={styles.infoText}>{formatDate(task.scheduled_time)}</Text>
                    </View>
                </View>

                {/* Customer Info */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Customer</Text>
                    {task.customer_name && (
                        <View style={styles.infoRow}>
                            <Ionicons name="person-outline" size={20} color="#666" />
                            <Text style={styles.infoText}>{task.customer_name}</Text>
                        </View>
                    )}
                    {task.address_text && (
                        <View style={styles.infoRow}>
                            <Ionicons name="location-outline" size={20} color="#666" />
                            <Text style={styles.infoText}>{task.address_text}</Text>
                        </View>
                    )}
                    {task.phone_number && (
                        <View style={styles.infoRow}>
                            <Ionicons name="call-outline" size={20} color="#666" />
                            <Text style={styles.infoText}>{task.phone_number}</Text>
                        </View>
                    )}

                    {/* Directions Button */}
                    {task.address_text && (
                        <TouchableOpacity style={styles.directionsButton}>
                            <Ionicons name="navigate" size={20} color="#fff" />
                            <Text style={styles.directionsButtonText}>Get Directions</Text>
                        </TouchableOpacity>
                    )}
                </View>

                {/* Payment */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Payment</Text>
                    <View style={styles.paymentRow}>
                        <Text style={styles.paymentLabel}>Service Charge</Text>
                        <Text style={styles.paymentValue}>{formatPrice(task.fixed_charge)}</Text>
                    </View>

                    {canComplete && (
                        <View style={styles.additionalCostSection}>
                            <Text style={styles.paymentLabel}>Additional Cost</Text>
                            <View style={styles.inputRow}>
                                <Text style={styles.currencySymbol}>₹</Text>
                                <TextInput
                                    style={styles.costInput}
                                    value={additionalCost}
                                    onChangeText={setAdditionalCost}
                                    keyboardType="numeric"
                                    placeholder="0"
                                />
                            </View>
                        </View>
                    )}

                    <View style={[styles.paymentRow, styles.totalRow]}>
                        <Text style={styles.totalLabel}>Total</Text>
                        <Text style={styles.totalValue}>
                            {formatPrice(task.fixed_charge + (parseFloat(additionalCost) || 0))}
                        </Text>
                    </View>
                </View>
            </ScrollView>

            {/* Complete Button */}
            {canComplete && (
                <View style={styles.footer}>
                    <TouchableOpacity
                        style={[styles.completeButton, submitting && styles.buttonDisabled]}
                        onPress={handleComplete}
                        disabled={submitting}
                    >
                        <Ionicons name="checkmark-circle" size={24} color="#fff" />
                        <Text style={styles.completeButtonText}>
                            {submitting ? 'Completing...' : 'Mark as Completed'}
                        </Text>
                    </TouchableOpacity>
                </View>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    errorContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
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
    card: { backgroundColor: '#fff', borderRadius: 12, padding: 15, marginBottom: 15, elevation: 2 },
    cardTitle: { fontSize: 14, fontWeight: '600', color: '#999', marginBottom: 10 },
    serviceName: { fontSize: 18, fontWeight: '600', color: '#333' },
    vendorName: { fontSize: 14, color: '#666', marginTop: 4 },
    infoRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
    infoText: { marginLeft: 10, color: '#333', flex: 1 },
    directionsButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#4CAF50',
        padding: 14,
        borderRadius: 10,
        marginTop: 10
    },
    directionsButtonText: { color: '#fff', fontWeight: '600', marginLeft: 8 },
    paymentRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
    paymentLabel: { color: '#666' },
    paymentValue: { color: '#333', fontWeight: '500' },
    additionalCostSection: { marginVertical: 10 },
    inputRow: { flexDirection: 'row', alignItems: 'center', marginTop: 8 },
    currencySymbol: { fontSize: 20, color: '#333', marginRight: 4 },
    costInput: {
        flex: 1,
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 16
    },
    totalRow: { borderTopWidth: 1, borderTopColor: '#eee', paddingTop: 10, marginTop: 5 },
    totalLabel: { fontSize: 16, fontWeight: '600', color: '#333' },
    totalValue: { fontSize: 20, fontWeight: 'bold', color: '#1E88E5' },
    footer: { backgroundColor: '#fff', padding: 20, borderTopWidth: 1, borderTopColor: '#eee' },
    completeButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#4CAF50',
        padding: 16,
        borderRadius: 12
    },
    buttonDisabled: { backgroundColor: '#A5D6A7' },
    completeButtonText: { color: '#fff', fontSize: 18, fontWeight: '600', marginLeft: 8 }
});

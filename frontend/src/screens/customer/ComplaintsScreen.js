import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import ErrorDisplay from '../../components/ErrorDisplay';
import { getStructuredError } from '../../api/client';

const STATUS_COLORS = {
    'OPEN': { bg: '#FFF3E0', text: '#E65100' },
    'RESOLVED_PENDING_CUSTOMER': { bg: '#E3F2FD', text: '#1565C0' },
    'CLOSED': { bg: '#E8F5E9', text: '#388E3C' }
};

const STATUS_LABELS = {
    'OPEN': 'Pending',
    'RESOLVED_PENDING_CUSTOMER': 'Resolved',
    'CLOSED': 'Closed'
};

export default function ComplaintsScreen({ navigation }) {
    const [complaints, setComplaints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchComplaints();
    }, []);

    const fetchComplaints = async () => {
        try {
            setError(null);
            const res = await client.get('/complaints');
            setComplaints(res.data);
        } catch (e) {
            setError(getStructuredError(e));
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchComplaints();
    }, []);

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
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
                <Text style={styles.title}>My Complaints</Text>
                <TouchableOpacity
                    style={styles.createButton}
                    onPress={() => navigation.navigate('CreateComplaint')}
                >
                    <Ionicons name="add" size={24} color="#fff" />
                </TouchableOpacity>
            </View>

            {error && (
                <View style={styles.errorContainer}>
                    <ErrorDisplay error={error} onRetry={fetchComplaints} showRetry />
                </View>
            )}

            {complaints.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Ionicons name="chatbox-outline" size={70} color="#ccc" />
                    <Text style={styles.emptyText}>No complaints yet</Text>
                    <Text style={styles.emptySubtext}>File a complaint if you have any issues</Text>
                </View>
            ) : (
                <FlatList
                    data={complaints}
                    keyExtractor={(item) => item.id.toString()}
                    contentContainerStyle={styles.list}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#1E88E5']} />
                    }
                    renderItem={({ item }) => (
                        <TouchableOpacity style={styles.complaintCard}>
                            <View style={styles.complaintHeader}>
                                <Text style={styles.complaintId}>Complaint #{item.id}</Text>
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

                            <Text style={styles.description} numberOfLines={2}>
                                {item.description}
                            </Text>

                            <View style={styles.complaintFooter}>
                                <View style={styles.dateRow}>
                                    <Ionicons name="calendar-outline" size={14} color="#999" />
                                    <Text style={styles.dateText}>{formatDate(item.created_at)}</Text>
                                </View>
                                <Text style={styles.bookingRef}>Booking #{item.booking_id}</Text>
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
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    createButton: {
        backgroundColor: '#1E88E5',
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center'
    },
    errorContainer: { padding: 15 },
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
    complaintCard: {
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
    complaintHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 10
    },
    complaintId: { fontSize: 16, fontWeight: '600', color: '#333' },
    statusBadge: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12
    },
    statusText: { fontSize: 12, fontWeight: '600' },
    description: {
        fontSize: 14,
        color: '#666',
        marginBottom: 12,
        lineHeight: 20
    },
    complaintFooter: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderTopWidth: 1,
        borderTopColor: '#f0f0f0',
        paddingTop: 10
    },
    dateRow: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    dateText: {
        marginLeft: 5,
        fontSize: 12,
        color: '#999'
    },
    bookingRef: {
        fontSize: 12,
        color: '#1E88E5',
        fontWeight: '500'
    }
});

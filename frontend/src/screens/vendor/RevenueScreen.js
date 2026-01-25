import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

export default function RevenueScreen() {
    const [revenue, setRevenue] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchRevenue();
    }, []);

    const fetchRevenue = async () => {
        try {
            const res = await client.get('/vendor/revenue');
            setRevenue(res.data);
        } catch (e) {
            console.log('Error:', e);
        } finally {
            setLoading(false);
        }
    };

    const formatPrice = (price) => `₹${(price || 0).toLocaleString('en-IN')}`;

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
                <Text style={styles.title}>Revenue</Text>
            </View>

            <ScrollView style={styles.content}>
                {/* Today */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Ionicons name="today" size={24} color="#1E88E5" />
                        <Text style={styles.cardTitle}>Today</Text>
                    </View>
                    <View style={styles.statsRow}>
                        <View style={styles.stat}>
                            <Text style={styles.statNumber}>{revenue?.daily_orders || 0}</Text>
                            <Text style={styles.statLabel}>Orders</Text>
                        </View>
                        <View style={styles.stat}>
                            <Text style={styles.statValue}>{formatPrice(revenue?.daily_revenue)}</Text>
                            <Text style={styles.statLabel}>Revenue</Text>
                        </View>
                    </View>
                </View>

                {/* This Month */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Ionicons name="calendar" size={24} color="#4CAF50" />
                        <Text style={styles.cardTitle}>This Month</Text>
                    </View>
                    <View style={styles.statsRow}>
                        <View style={styles.stat}>
                            <Text style={styles.statNumber}>{revenue?.monthly_orders || 0}</Text>
                            <Text style={styles.statLabel}>Orders</Text>
                        </View>
                        <View style={styles.stat}>
                            <Text style={[styles.statValue, { color: '#4CAF50' }]}>{formatPrice(revenue?.monthly_revenue)}</Text>
                            <Text style={styles.statLabel}>Revenue</Text>
                        </View>
                    </View>
                </View>

                {/* All Time */}
                <View style={[styles.card, styles.totalCard]}>
                    <View style={styles.cardHeader}>
                        <Ionicons name="stats-chart" size={24} color="#fff" />
                        <Text style={[styles.cardTitle, { color: '#fff' }]}>All Time</Text>
                    </View>
                    <View style={styles.statsRow}>
                        <View style={styles.stat}>
                            <Text style={[styles.statNumber, { color: '#fff' }]}>{revenue?.total_orders || 0}</Text>
                            <Text style={[styles.statLabel, { color: 'rgba(255,255,255,0.8)' }]}>Total Orders</Text>
                        </View>
                        <View style={styles.stat}>
                            <Text style={[styles.statValue, { color: '#fff' }]}>{formatPrice(revenue?.total_revenue)}</Text>
                            <Text style={[styles.statLabel, { color: 'rgba(255,255,255,0.8)' }]}>Total Revenue</Text>
                        </View>
                    </View>
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
    content: { flex: 1, padding: 15 },
    card: {
        backgroundColor: '#fff',
        borderRadius: 16,
        padding: 20,
        marginBottom: 15,
        elevation: 3
    },
    totalCard: {
        backgroundColor: '#1E88E5'
    },
    cardHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
    cardTitle: { fontSize: 18, fontWeight: '600', color: '#333', marginLeft: 10 },
    statsRow: { flexDirection: 'row', justifyContent: 'space-around' },
    stat: { alignItems: 'center' },
    statNumber: { fontSize: 32, fontWeight: 'bold', color: '#333' },
    statValue: { fontSize: 24, fontWeight: 'bold', color: '#1E88E5' },
    statLabel: { fontSize: 14, color: '#666', marginTop: 4 }
});

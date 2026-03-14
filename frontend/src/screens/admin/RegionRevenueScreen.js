import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import ErrorDisplay from '../../components/ErrorDisplay';
import { getStructuredError } from '../../api/client';

/**
 * RegionRevenueScreen
 * 
 * Displays revenue breakdown by region for Super Admin
 * Shows list of all regions with their respective revenue amounts
 * Handles empty states: no regions and zero revenue
 */
export default function RegionRevenueScreen({ navigation }) {
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchRegionRevenue();
    }, []);

    const fetchRegionRevenue = async (isRefresh = false) => {
        if (isRefresh) {
            setRefreshing(true);
        } else {
            setLoading(true);
        }
        setError(null);

        try {
            const response = await client.get('/admin/revenue/regions');
            setRegions(response.data.regions || []);
        } catch (err) {
            console.error('Error fetching region revenue:', err);
            setError(getStructuredError(err));
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const formatINR = (amount) => {
        if (amount === null || amount === undefined || amount === 0) {
            return '₹0.00';
        }
        return `₹${amount.toLocaleString('en-IN', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
        })}`;
    };

    const renderEmptyState = () => {
        if (loading) return null;

        if (regions.length === 0) {
            return (
                <View style={styles.emptyContainer}>
                    <Ionicons name="location-outline" size={64} color="#ccc" />
                    <Text style={styles.emptyTitle}>No regions available</Text>
                    <Text style={styles.emptySubtitle}>
                        Create regions to track revenue by geographic area
                    </Text>
                </View>
            );
        }

        return null;
    };

    const renderRegionCard = (region) => {
        const hasRevenue = region.revenue && region.revenue > 0;

        return (
            <View key={region.id} style={styles.regionCard}>
                <View style={styles.regionHeader}>
                    <View style={styles.regionIconContainer}>
                        <Ionicons name="location" size={24} color="#1E88E5" />
                    </View>
                    <View style={styles.regionInfo}>
                        <Text style={styles.regionName}>{region.name}</Text>
                        {region.state && (
                            <Text style={styles.regionState}>{region.state}</Text>
                        )}
                    </View>
                </View>
                <View style={styles.revenueContainer}>
                    <Text style={[
                        styles.revenueAmount,
                        !hasRevenue && styles.noRevenue
                    ]}>
                        {formatINR(region.revenue)}
                    </Text>
                    {!hasRevenue && (
                        <Text style={styles.noRevenueLabel}>No revenue</Text>
                    )}
                </View>
            </View>
        );
    };

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#1E88E5" />
                <Text style={styles.loadingText}>Loading region revenue...</Text>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>Revenue by Region</Text>
                <Text style={styles.subtitle}>
                    View revenue breakdown across all regions
                </Text>
            </View>

            {error && (
                <View style={styles.errorContainer}>
                    <ErrorDisplay 
                        error={error}
                        onRetry={() => fetchRegionRevenue()}
                        showRetry={true}
                    />
                </View>
            )}

            <ScrollView 
                style={styles.content}
                refreshControl={
                    <RefreshControl
                        refreshing={refreshing}
                        onRefresh={() => fetchRegionRevenue(true)}
                        colors={['#1E88E5']}
                    />
                }
            >
                {renderEmptyState()}
                {regions.map(region => renderRegionCard(region))}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
    },
    loadingText: {
        marginTop: 12,
        fontSize: 14,
        color: '#666',
    },
    header: {
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
    },
    subtitle: {
        fontSize: 14,
        color: '#666',
        marginTop: 4,
    },
    errorContainer: {
        padding: 15,
    },
    content: {
        flex: 1,
        padding: 15,
    },
    emptyContainer: {
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 60,
    },
    emptyTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#666',
        marginTop: 16,
    },
    emptySubtitle: {
        fontSize: 14,
        color: '#999',
        marginTop: 8,
        textAlign: 'center',
        paddingHorizontal: 40,
    },
    regionCard: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        marginBottom: 12,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
    },
    regionHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 12,
    },
    regionIconContainer: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: '#E3F2FD',
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: 12,
    },
    regionInfo: {
        flex: 1,
    },
    regionName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
    },
    regionState: {
        fontSize: 13,
        color: '#666',
        marginTop: 2,
    },
    revenueContainer: {
        borderTopWidth: 1,
        borderTopColor: '#f0f0f0',
        paddingTop: 12,
        alignItems: 'flex-end',
    },
    revenueAmount: {
        fontSize: 22,
        fontWeight: 'bold',
        color: '#4CAF50',
    },
    noRevenue: {
        color: '#999',
    },
    noRevenueLabel: {
        fontSize: 12,
        color: '#999',
        marginTop: 4,
        fontStyle: 'italic',
    },
});

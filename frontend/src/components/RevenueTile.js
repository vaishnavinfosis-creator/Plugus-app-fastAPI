import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

/**
 * RevenueTile Component
 * 
 * Displays total revenue in a dashboard tile with INR formatting
 * Navigates to detail screen on press
 * 
 * @param {number} totalRevenue - Total revenue amount in INR
 * @param {Function} onPress - Callback when tile is pressed
 * @param {boolean} loading - Whether revenue data is loading
 * @param {string} error - Error message if revenue fetch failed
 * @param {string} label - Label to display (default: "Total Revenue")
 */
const RevenueTile = ({ 
    totalRevenue = 0, 
    onPress, 
    loading = false, 
    error = null,
    label = "Total Revenue"
}) => {
    const formatINR = (amount) => {
        if (amount === null || amount === undefined) return '₹0';
        return `₹${amount.toLocaleString('en-IN', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
        })}`;
    };

    const renderContent = () => {
        if (loading) {
            return (
                <View style={styles.centerContent}>
                    <ActivityIndicator size="large" color="#4CAF50" />
                    <Text style={styles.loadingText}>Loading...</Text>
                </View>
            );
        }

        if (error) {
            return (
                <View style={styles.centerContent}>
                    <Ionicons name="alert-circle-outline" size={32} color="#F44336" />
                    <Text style={styles.errorText}>Failed to load</Text>
                </View>
            );
        }

        return (
            <>
                <Ionicons name="cash-outline" size={32} color="#4CAF50" />
                <Text style={styles.revenueAmount}>{formatINR(totalRevenue)}</Text>
                <Text style={styles.revenueLabel}>{label}</Text>
                {onPress && (
                    <View style={styles.viewDetailsContainer}>
                        <Text style={styles.viewDetailsText}>View Details</Text>
                        <Ionicons name="chevron-forward" size={16} color="#4CAF50" />
                    </View>
                )}
            </>
        );
    };

    const TileWrapper = onPress ? TouchableOpacity : View;

    return (
        <TileWrapper 
            style={styles.container} 
            onPress={onPress}
            disabled={loading || error}
        >
            {renderContent()}
        </TileWrapper>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#E8F5E9',
        padding: 20,
        borderRadius: 12,
        alignItems: 'center',
        elevation: 2,
        minHeight: 140,
        justifyContent: 'center',
    },
    centerContent: {
        alignItems: 'center',
        justifyContent: 'center',
    },
    revenueAmount: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#2E7D32',
        marginTop: 8,
    },
    revenueLabel: {
        fontSize: 12,
        color: '#666',
        marginTop: 4,
        textAlign: 'center',
    },
    viewDetailsContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 8,
    },
    viewDetailsText: {
        fontSize: 12,
        color: '#4CAF50',
        fontWeight: '500',
        marginRight: 2,
    },
    loadingText: {
        fontSize: 12,
        color: '#666',
        marginTop: 8,
    },
    errorText: {
        fontSize: 12,
        color: '#F44336',
        marginTop: 8,
    },
});

export default RevenueTile;

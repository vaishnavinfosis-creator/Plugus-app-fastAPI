import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, RefreshControl, Image, TouchableOpacity, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import ErrorDisplay from '../../components/ErrorDisplay';
import { getStructuredError } from '../../api/client';

/**
 * VendorTransactionsScreen
 * 
 * Displays complete transaction history for a specific vendor
 * Shows datetime, amount, and screenshot for each transaction
 * Sorted by datetime descending (most recent first)
 * 
 * Requirements: 7.1, 7.2, 7.3, 7.4
 */
export default function VendorTransactionsScreen({ route, navigation }) {
    const { vendorId, vendorName } = route.params;
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState(null);
    const [selectedImage, setSelectedImage] = useState(null);

    useEffect(() => {
        fetchTransactions();
    }, [vendorId]);

    const fetchTransactions = async (isRefresh = false) => {
        if (isRefresh) {
            setRefreshing(true);
        } else {
            setLoading(true);
        }
        setError(null);

        try {
            const response = await client.get(`/admin/vendors/${vendorId}/transactions`);
            // Transactions are already sorted by datetime descending from backend
            setTransactions(response.data || []);
        } catch (err) {
            console.error('Error fetching vendor transactions:', err);
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

    const formatDateTime = (dateTimeString) => {
        if (!dateTimeString) return 'N/A';
        
        try {
            const date = new Date(dateTimeString);
            const dateStr = date.toLocaleDateString('en-IN', {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
            });
            const timeStr = date.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            });
            return `${dateStr} at ${timeStr}`;
        } catch (e) {
            return dateTimeString;
        }
    };

    const renderEmptyState = () => {
        if (loading) return null;

        if (transactions.length === 0) {
            return (
                <View style={styles.emptyContainer}>
                    <Ionicons name="receipt-outline" size={64} color="#ccc" />
                    <Text style={styles.emptyTitle}>No transactions yet</Text>
                    <Text style={styles.emptySubtitle}>
                        This vendor has no transaction history
                    </Text>
                </View>
            );
        }

        return null;
    };

    const renderTransactionCard = (transaction) => {
        return (
            <View key={transaction.transaction_id} style={styles.transactionCard}>
                <View style={styles.transactionHeader}>
                    <View style={styles.iconContainer}>
                        <Ionicons name="receipt" size={24} color="#1E88E5" />
                    </View>
                    <View style={styles.transactionInfo}>
                        <Text style={styles.transactionId}>
                            Transaction #{transaction.transaction_id}
                        </Text>
                        <Text style={styles.dateTime}>
                            {formatDateTime(transaction.datetime)}
                        </Text>
                    </View>
                </View>

                <View style={styles.amountContainer}>
                    <Text style={styles.amountLabel}>Amount</Text>
                    <Text style={styles.amountValue}>
                        {formatINR(transaction.amount)}
                    </Text>
                </View>

                {transaction.screenshot_url && (
                    <View style={styles.screenshotContainer}>
                        <Text style={styles.screenshotLabel}>Payment Screenshot</Text>
                        <TouchableOpacity 
                            onPress={() => setSelectedImage(transaction.screenshot_url)}
                            style={styles.screenshotTouchable}
                        >
                            <Image
                                source={{ uri: transaction.screenshot_url }}
                                style={styles.screenshotThumbnail}
                                resizeMode="cover"
                            />
                            <View style={styles.zoomIconOverlay}>
                                <Ionicons name="expand" size={20} color="#fff" />
                            </View>
                        </TouchableOpacity>
                    </View>
                )}

                {!transaction.screenshot_url && (
                    <View style={styles.noScreenshotContainer}>
                        <Ionicons name="image-outline" size={20} color="#999" />
                        <Text style={styles.noScreenshotText}>No screenshot available</Text>
                    </View>
                )}
            </View>
        );
    };

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#1E88E5" />
                <Text style={styles.loadingText}>Loading transactions...</Text>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>Transaction History</Text>
                <Text style={styles.subtitle}>
                    {vendorName || `Vendor #${vendorId}`}
                </Text>
            </View>

            {error && (
                <View style={styles.errorContainer}>
                    <ErrorDisplay 
                        error={error}
                        onRetry={() => fetchTransactions()}
                        showRetry={true}
                    />
                </View>
            )}

            <ScrollView 
                style={styles.content}
                refreshControl={
                    <RefreshControl
                        refreshing={refreshing}
                        onRefresh={() => fetchTransactions(true)}
                        colors={['#1E88E5']}
                    />
                }
            >
                {renderEmptyState()}
                {transactions.map(transaction => renderTransactionCard(transaction))}
            </ScrollView>

            {/* Image Zoom Modal */}
            <Modal
                visible={selectedImage !== null}
                transparent={true}
                animationType="fade"
                onRequestClose={() => setSelectedImage(null)}
            >
                <View style={styles.modalContainer}>
                    <TouchableOpacity 
                        style={styles.modalCloseArea}
                        activeOpacity={1}
                        onPress={() => setSelectedImage(null)}
                    >
                        <View style={styles.modalHeader}>
                            <TouchableOpacity 
                                style={styles.closeButton}
                                onPress={() => setSelectedImage(null)}
                            >
                                <Ionicons name="close" size={28} color="#fff" />
                            </TouchableOpacity>
                        </View>
                        {selectedImage && (
                            <Image
                                source={{ uri: selectedImage }}
                                style={styles.fullScreenImage}
                                resizeMode="contain"
                            />
                        )}
                    </TouchableOpacity>
                </View>
            </Modal>
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
    transactionCard: {
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
    transactionHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 12,
    },
    iconContainer: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: '#E3F2FD',
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: 12,
    },
    transactionInfo: {
        flex: 1,
    },
    transactionId: {
        fontSize: 15,
        fontWeight: '600',
        color: '#333',
    },
    dateTime: {
        fontSize: 13,
        color: '#666',
        marginTop: 2,
    },
    amountContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 12,
        borderTopWidth: 1,
        borderTopColor: '#f0f0f0',
        borderBottomWidth: 1,
        borderBottomColor: '#f0f0f0',
    },
    amountLabel: {
        fontSize: 14,
        color: '#666',
        fontWeight: '500',
    },
    amountValue: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#4CAF50',
    },
    screenshotContainer: {
        marginTop: 12,
    },
    screenshotLabel: {
        fontSize: 13,
        color: '#666',
        marginBottom: 8,
        fontWeight: '500',
    },
    screenshotTouchable: {
        position: 'relative',
        borderRadius: 8,
        overflow: 'hidden',
    },
    screenshotThumbnail: {
        width: '100%',
        height: 200,
        borderRadius: 8,
        backgroundColor: '#f0f0f0',
    },
    zoomIconOverlay: {
        position: 'absolute',
        top: 8,
        right: 8,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        borderRadius: 20,
        width: 36,
        height: 36,
        alignItems: 'center',
        justifyContent: 'center',
    },
    noScreenshotContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 16,
        marginTop: 8,
        backgroundColor: '#f9f9f9',
        borderRadius: 8,
    },
    noScreenshotText: {
        fontSize: 13,
        color: '#999',
        marginLeft: 8,
        fontStyle: 'italic',
    },
    modalContainer: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.95)',
    },
    modalCloseArea: {
        flex: 1,
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'flex-end',
        padding: 16,
    },
    closeButton: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        alignItems: 'center',
        justifyContent: 'center',
    },
    fullScreenImage: {
        flex: 1,
        width: '100%',
    },
});

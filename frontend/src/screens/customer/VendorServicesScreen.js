import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

export default function VendorServicesScreen({ route, navigation }) {
    const { vendor, category } = route.params;
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchServices();
    }, []);

    const fetchServices = async () => {
        try {
            const res = await client.get(`/customer/services?vendor_id=${vendor.id}`);
            setServices(res.data);
        } catch (e) {
            console.log('Error fetching services:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleBookService = (service) => {
        navigation.navigate('BookService', { service, vendor });
    };

    const formatPrice = (price) => {
        return `₹${price.toLocaleString('en-IN')}`;
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
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#333" />
                </TouchableOpacity>
                <View>
                    <Text style={styles.title}>{vendor.business_name}</Text>
                    <Text style={styles.subtitle}>{category.name}</Text>
                </View>
            </View>

            {services.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Ionicons name="construct-outline" size={60} color="#ccc" />
                    <Text style={styles.emptyText}>No services available</Text>
                </View>
            ) : (
                <FlatList
                    data={services}
                    keyExtractor={(item) => item.id.toString()}
                    contentContainerStyle={styles.list}
                    renderItem={({ item }) => (
                        <View style={styles.serviceCard}>
                            <View style={styles.serviceInfo}>
                                <Text style={styles.serviceName}>{item.name}</Text>
                                {item.description && (
                                    <Text style={styles.serviceDesc} numberOfLines={2}>
                                        {item.description}
                                    </Text>
                                )}
                                <View style={styles.priceRow}>
                                    <Text style={styles.price}>{formatPrice(item.base_price)}</Text>
                                    <View style={styles.durationBadge}>
                                        <Ionicons name="time-outline" size={14} color="#666" />
                                        <Text style={styles.duration}>{item.duration_minutes} mins</Text>
                                    </View>
                                </View>
                            </View>
                            <TouchableOpacity
                                style={styles.bookButton}
                                onPress={() => handleBookService(item)}
                            >
                                <Text style={styles.bookButtonText}>Book</Text>
                            </TouchableOpacity>
                        </View>
                    )}
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5'
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center'
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    backButton: {
        marginRight: 15
    },
    title: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333'
    },
    subtitle: {
        fontSize: 14,
        color: '#666',
        marginTop: 2
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center'
    },
    emptyText: {
        marginTop: 15,
        fontSize: 16,
        color: '#999'
    },
    list: {
        padding: 15
    },
    serviceCard: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 15,
        backgroundColor: '#fff',
        marginBottom: 10,
        borderRadius: 12,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2
    },
    serviceInfo: {
        flex: 1
    },
    serviceName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333'
    },
    serviceDesc: {
        fontSize: 13,
        color: '#666',
        marginTop: 4
    },
    priceRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 8
    },
    price: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#1E88E5'
    },
    durationBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        marginLeft: 15,
        backgroundColor: '#f0f0f0',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 12
    },
    duration: {
        fontSize: 12,
        color: '#666',
        marginLeft: 4
    },
    bookButton: {
        backgroundColor: '#1E88E5',
        paddingHorizontal: 24,
        paddingVertical: 12,
        borderRadius: 8
    },
    bookButtonText: {
        color: '#fff',
        fontWeight: '600',
        fontSize: 14
    }
});

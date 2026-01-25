import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

export default function VendorListScreen({ route, navigation }) {
    const { category } = route.params;
    const [vendors, setVendors] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchVendors();
    }, []);

    const fetchVendors = async () => {
        try {
            const res = await client.get(`/customer/vendors?category_id=${category.id}`);
            setVendors(res.data);
        } catch (e) {
            console.log('Error fetching vendors:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleVendorPress = (vendor) => {
        navigation.navigate('VendorServices', { vendor, category });
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
                <Text style={styles.title}>{category.name}</Text>
            </View>

            {vendors.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Ionicons name="storefront-outline" size={60} color="#ccc" />
                    <Text style={styles.emptyText}>No vendors available</Text>
                    <Text style={styles.emptySubtext}>Check back later for services in this category</Text>
                </View>
            ) : (
                <FlatList
                    data={vendors}
                    keyExtractor={(item) => item.id.toString()}
                    contentContainerStyle={styles.list}
                    renderItem={({ item }) => (
                        <TouchableOpacity
                            style={styles.vendorCard}
                            onPress={() => handleVendorPress(item)}
                        >
                            <View style={styles.vendorIcon}>
                                <Ionicons name="storefront" size={28} color="#1E88E5" />
                            </View>
                            <View style={styles.vendorInfo}>
                                <Text style={styles.vendorName}>{item.business_name}</Text>
                                <Text style={styles.serviceCount}>
                                    {item.service_count} service(s) available
                                </Text>
                                {item.description && (
                                    <Text style={styles.vendorDesc} numberOfLines={2}>
                                        {item.description}
                                    </Text>
                                )}
                            </View>
                            <Ionicons name="chevron-forward" size={24} color="#ccc" />
                        </TouchableOpacity>
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
        fontSize: 20,
        fontWeight: 'bold',
        color: '#333'
    },
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
        color: '#999',
        textAlign: 'center'
    },
    list: {
        padding: 15
    },
    vendorCard: {
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
    vendorIcon: {
        width: 55,
        height: 55,
        borderRadius: 27,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center'
    },
    vendorInfo: {
        flex: 1,
        marginLeft: 15
    },
    vendorName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333'
    },
    serviceCount: {
        fontSize: 14,
        color: '#1E88E5',
        marginTop: 2
    },
    vendorDesc: {
        fontSize: 13,
        color: '#999',
        marginTop: 4
    }
});

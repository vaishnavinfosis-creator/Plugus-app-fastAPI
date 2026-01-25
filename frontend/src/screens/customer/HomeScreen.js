import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity, Dimensions, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

const { width } = Dimensions.get('window');
const CARD_WIDTH = (width - 60) / 3;

// Default category icons mapping
const CATEGORY_ICONS = {
    'laundry': 'shirt',
    'car/bike service': 'car-sport',
    'mobile repair': 'phone-portrait',
    'electrician': 'flash',
    'a/c service': 'snow',
    'ac service': 'snow',
    'house help': 'home',
};

export default function HomeScreen({ navigation }) {
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchCategories();
    }, []);

    const fetchCategories = async () => {
        try {
            const res = await client.get('/customer/categories');
            // Map icons to categories
            const categoriesWithIcons = res.data.map(cat => ({
                ...cat,
                icon: cat.icon || CATEGORY_ICONS[cat.name.toLowerCase()] || null
            }));
            setCategories(categoriesWithIcons);
        } catch (e) {
            console.log('Error fetching categories:', e);
        } finally {
            setLoading(false);
        }
    };

    const renderIcon = (icon) => {
        if (!icon) return <Text style={styles.noIcon}>📦</Text>;
        return <Ionicons name={icon} size={36} color="#1E88E5" />;
    };

    const handleCategoryPress = (category) => {
        navigation.navigate('VendorList', { category });
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
                <Image
                    source={require('../../../assets/logo.png')}
                    style={styles.logo}
                    resizeMode="contain"
                />
                <View>
                    <Text style={styles.title}>Plugus</Text>
                    <Text style={styles.subtitle}>What service do you need?</Text>
                </View>
            </View>

            {categories.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Ionicons name="grid-outline" size={60} color="#ccc" />
                    <Text style={styles.emptyText}>No services available</Text>
                </View>
            ) : (
                <FlatList
                    data={categories}
                    keyExtractor={(item) => item.id.toString()}
                    numColumns={3}
                    contentContainerStyle={styles.grid}
                    renderItem={({ item }) => (
                        <TouchableOpacity
                            style={styles.card}
                            onPress={() => handleCategoryPress(item)}
                        >
                            <View style={styles.iconContainer}>
                                {renderIcon(item.icon)}
                            </View>
                            <Text style={styles.cardTitle} numberOfLines={2}>{item.name}</Text>
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
        alignItems: 'center',
        backgroundColor: '#f5f5f5'
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    logo: {
        width: 50,
        height: 50,
        marginRight: 15
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1E88E5'
    },
    subtitle: {
        fontSize: 14,
        color: '#666'
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
    grid: {
        padding: 15
    },
    card: {
        width: CARD_WIDTH,
        padding: 15,
        backgroundColor: '#fff',
        margin: 5,
        borderRadius: 12,
        elevation: 3,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        alignItems: 'center'
    },
    iconContainer: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 10
    },
    noIcon: {
        fontSize: 28
    },
    cardTitle: {
        fontSize: 12,
        fontWeight: '600',
        textAlign: 'center',
        color: '#333'
    },
});

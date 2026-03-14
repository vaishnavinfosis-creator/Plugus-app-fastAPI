import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity, Modal, TextInput, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import CategoryIcon from '../../components/CategoryIcon';

export default function CategoriesScreen() {
    const { user } = useAuthStore();
    const isSuperAdmin = user?.role === 'SUPER_ADMIN';
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [categoryName, setCategoryName] = useState('');
    const [categoryIcon, setCategoryIcon] = useState('');

    useEffect(() => {
        fetchCategories();
    }, []);

    const fetchCategories = async () => {
        try {
            const res = await client.get('/admin/categories');
            setCategories(res.data);
        } catch (e) {
            console.log('Error:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleAddCategory = async () => {
        if (!categoryName.trim()) {
            Alert.alert('Error', 'Please enter category name');
            return;
        }
        try {
            await client.post('/admin/categories', {
                name: categoryName,
                icon: categoryIcon || null
            });
            Alert.alert('Success', 'Category added');
            setShowModal(false);
            setCategoryName('');
            setCategoryIcon('');
            fetchCategories();
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to add category');
        }
    };

    const handleDeleteCategory = (categoryId) => {
        Alert.alert('Delete Category', 'Are you sure?', [
            { text: 'Cancel', style: 'cancel' },
            {
                text: 'Delete', style: 'destructive', onPress: async () => {
                    try {
                        await client.delete(`/admin/categories/${categoryId}`);
                        fetchCategories();
                    } catch (e) {
                        Alert.alert('Error', e.response?.data?.detail || 'Cannot delete category');
                    }
                }
            }
        ]);
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
                <Text style={styles.title}>Categories</Text>
                {isSuperAdmin && (
                    <TouchableOpacity
                        style={styles.addButton}
                        onPress={() => setShowModal(true)}
                    >
                        <Ionicons name="add" size={20} color="#fff" />
                        <Text style={styles.addButtonText}>Add</Text>
                    </TouchableOpacity>
                )}
            </View>

            <FlatList
                data={categories}
                keyExtractor={(item) => item.id.toString()}
                contentContainerStyle={styles.list}
                renderItem={({ item }) => (
                    <View style={styles.categoryCard}>
                        <View style={styles.categoryIcon}>
                            <CategoryIcon
                                iconName={item.icon}
                                size={24}
                                color="#1E88E5"
                            />
                        </View>
                        <View style={styles.categoryInfo}>
                            <Text style={styles.categoryName}>{item.name}</Text>
                            <Text style={styles.categoryType}>
                                {item.is_default ? 'Default' : 'Custom'}
                            </Text>
                        </View>
                        {isSuperAdmin && !item.is_default && (
                            <TouchableOpacity onPress={() => handleDeleteCategory(item.id)}>
                                <Ionicons name="trash-outline" size={22} color="#E53935" />
                            </TouchableOpacity>
                        )}
                    </View>
                )}
            />

            {/* Add Modal */}
            <Modal visible={showModal} animationType="slide" transparent>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>Add Category</Text>
                            <TouchableOpacity onPress={() => setShowModal(false)}>
                                <Ionicons name="close" size={24} color="#666" />
                            </TouchableOpacity>
                        </View>
                        <TextInput
                            style={styles.input}
                            placeholder="Category Name *"
                            value={categoryName}
                            onChangeText={setCategoryName}
                        />
                        <TextInput
                            style={styles.input}
                            placeholder="Icon Name (e.g., 'car-sport')"
                            value={categoryIcon}
                            onChangeText={setCategoryIcon}
                        />
                        <TouchableOpacity style={styles.submitButton} onPress={handleAddCategory}>
                            <Text style={styles.submitButtonText}>Add Category</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </Modal>
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
    addButton: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#1E88E5',
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 8
    },
    addButtonText: { color: '#fff', fontWeight: '600', marginLeft: 4 },
    list: { padding: 15 },
    categoryCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 12,
        marginBottom: 10,
        elevation: 1
    },
    categoryIcon: {
        width: 50,
        height: 50,
        borderRadius: 25,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center'
    },
    categoryInfo: { flex: 1, marginLeft: 15 },
    categoryName: { fontSize: 16, fontWeight: '600', color: '#333' },
    categoryType: { fontSize: 13, color: '#999', marginTop: 2 },
    modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
    modalContent: { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20 },
    modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
    modalTitle: { fontSize: 20, fontWeight: 'bold', color: '#333' },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 10,
        padding: 14,
        fontSize: 16,
        marginBottom: 15
    },
    submitButton: { backgroundColor: '#1E88E5', padding: 16, borderRadius: 10, alignItems: 'center' },
    submitButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' }
});

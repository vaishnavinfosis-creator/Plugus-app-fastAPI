import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    FlatList,
    TouchableOpacity,
    Modal,
    TextInput,
    Alert,
    ActivityIndicator
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

export default function ServicesScreen() {
    const [services, setServices] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    
    // Form state
    const [selectedCategoryId, setSelectedCategoryId] = useState(null);
    const [serviceName, setServiceName] = useState('');
    const [description, setDescription] = useState('');
    const [basePrice, setBasePrice] = useState('');
    const [durationMinutes, setDurationMinutes] = useState('60');
    const [categoryError, setCategoryError] = useState('');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [servicesRes, categoriesRes] = await Promise.all([
                client.get('/vendor/services'),
                client.get('/customer/categories')
            ]);
            setServices(servicesRes.data);
            setCategories(categoriesRes.data);
        } catch (e) {
            console.log('Error fetching data:', e);
            Alert.alert('Error', 'Failed to load data');
        } finally {
            setLoading(false);
        }
    };

    const handleAddService = () => {
        setShowModal(true);
        // Reset form
        setSelectedCategoryId(null);
        setServiceName('');
        setDescription('');
        setBasePrice('');
        setDurationMinutes('60');
        setCategoryError('');
    };

    const handleSubmit = async () => {
        // Validate category selection first
        if (!selectedCategoryId) {
            setCategoryError('Please select a category before creating a service');
            return;
        }

        // Validate other fields
        if (!serviceName.trim()) {
            Alert.alert('Error', 'Service name is required');
            return;
        }

        if (!basePrice || parseFloat(basePrice) <= 0) {
            Alert.alert('Error', 'Please enter a valid price greater than 0');
            return;
        }

        try {
            await client.post('/vendor/services', {
                category_id: selectedCategoryId,
                name: serviceName.trim(),
                description: description.trim() || null,
                base_price: parseFloat(basePrice),
                duration_minutes: parseInt(durationMinutes) || 60
            });

            Alert.alert('Success', 'Service created successfully');
            setShowModal(false);
            fetchData();
        } catch (e) {
            const errorMsg = e.response?.data?.detail || 'Failed to create service';
            Alert.alert('Error', errorMsg);
        }
    };

    const handleDeleteService = (serviceId, serviceName) => {
        Alert.alert(
            'Delete Service',
            `Are you sure you want to delete "${serviceName}"?`,
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Delete',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await client.delete(`/vendor/services/${serviceId}`);
                            fetchData();
                        } catch (e) {
                            Alert.alert('Error', e.response?.data?.detail || 'Failed to delete service');
                        }
                    }
                }
            ]
        );
    };

    const getCategoryName = (categoryId) => {
        const category = categories.find(c => c.id === categoryId);
        return category ? category.name : 'Unknown';
    };

    const renderService = ({ item }) => (
        <View style={styles.serviceCard}>
            <View style={styles.serviceHeader}>
                <View style={styles.serviceInfo}>
                    <Text style={styles.serviceName}>{item.name}</Text>
                    <Text style={styles.categoryBadge}>{getCategoryName(item.category_id)}</Text>
                </View>
                <TouchableOpacity
                    onPress={() => handleDeleteService(item.id, item.name)}
                    style={styles.deleteButton}
                >
                    <Ionicons name="trash-outline" size={20} color="#f44336" />
                </TouchableOpacity>
            </View>
            {item.description && (
                <Text style={styles.serviceDescription}>{item.description}</Text>
            )}
            <View style={styles.serviceDetails}>
                <Text style={styles.price}>₹{item.base_price}</Text>
                <Text style={styles.duration}>{item.duration_minutes} mins</Text>
            </View>
        </View>
    );

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#4CAF50" />
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>My Services</Text>
                <TouchableOpacity style={styles.addButton} onPress={handleAddService}>
                    <Ionicons name="add-circle" size={32} color="#4CAF50" />
                </TouchableOpacity>
            </View>

            {services.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Ionicons name="briefcase-outline" size={60} color="#ccc" />
                    <Text style={styles.emptyText}>No services yet</Text>
                    <Text style={styles.emptySubtext}>Add your first service to get started</Text>
                </View>
            ) : (
                <FlatList
                    data={services}
                    renderItem={renderService}
                    keyExtractor={(item) => item.id.toString()}
                    contentContainerStyle={styles.list}
                />
            )}

            {/* Add Service Modal */}
            <Modal
                visible={showModal}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setShowModal(false)}
            >
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>Add New Service</Text>
                            <TouchableOpacity onPress={() => setShowModal(false)}>
                                <Ionicons name="close" size={24} color="#666" />
                            </TouchableOpacity>
                        </View>

                        {/* Category Selection - Required First */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>
                                Category <Text style={styles.required}>*</Text>
                            </Text>
                            <Text style={styles.helperText}>Select a category before adding service details</Text>
                            <View style={styles.categoryGrid}>
                                {categories.map((category) => (
                                    <TouchableOpacity
                                        key={category.id}
                                        style={[
                                            styles.categoryChip,
                                            selectedCategoryId === category.id && styles.categoryChipSelected
                                        ]}
                                        onPress={() => {
                                            setSelectedCategoryId(category.id);
                                            setCategoryError('');
                                        }}
                                    >
                                        <Text
                                            style={[
                                                styles.categoryChipText,
                                                selectedCategoryId === category.id && styles.categoryChipTextSelected
                                            ]}
                                        >
                                            {category.name}
                                        </Text>
                                    </TouchableOpacity>
                                ))}
                            </View>
                            {categoryError ? (
                                <Text style={styles.errorText}>{categoryError}</Text>
                            ) : null}
                        </View>

                        {/* Service Details - Enabled after category selection */}
                        <View style={[styles.inputGroup, !selectedCategoryId && styles.disabledSection]}>
                            <Text style={styles.label}>
                                Service Name <Text style={styles.required}>*</Text>
                            </Text>
                            <TextInput
                                style={styles.input}
                                value={serviceName}
                                onChangeText={setServiceName}
                                placeholder="e.g., House Cleaning"
                                editable={!!selectedCategoryId}
                            />
                        </View>

                        <View style={[styles.inputGroup, !selectedCategoryId && styles.disabledSection]}>
                            <Text style={styles.label}>Description</Text>
                            <TextInput
                                style={[styles.input, styles.textArea]}
                                value={description}
                                onChangeText={setDescription}
                                placeholder="Service description"
                                multiline
                                numberOfLines={3}
                                editable={!!selectedCategoryId}
                            />
                        </View>

                        <View style={[styles.inputGroup, !selectedCategoryId && styles.disabledSection]}>
                            <Text style={styles.label}>
                                Base Price (₹) <Text style={styles.required}>*</Text>
                            </Text>
                            <TextInput
                                style={styles.input}
                                value={basePrice}
                                onChangeText={setBasePrice}
                                placeholder="0.00"
                                keyboardType="decimal-pad"
                                editable={!!selectedCategoryId}
                            />
                        </View>

                        <View style={[styles.inputGroup, !selectedCategoryId && styles.disabledSection]}>
                            <Text style={styles.label}>Duration (minutes)</Text>
                            <TextInput
                                style={styles.input}
                                value={durationMinutes}
                                onChangeText={setDurationMinutes}
                                placeholder="60"
                                keyboardType="number-pad"
                                editable={!!selectedCategoryId}
                            />
                        </View>

                        <TouchableOpacity
                            style={[styles.submitButton, !selectedCategoryId && styles.submitButtonDisabled]}
                            onPress={handleSubmit}
                            disabled={!selectedCategoryId}
                        >
                            <Text style={styles.submitButtonText}>Create Service</Text>
                        </TouchableOpacity>
                    </View>
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
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 16,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#e0e0e0',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
    },
    addButton: {
        padding: 4,
    },
    list: {
        padding: 16,
    },
    serviceCard: {
        backgroundColor: '#fff',
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.2,
        shadowRadius: 2,
    },
    serviceHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 8,
    },
    serviceInfo: {
        flex: 1,
    },
    serviceName: {
        fontSize: 18,
        fontWeight: '600',
        color: '#333',
        marginBottom: 4,
    },
    categoryBadge: {
        fontSize: 12,
        color: '#4CAF50',
        backgroundColor: '#E8F5E9',
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 4,
        alignSelf: 'flex-start',
    },
    deleteButton: {
        padding: 4,
    },
    serviceDescription: {
        fontSize: 14,
        color: '#666',
        marginBottom: 8,
    },
    serviceDetails: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    price: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#4CAF50',
    },
    duration: {
        fontSize: 14,
        color: '#666',
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 32,
    },
    emptyText: {
        fontSize: 18,
        color: '#999',
        marginTop: 16,
    },
    emptySubtext: {
        fontSize: 14,
        color: '#ccc',
        marginTop: 8,
    },
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        justifyContent: 'flex-end',
    },
    modalContent: {
        backgroundColor: '#fff',
        borderTopLeftRadius: 20,
        borderTopRightRadius: 20,
        padding: 20,
        maxHeight: '90%',
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
    },
    modalTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#333',
    },
    inputGroup: {
        marginBottom: 16,
    },
    disabledSection: {
        opacity: 0.5,
    },
    label: {
        fontSize: 14,
        fontWeight: '600',
        color: '#333',
        marginBottom: 8,
    },
    required: {
        color: '#f44336',
    },
    helperText: {
        fontSize: 12,
        color: '#666',
        marginBottom: 8,
        fontStyle: 'italic',
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        backgroundColor: '#fff',
    },
    textArea: {
        height: 80,
        textAlignVertical: 'top',
    },
    categoryGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    categoryChip: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 20,
        borderWidth: 1,
        borderColor: '#ddd',
        backgroundColor: '#fff',
    },
    categoryChipSelected: {
        backgroundColor: '#4CAF50',
        borderColor: '#4CAF50',
    },
    categoryChipText: {
        fontSize: 14,
        color: '#666',
    },
    categoryChipTextSelected: {
        color: '#fff',
        fontWeight: '600',
    },
    errorText: {
        color: '#f44336',
        fontSize: 12,
        marginTop: 4,
    },
    submitButton: {
        backgroundColor: '#4CAF50',
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
        marginTop: 8,
    },
    submitButtonDisabled: {
        backgroundColor: '#ccc',
    },
    submitButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: 'bold',
    },
});

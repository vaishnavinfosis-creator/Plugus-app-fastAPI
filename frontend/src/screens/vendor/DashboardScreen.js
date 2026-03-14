import React, { useEffect, useState } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity,
    Alert, Modal, TextInput, FlatList, ActivityIndicator
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import FormField from '../../components/FormField';

export default function DashboardScreen({ navigation }) {
    const { user } = useAuthStore();
    const [services, setServices] = useState([]);
    const [workers, setWorkers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showServiceModal, setShowServiceModal] = useState(false);
    const [showWorkerModal, setShowWorkerModal] = useState(false);

    // Service form
    const [serviceName, setServiceName] = useState('');
    const [serviceDesc, setServiceDesc] = useState('');
    const [servicePrice, setServicePrice] = useState('');
    const [serviceDuration, setServiceDuration] = useState('60');
    const [categoryId, setCategoryId] = useState('1');
    const [serviceErrors, setServiceErrors] = useState({});

    // Worker form
    const [workerEmail, setWorkerEmail] = useState('');
    const [workerPassword, setWorkerPassword] = useState('');
    const [workerName, setWorkerName] = useState('');
    const [workerErrors, setWorkerErrors] = useState({});

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [servicesRes, workersRes] = await Promise.all([
                client.get('/vendor/services'),
                client.get('/vendor/workers')
            ]);
            setServices(servicesRes.data);
            setWorkers(workersRes.data);
        } catch (e) {
            console.log('Error fetching data:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleAddService = async () => {
        // Clear previous errors
        setServiceErrors({});

        // Field-level validation
        const errors = {};
        if (!serviceName.trim()) {
            errors.serviceName = 'Service name is required';
        }
        if (!servicePrice) {
            errors.servicePrice = 'Price is required';
        } else if (isNaN(parseFloat(servicePrice)) || parseFloat(servicePrice) <= 0) {
            errors.servicePrice = 'Please enter a valid price';
        }
        if (serviceDuration && (isNaN(parseInt(serviceDuration)) || parseInt(serviceDuration) <= 0)) {
            errors.serviceDuration = 'Please enter a valid duration';
        }

        if (Object.keys(errors).length > 0) {
            setServiceErrors(errors);
            return;
        }

        try {
            await client.post('/vendor/services', {
                name: serviceName,
                description: serviceDesc,
                base_price: parseFloat(servicePrice),
                duration_minutes: parseInt(serviceDuration) || 60,
                category_id: parseInt(categoryId) || 1
            });
            Alert.alert('Success', 'Service added');
            setShowServiceModal(false);
            resetServiceForm();
            fetchData();
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to add service');
        }
    };

    const handleAddWorker = async () => {
        // Clear previous errors
        setWorkerErrors({});

        // Field-level validation
        const errors = {};
        if (!workerEmail.trim()) {
            errors.workerEmail = 'Email is required';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(workerEmail.trim())) {
            errors.workerEmail = 'Please enter a valid email address';
        }
        if (!workerPassword) {
            errors.workerPassword = 'Password is required';
        } else if (workerPassword.length < 6) {
            errors.workerPassword = 'Password must be at least 6 characters';
        }

        if (Object.keys(errors).length > 0) {
            setWorkerErrors(errors);
            return;
        }

        try {
            await client.post('/vendor/workers', {
                email: workerEmail,
                password: workerPassword,
                full_name: workerName
            });
            Alert.alert('Success', 'Worker created with login credentials');
            setShowWorkerModal(false);
            resetWorkerForm();
            fetchData();
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to add worker');
        }
    };

    const handleDeleteService = (serviceId) => {
        Alert.alert('Delete Service', 'Are you sure?', [
            { text: 'Cancel', style: 'cancel' },
            {
                text: 'Delete', style: 'destructive', onPress: async () => {
                    try {
                        await client.delete(`/vendor/services/${serviceId}`);
                        fetchData();
                    } catch (e) {
                        Alert.alert('Error', e.response?.data?.detail || 'Cannot delete service');
                    }
                }
            }
        ]);
    };

    const resetServiceForm = () => {
        setServiceName('');
        setServiceDesc('');
        setServicePrice('');
        setServiceDuration('60');
        setServiceErrors({});
    };

    const resetWorkerForm = () => {
        setWorkerEmail('');
        setWorkerPassword('');
        setWorkerName('');
        setWorkerErrors({});
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
                <Text style={styles.title}>Dashboard</Text>
                <Text style={styles.subtitle}>Welcome, Vendor!</Text>
            </View>

            <ScrollView style={styles.content}>
                {/* Quick Stats */}
                <View style={styles.statsRow}>
                    <View style={styles.statCard}>
                        <Ionicons name="construct" size={28} color="#1E88E5" />
                        <Text style={styles.statNumber}>{services.length}</Text>
                        <Text style={styles.statLabel}>Services</Text>
                    </View>
                    <View style={styles.statCard}>
                        <Ionicons name="people" size={28} color="#4CAF50" />
                        <Text style={styles.statNumber}>{workers.length}</Text>
                        <Text style={styles.statLabel}>Workers</Text>
                    </View>
                </View>

                {/* Services Section */}
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <Text style={styles.sectionTitle}>My Services</Text>
                        <TouchableOpacity
                            style={styles.addButton}
                            onPress={() => setShowServiceModal(true)}
                        >
                            <Ionicons name="add" size={20} color="#fff" />
                            <Text style={styles.addButtonText}>Add</Text>
                        </TouchableOpacity>
                    </View>

                    {services.length === 0 ? (
                        <Text style={styles.emptyText}>No services yet. Add your first service!</Text>
                    ) : (
                        services.map(service => (
                            <View key={service.id} style={styles.itemCard}>
                                <View style={styles.itemInfo}>
                                    <Text style={styles.itemName}>{service.name}</Text>
                                    <Text style={styles.itemPrice}>₹{service.base_price}</Text>
                                </View>
                                <TouchableOpacity onPress={() => handleDeleteService(service.id)}>
                                    <Ionicons name="trash-outline" size={22} color="#E53935" />
                                </TouchableOpacity>
                            </View>
                        ))
                    )}
                </View>

                {/* Workers Section */}
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <Text style={styles.sectionTitle}>My Workers</Text>
                        <TouchableOpacity
                            style={styles.addButton}
                            onPress={() => setShowWorkerModal(true)}
                        >
                            <Ionicons name="add" size={20} color="#fff" />
                            <Text style={styles.addButtonText}>Add</Text>
                        </TouchableOpacity>
                    </View>

                    {workers.length === 0 ? (
                        <Text style={styles.emptyText}>No workers yet. Create worker accounts!</Text>
                    ) : (
                        workers.map(worker => (
                            <View key={worker.id} style={styles.itemCard}>
                                <View style={styles.workerIcon}>
                                    <Ionicons name="person" size={20} color="#1E88E5" />
                                </View>
                                <View style={styles.itemInfo}>
                                    <Text style={styles.itemName}>Worker #{worker.id}</Text>
                                    <View style={[
                                        styles.statusBadge,
                                        { backgroundColor: worker.is_available ? '#E8F5E9' : '#FFEBEE' }
                                    ]}>
                                        <Text style={[
                                            styles.statusText,
                                            { color: worker.is_available ? '#2E7D32' : '#C62828' }
                                        ]}>
                                            {worker.is_available ? 'Available' : 'Busy'}
                                        </Text>
                                    </View>
                                </View>
                            </View>
                        ))
                    )}
                </View>
            </ScrollView>

            {/* Add Service Modal */}
            <Modal visible={showServiceModal} animationType="slide" transparent>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>Add Service</Text>
                            <TouchableOpacity onPress={() => setShowServiceModal(false)}>
                                <Ionicons name="close" size={24} color="#666" />
                            </TouchableOpacity>
                        </View>
                        <ScrollView>
                            <FormField
                                label="Service Name"
                                icon="briefcase-outline"
                                placeholder="Enter service name"
                                value={serviceName}
                                onChangeText={setServiceName}
                                error={serviceErrors.serviceName}
                                onClearError={() => setServiceErrors({ ...serviceErrors, serviceName: null })}
                            />
                            <FormField
                                label="Description"
                                icon="document-text-outline"
                                placeholder="Enter service description"
                                value={serviceDesc}
                                onChangeText={setServiceDesc}
                                multiline
                                numberOfLines={3}
                            />
                            <FormField
                                label="Price (₹)"
                                icon="cash-outline"
                                placeholder="Enter price"
                                value={servicePrice}
                                onChangeText={setServicePrice}
                                error={serviceErrors.servicePrice}
                                onClearError={() => setServiceErrors({ ...serviceErrors, servicePrice: null })}
                                keyboardType="numeric"
                            />
                            <FormField
                                label="Duration (minutes)"
                                icon="time-outline"
                                placeholder="Enter duration"
                                value={serviceDuration}
                                onChangeText={setServiceDuration}
                                error={serviceErrors.serviceDuration}
                                onClearError={() => setServiceErrors({ ...serviceErrors, serviceDuration: null })}
                                keyboardType="numeric"
                            />
                            <TouchableOpacity style={styles.submitButton} onPress={handleAddService}>
                                <Text style={styles.submitButtonText}>Add Service</Text>
                            </TouchableOpacity>
                        </ScrollView>
                    </View>
                </View>
            </Modal>

            {/* Add Worker Modal */}
            <Modal visible={showWorkerModal} animationType="slide" transparent>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>Add Worker</Text>
                            <TouchableOpacity onPress={() => setShowWorkerModal(false)}>
                                <Ionicons name="close" size={24} color="#666" />
                            </TouchableOpacity>
                        </View>
                        <FormField
                            label="Worker Email"
                            icon="mail-outline"
                            placeholder="Enter worker email"
                            value={workerEmail}
                            onChangeText={setWorkerEmail}
                            error={workerErrors.workerEmail}
                            onClearError={() => setWorkerErrors({ ...workerErrors, workerEmail: null })}
                            keyboardType="email-address"
                            autoCapitalize="none"
                        />
                        <FormField
                            label="Password"
                            icon="lock-closed-outline"
                            placeholder="Enter password"
                            value={workerPassword}
                            onChangeText={setWorkerPassword}
                            error={workerErrors.workerPassword}
                            onClearError={() => setWorkerErrors({ ...workerErrors, workerPassword: null })}
                            secureTextEntry
                        />
                        <FormField
                            label="Full Name (Optional)"
                            icon="person-outline"
                            placeholder="Enter full name"
                            value={workerName}
                            onChangeText={setWorkerName}
                        />
                        <TouchableOpacity style={styles.submitButton} onPress={handleAddWorker}>
                            <Text style={styles.submitButtonText}>Create Worker Account</Text>
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
    header: { padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#eee' },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    subtitle: { fontSize: 14, color: '#666', marginTop: 4 },
    content: { flex: 1, padding: 15 },
    statsRow: { flexDirection: 'row', gap: 15, marginBottom: 20 },
    statCard: {
        flex: 1,
        backgroundColor: '#fff',
        padding: 20,
        borderRadius: 12,
        alignItems: 'center',
        elevation: 2
    },
    statNumber: { fontSize: 28, fontWeight: 'bold', color: '#333', marginTop: 8 },
    statLabel: { fontSize: 14, color: '#666', marginTop: 4 },
    section: { marginBottom: 20 },
    sectionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 15
    },
    sectionTitle: { fontSize: 18, fontWeight: '600', color: '#333' },
    addButton: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#1E88E5',
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 8
    },
    addButtonText: { color: '#fff', fontWeight: '600', marginLeft: 4 },
    emptyText: { color: '#999', fontStyle: 'italic' },
    itemCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 10,
        marginBottom: 10,
        elevation: 1
    },
    itemInfo: { flex: 1 },
    itemName: { fontSize: 16, fontWeight: '500', color: '#333' },
    itemPrice: { fontSize: 14, color: '#1E88E5', marginTop: 4 },
    workerIcon: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12
    },
    statusBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, marginTop: 4, alignSelf: 'flex-start' },
    statusText: { fontSize: 12, fontWeight: '600' },
    modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
    modalContent: { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20, maxHeight: '80%' },
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

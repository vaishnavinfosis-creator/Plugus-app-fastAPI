import React, { useEffect, useState } from 'react';
import {
    View, Text, StyleSheet, FlatList, TouchableOpacity,
    Modal, TextInput, Alert, ActivityIndicator
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

export default function RegionsScreen() {
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalVisible, setModalVisible] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [selectedRegion, setSelectedRegion] = useState(null);

    // Form state
    const [name, setName] = useState('');
    const [state, setState] = useState('');
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        fetchRegions();
    }, []);

    const fetchRegions = async () => {
        try {
            setLoading(true);
            const res = await client.get('/admin/regions');
            setRegions(res.data);
        } catch (e) {
            console.log('Error fetching regions:', e);
            Alert.alert('Error', 'Failed to load regions');
        } finally {
            setLoading(false);
        }
    };

    const handleAddRegion = async () => {
        if (!name.trim() || !state.trim()) {
            Alert.alert('Error', 'Please fill all fields');
            return;
        }

        try {
            setSubmitting(true);
            await client.post('/admin/regions', {
                name: name.trim(),
                state: state.trim()
            });

            setModalVisible(false);
            resetForm();
            fetchRegions();
            Alert.alert('Success', 'Region created successfully');
        } catch (e) {
            console.log('Error adding region:', e);
            Alert.alert('Error', e.response?.data?.detail || 'Failed to create region');
        } finally {
            setSubmitting(false);
        }
    };

    const handleUpdateRegion = async () => {
        if (!name.trim() || !state.trim()) {
            Alert.alert('Error', 'Please fill all fields');
            return;
        }

        try {
            setSubmitting(true);
            await client.put(`/admin/regions/${selectedRegion.id}`, {
                name: name.trim(),
                state: state.trim()
            });

            setModalVisible(false);
            resetForm();
            fetchRegions();
            Alert.alert('Success', 'Region updated successfully');
        } catch (e) {
            console.log('Error updating region:', e);
            Alert.alert('Error', e.response?.data?.detail || 'Failed to update region');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteRegion = async (region) => {
        Alert.alert(
            'Confirm Delete',
            `Are you sure you want to delete "${region.name}"?`,
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Delete',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await client.delete(`/admin/regions/${region.id}?force=true`);
                            fetchRegions();
                            Alert.alert('Success', 'Region deleted successfully');
                        } catch (e) {
                            console.log('Error deleting region:', e);
                            const errorMsg = e.response?.data?.detail || 'Failed to delete region';
                            Alert.alert('Error', errorMsg);
                        }
                    }
                }
            ]
        );
    };

    const openEditModal = (region) => {
        setSelectedRegion(region);
        setName(region.name);
        setState(region.state);
        setEditMode(true);
        setModalVisible(true);
    };

    const openAddModal = () => {
        resetForm();
        setEditMode(false);
        setModalVisible(true);
    };

    const resetForm = () => {
        setName('');
        setState('');
        setSelectedRegion(null);
        setEditMode(false);
    };

    const renderRegionItem = ({ item }) => {
        return (
            <View style={styles.card}>
                <View style={styles.cardContent}>
                    <View style={styles.iconContainer}>
                        <Ionicons name="location" size={24} color="#1E88E5" />
                    </View>
                    <View style={styles.info}>
                        <Text style={styles.regionName}>{item.name}</Text>
                        <Text style={styles.stateName}>{item.state}</Text>
                        {item.admin_id && (
                            <View style={styles.badge}>
                                <Ionicons name="person" size={12} color="#4CAF50" />
                                <Text style={styles.badgeText}>Admin Assigned</Text>
                            </View>
                        )}
                    </View>
                </View>
                <View style={styles.actions}>
                    <TouchableOpacity
                        onPress={() => openEditModal(item)}
                        style={styles.actionBtn}
                    >
                        <Ionicons name="create-outline" size={20} color="#1E88E5" />
                    </TouchableOpacity>
                    <TouchableOpacity
                        onPress={() => handleDeleteRegion(item)}
                        style={styles.actionBtn}
                    >
                        <Ionicons name="trash-outline" size={20} color="#FF5252" />
                    </TouchableOpacity>
                </View>
            </View>
        );
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
                <View>
                    <Text style={styles.title}>Regions</Text>
                    <Text style={styles.subtitle}>{regions.length} total regions</Text>
                </View>
                <TouchableOpacity
                    style={styles.addBtn}
                    onPress={openAddModal}
                >
                    <Ionicons name="add" size={24} color="#fff" />
                    <Text style={styles.addBtnText}>Add New</Text>
                </TouchableOpacity>
            </View>

            <FlatList
                data={regions}
                renderItem={renderRegionItem}
                keyExtractor={item => item.id.toString()}
                contentContainerStyle={styles.list}
                ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                        <Ionicons name="location-outline" size={64} color="#ccc" />
                        <Text style={styles.emptyText}>No regions found</Text>
                        <Text style={styles.emptySubtext}>Create your first region to get started</Text>
                    </View>
                }
            />

            <Modal
                visible={modalVisible}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setModalVisible(false)}
            >
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>
                                {editMode ? 'Edit Region' : 'Add New Region'}
                            </Text>
                            <TouchableOpacity onPress={() => setModalVisible(false)}>
                                <Ionicons name="close" size={24} color="#666" />
                            </TouchableOpacity>
                        </View>

                        <View style={styles.form}>
                            <View style={styles.inputGroup}>
                                <Text style={styles.label}>Region Name</Text>
                                <TextInput
                                    style={styles.input}
                                    value={name}
                                    onChangeText={setName}
                                    placeholder="e.g., Mumbai, Delhi, Bangalore"
                                    autoCapitalize="words"
                                />
                            </View>

                            <View style={styles.inputGroup}>
                                <Text style={styles.label}>State</Text>
                                <TextInput
                                    style={styles.input}
                                    value={state}
                                    onChangeText={setState}
                                    placeholder="e.g., Maharashtra, Delhi, Karnataka"
                                    autoCapitalize="words"
                                />
                            </View>

                            <TouchableOpacity
                                style={[styles.submitBtn, submitting && styles.disabledBtn]}
                                onPress={editMode ? handleUpdateRegion : handleAddRegion}
                                disabled={submitting}
                            >
                                {submitting ? (
                                    <ActivityIndicator color="#fff" />
                                ) : (
                                    <Text style={styles.submitBtnText}>
                                        {editMode ? 'Update Region' : 'Create Region'}
                                    </Text>
                                )}
                            </TouchableOpacity>
                        </View>
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
        padding: 20,
        backgroundColor: '#fff',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    subtitle: { fontSize: 14, color: '#666', marginTop: 4 },
    addBtn: {
        backgroundColor: '#1E88E5',
        flexDirection: 'row',
        alignItems: 'center',
        padding: 8,
        paddingHorizontal: 12,
        borderRadius: 8
    },
    addBtnText: { color: '#fff', fontWeight: '600', marginLeft: 4 },
    list: { padding: 15 },
    card: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 15,
        marginBottom: 10,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4
    },
    cardContent: { flexDirection: 'row', alignItems: 'center', flex: 1 },
    iconContainer: {
        width: 48,
        height: 48,
        borderRadius: 24,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12
    },
    info: { flex: 1 },
    regionName: { fontSize: 16, fontWeight: '600', color: '#333' },
    stateName: { fontSize: 14, color: '#666', marginTop: 2 },
    badge: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#E8F5E9',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 12,
        marginTop: 6,
        alignSelf: 'flex-start'
    },
    badgeText: { fontSize: 12, color: '#4CAF50', marginLeft: 4, fontWeight: '500' },
    actions: { flexDirection: 'row', gap: 8 },
    actionBtn: { padding: 8 },
    emptyContainer: {
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 60
    },
    emptyText: { 
        fontSize: 18, 
        fontWeight: '600', 
        color: '#999', 
        marginTop: 16 
    },
    emptySubtext: { 
        fontSize: 14, 
        color: '#bbb', 
        marginTop: 8 
    },

    // Modal
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'flex-end'
    },
    modalContent: {
        backgroundColor: '#fff',
        borderTopLeftRadius: 20,
        borderTopRightRadius: 20,
        padding: 20,
        maxHeight: '70%'
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20
    },
    modalTitle: { fontSize: 20, fontWeight: 'bold', color: '#333' },
    form: { gap: 20 },
    inputGroup: { gap: 8 },
    label: { fontSize: 14, fontWeight: '600', color: '#666' },
    input: {
        backgroundColor: '#f5f5f5',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        borderWidth: 1,
        borderColor: '#eee'
    },
    submitBtn: {
        backgroundColor: '#1E88E5',
        padding: 15,
        borderRadius: 10,
        alignItems: 'center',
        marginTop: 10
    },
    disabledBtn: { opacity: 0.7 },
    submitBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' }
});

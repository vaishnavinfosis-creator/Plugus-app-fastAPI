import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity, RefreshControl, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

const STATUS_COLORS = {
    'WORKER_ASSIGNED': { bg: '#E3F2FD', text: '#1565C0' },
    'IN_PROGRESS': { bg: '#FFF3E0', text: '#E65100' },
    'COMPLETED': { bg: '#E8F5E9', text: '#2E7D32' },
    'PAYMENT_UPLOADED': { bg: '#C8E6C9', text: '#1B5E20' }
};

export default function TasksScreen({ navigation }) {
    const [activeTab, setActiveTab] = useState('active');
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        fetchTasks();
    }, [activeTab]);

    const fetchTasks = async () => {
        try {
            const endpoint = activeTab === 'active' ? '/worker/tasks/active' : '/worker/tasks/completed';
            const res = await client.get(endpoint);
            setTasks(res.data);
        } catch (e) {
            console.log('Error:', e);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchTasks();
    }, [activeTab]);

    const handleStartTask = async (taskId) => {
        try {
            await client.put(`/worker/tasks/${taskId}/start`);
            Alert.alert('Success', 'Task started');
            fetchTasks();
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to start task');
        }
    };

    const formatDate = (dateStr) => {
        return new Date(dateStr).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
        });
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
                <Text style={styles.title}>My Tasks</Text>
            </View>

            {/* Tabs */}
            <View style={styles.tabs}>
                <TouchableOpacity
                    style={[styles.tab, activeTab === 'active' && styles.tabActive]}
                    onPress={() => { setActiveTab('active'); setLoading(true); }}
                >
                    <Text style={[styles.tabText, activeTab === 'active' && styles.tabTextActive]}>
                        Active
                    </Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={[styles.tab, activeTab === 'completed' && styles.tabActive]}
                    onPress={() => { setActiveTab('completed'); setLoading(true); }}
                >
                    <Text style={[styles.tabText, activeTab === 'completed' && styles.tabTextActive]}>
                        Completed
                    </Text>
                </TouchableOpacity>
            </View>

            {tasks.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Ionicons name="clipboard-outline" size={70} color="#ccc" />
                    <Text style={styles.emptyText}>
                        {activeTab === 'active' ? 'No active tasks' : 'No completed tasks'}
                    </Text>
                </View>
            ) : (
                <FlatList
                    data={tasks}
                    keyExtractor={(item) => item.id.toString()}
                    contentContainerStyle={styles.list}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#1E88E5']} />
                    }
                    renderItem={({ item }) => (
                        <TouchableOpacity
                            style={styles.taskCard}
                            onPress={() => navigation.navigate('TaskDetail', { taskId: item.id })}
                        >
                            <View style={styles.taskHeader}>
                                <Text style={styles.taskId}>Task #{item.id}</Text>
                                <View style={[
                                    styles.statusBadge,
                                    { backgroundColor: STATUS_COLORS[item.status]?.bg || '#eee' }
                                ]}>
                                    <Text style={[
                                        styles.statusText,
                                        { color: STATUS_COLORS[item.status]?.text || '#666' }
                                    ]}>
                                        {item.status.replace(/_/g, ' ')}
                                    </Text>
                                </View>
                            </View>

                            <View style={styles.taskDetails}>
                                <View style={styles.detailRow}>
                                    <Ionicons name="calendar-outline" size={16} color="#666" />
                                    <Text style={styles.detailText}>{formatDate(item.scheduled_time)}</Text>
                                </View>
                            </View>

                            <View style={styles.taskFooter}>
                                <Text style={styles.priceText}>₹{item.total_cost}</Text>

                                {item.status === 'WORKER_ASSIGNED' && (
                                    <TouchableOpacity
                                        style={styles.startButton}
                                        onPress={() => handleStartTask(item.id)}
                                    >
                                        <Ionicons name="play" size={16} color="#fff" />
                                        <Text style={styles.startButtonText}>Start</Text>
                                    </TouchableOpacity>
                                )}

                                {item.status === 'IN_PROGRESS' && (
                                    <TouchableOpacity
                                        style={[styles.startButton, { backgroundColor: '#4CAF50' }]}
                                        onPress={() => navigation.navigate('TaskDetail', { taskId: item.id })}
                                    >
                                        <Ionicons name="checkmark" size={16} color="#fff" />
                                        <Text style={styles.startButtonText}>Complete</Text>
                                    </TouchableOpacity>
                                )}
                            </View>
                        </TouchableOpacity>
                    )}
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    header: { padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#eee' },
    title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
    tabs: { flexDirection: 'row', backgroundColor: '#fff', padding: 10 },
    tab: { flex: 1, paddingVertical: 12, alignItems: 'center', borderRadius: 8 },
    tabActive: { backgroundColor: '#E3F2FD' },
    tabText: { fontWeight: '600', color: '#666' },
    tabTextActive: { color: '#1E88E5' },
    emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    emptyText: { marginTop: 15, fontSize: 16, color: '#999' },
    list: { padding: 15 },
    taskCard: { backgroundColor: '#fff', borderRadius: 12, padding: 15, marginBottom: 12, elevation: 2 },
    taskHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
    taskId: { fontSize: 16, fontWeight: '600', color: '#333' },
    statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
    statusText: { fontSize: 11, fontWeight: '600' },
    taskDetails: { marginBottom: 12 },
    detailRow: { flexDirection: 'row', alignItems: 'center' },
    detailText: { marginLeft: 8, color: '#666' },
    taskFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderTopWidth: 1, borderTopColor: '#f0f0f0', paddingTop: 12 },
    priceText: { fontSize: 18, fontWeight: 'bold', color: '#1E88E5' },
    startButton: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#1E88E5',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 8
    },
    startButtonText: { color: '#fff', fontWeight: '600', marginLeft: 4 }
});

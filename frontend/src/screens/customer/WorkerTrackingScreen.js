import React, { useEffect, useState, useRef } from 'react';
import { View, Text, StyleSheet, Dimensions, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import WebSocketService from '../../services/websocket';
import { useAuthStore } from '../../store/authStore';

const { width, height } = Dimensions.get('window');

// Note: For real Google Maps, install:
// npx expo install react-native-maps
// And use: import MapView, { Marker } from 'react-native-maps';

export default function WorkerTrackingScreen({ route, navigation }) {
    const { bookingId, workerName } = route.params;
    const { token } = useAuthStore();
    const [workerLocation, setWorkerLocation] = useState(null);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef(null);

    useEffect(() => {
        // Connect to worker tracking WebSocket
        wsRef.current = WebSocketService.connectWorkerTracking(
            bookingId,
            token,
            (data) => {
                if (data.type === 'worker_location') {
                    setWorkerLocation({
                        lat: data.latitude,
                        lng: data.longitude
                    });
                }
            },
            (error) => {
                console.log('WebSocket error:', error);
                setConnected(false);
            }
        );
        setConnected(true);

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [bookingId, token]);

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#333" />
                </TouchableOpacity>
                <View>
                    <Text style={styles.headerTitle}>Track Worker</Text>
                    <Text style={styles.headerSubtitle}>{workerName || 'Worker'}</Text>
                </View>
            </View>

            {/* Map Placeholder - Replace with react-native-maps */}
            <View style={styles.mapContainer}>
                <View style={styles.mapPlaceholder}>
                    <Ionicons name="map" size={60} color="#1E88E5" />
                    <Text style={styles.mapPlaceholderText}>
                        {workerLocation
                            ? `Worker at: ${workerLocation.lat.toFixed(4)}, ${workerLocation.lng.toFixed(4)}`
                            : 'Waiting for worker location...'}
                    </Text>
                    <Text style={styles.mapNote}>
                        Install react-native-maps for actual map display
                    </Text>
                </View>

                {/* Worker Marker Preview */}
                {workerLocation && (
                    <View style={styles.workerMarker}>
                        <View style={styles.markerDot} />
                        <Text style={styles.markerLabel}>Worker Location</Text>
                    </View>
                )}
            </View>

            {/* Connection Status */}
            <View style={styles.statusBar}>
                <View style={[styles.statusDot, { backgroundColor: connected ? '#4CAF50' : '#E53935' }]} />
                <Text style={styles.statusText}>
                    {connected ? 'Live tracking active' : 'Connecting...'}
                </Text>
            </View>

            {/* Info Card */}
            <View style={styles.infoCard}>
                <View style={styles.infoRow}>
                    <Ionicons name="navigate" size={20} color="#1E88E5" />
                    <Text style={styles.infoText}>Worker is on the way</Text>
                </View>
                <TouchableOpacity style={styles.callButton}>
                    <Ionicons name="call" size={20} color="#fff" />
                    <Text style={styles.callButtonText}>Call Worker</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    backButton: { marginRight: 15 },
    headerTitle: { fontSize: 18, fontWeight: 'bold', color: '#333' },
    headerSubtitle: { fontSize: 14, color: '#666' },
    mapContainer: {
        flex: 1,
        backgroundColor: '#E3F2FD',
        justifyContent: 'center',
        alignItems: 'center'
    },
    mapPlaceholder: {
        alignItems: 'center'
    },
    mapPlaceholderText: {
        marginTop: 15,
        fontSize: 16,
        color: '#1E88E5',
        textAlign: 'center'
    },
    mapNote: {
        marginTop: 10,
        fontSize: 12,
        color: '#666',
        textAlign: 'center'
    },
    workerMarker: {
        position: 'absolute',
        top: height * 0.3,
        alignItems: 'center'
    },
    markerDot: {
        width: 20,
        height: 20,
        borderRadius: 10,
        backgroundColor: '#1E88E5',
        borderWidth: 3,
        borderColor: '#fff',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.3,
        shadowRadius: 3
    },
    markerLabel: {
        marginTop: 5,
        fontSize: 12,
        color: '#333',
        backgroundColor: '#fff',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 12
    },
    statusBar: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 10,
        backgroundColor: '#fff'
    },
    statusDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        marginRight: 8
    },
    statusText: { color: '#666', fontSize: 14 },
    infoCard: {
        backgroundColor: '#fff',
        padding: 20,
        borderTopWidth: 1,
        borderTopColor: '#eee'
    },
    infoRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 15
    },
    infoText: { marginLeft: 10, color: '#333', fontSize: 16 },
    callButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#4CAF50',
        padding: 14,
        borderRadius: 10
    },
    callButtonText: { color: '#fff', fontWeight: '600', marginLeft: 8 }
});

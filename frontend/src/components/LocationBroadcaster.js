import React, { useEffect, useState, useRef } from 'react';
import { View, Text, StyleSheet, Switch, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import WebSocketService from '../../services/websocket';
import { useAuthStore } from '../../store/authStore';

export default function LocationBroadcaster({ bookingId, isActive }) {
    const { token } = useAuthStore();
    const [broadcasting, setBroadcasting] = useState(false);
    const [currentLocation, setCurrentLocation] = useState(null);
    const wsRef = useRef(null);
    const watchRef = useRef(null);

    useEffect(() => {
        if (isActive && broadcasting) {
            startBroadcasting();
        } else {
            stopBroadcasting();
        }

        return () => stopBroadcasting();
    }, [isActive, broadcasting]);

    const startBroadcasting = async () => {
        try {
            // Request location permission
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Permission Denied', 'Location permission required for tracking');
                setBroadcasting(false);
                return;
            }

            // Connect WebSocket
            wsRef.current = WebSocketService.connectWorkerLocation(
                token,
                () => console.log('Worker location connected'),
                (error) => console.log('WebSocket error:', error)
            );

            // Start watching location
            watchRef.current = await Location.watchPositionAsync(
                {
                    accuracy: Location.Accuracy.High,
                    distanceInterval: 10, // Update every 10 meters
                    timeInterval: 5000    // Or every 5 seconds
                },
                (location) => {
                    const { latitude, longitude } = location.coords;
                    setCurrentLocation({ lat: latitude, lng: longitude });

                    // Send to WebSocket
                    if (wsRef.current) {
                        wsRef.current.sendLocation(bookingId, latitude, longitude);
                    }
                }
            );
        } catch (error) {
            console.log('Location error:', error);
            Alert.alert('Error', 'Failed to start location tracking');
            setBroadcasting(false);
        }
    };

    const stopBroadcasting = () => {
        if (watchRef.current) {
            watchRef.current.remove();
            watchRef.current = null;
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setCurrentLocation(null);
    };

    const toggleBroadcasting = (value) => {
        setBroadcasting(value);
    };

    if (!isActive) return null;

    return (
        <View style={styles.container}>
            <View style={styles.row}>
                <View style={styles.iconContainer}>
                    <Ionicons
                        name={broadcasting ? 'location' : 'location-outline'}
                        size={24}
                        color={broadcasting ? '#4CAF50' : '#666'}
                    />
                </View>
                <View style={styles.info}>
                    <Text style={styles.title}>Live Location</Text>
                    <Text style={styles.subtitle}>
                        {broadcasting
                            ? currentLocation
                                ? `Sharing: ${currentLocation.lat.toFixed(4)}, ${currentLocation.lng.toFixed(4)}`
                                : 'Getting location...'
                            : 'Share your location with customer'
                        }
                    </Text>
                </View>
                <Switch
                    value={broadcasting}
                    onValueChange={toggleBroadcasting}
                    trackColor={{ false: '#ddd', true: '#A5D6A7' }}
                    thumbColor={broadcasting ? '#4CAF50' : '#999'}
                />
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 15,
        marginBottom: 15,
        elevation: 2
    },
    row: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    iconContainer: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: '#E8F5E9',
        justifyContent: 'center',
        alignItems: 'center'
    },
    info: {
        flex: 1,
        marginLeft: 12
    },
    title: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333'
    },
    subtitle: {
        fontSize: 13,
        color: '#666',
        marginTop: 2
    }
});

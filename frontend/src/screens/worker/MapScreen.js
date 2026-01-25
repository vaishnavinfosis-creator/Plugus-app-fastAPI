import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function MapScreen() {
    return (
        <View style={styles.container}>
            <Ionicons name="map-outline" size={80} color="#ccc" />
            <Text style={styles.title}>Map View</Text>
            <Text style={styles.subtitle}>Directions to customer location will appear here</Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
        padding: 20
    },
    title: {
        fontSize: 20,
        fontWeight: 'bold',
        marginTop: 20,
        color: '#333'
    },
    subtitle: {
        fontSize: 14,
        color: '#666',
        marginTop: 10,
        textAlign: 'center'
    }
});

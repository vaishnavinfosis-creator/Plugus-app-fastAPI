import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ScrollView, Switch } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

export default function AddPhoneScreen({ navigation, route }) {
    const { onSuccess } = route.params || {};
    const [number, setNumber] = useState('');
    const [isDefault, setIsDefault] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSave = async () => {
        if (!number.trim()) {
            Alert.alert('Validation Error', 'Please enter a phone number');
            return;
        }

        setLoading(true);
        try {
            await client.post('/customer/phones', {
                number: number.trim(),
                is_default: isDefault
            });

            Alert.alert('Success', 'Phone number added successfully', [
                {
                    text: 'OK',
                    onPress: () => {
                        if (onSuccess) onSuccess();
                        navigation.goBack();
                    }
                }
            ]);
        } catch (error) {
            console.error('Error adding phone:', error);
            Alert.alert('Error', error.response?.data?.detail || 'Failed to add phone number');
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()}>
                    <Ionicons name="arrow-back" size={24} color="#333" />
                </TouchableOpacity>
                <Text style={styles.title}>Add Phone Number</Text>
                <View style={{ width: 24 }} />
            </View>

            <ScrollView style={styles.content}>
                <View style={styles.form}>
                    <Text style={styles.label}>Phone Number *</Text>
                    <TextInput
                        style={styles.input}
                        value={number}
                        onChangeText={setNumber}
                        placeholder="e.g., +1234567890"
                        keyboardType="phone-pad"
                        maxLength={20}
                    />
                    <Text style={styles.hint}>
                        Enter 10-15 digits. You can include country code with +
                    </Text>

                    <View style={styles.switchRow}>
                        <Text style={styles.label}>Set as default</Text>
                        <Switch
                            value={isDefault}
                            onValueChange={setIsDefault}
                            trackColor={{ false: '#ccc', true: '#90CAF9' }}
                            thumbColor={isDefault ? '#1E88E5' : '#f4f3f4'}
                        />
                    </View>

                    <TouchableOpacity
                        style={[styles.saveButton, loading && styles.saveButtonDisabled]}
                        onPress={handleSave}
                        disabled={loading}
                    >
                        <Text style={styles.saveButtonText}>
                            {loading ? 'Saving...' : 'Save Phone Number'}
                        </Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    title: { fontSize: 20, fontWeight: 'bold', color: '#333' },
    content: { flex: 1 },
    form: {
        backgroundColor: '#fff',
        margin: 15,
        padding: 20,
        borderRadius: 12,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2
    },
    label: {
        fontSize: 14,
        fontWeight: '600',
        color: '#333',
        marginBottom: 8,
        marginTop: 12
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        backgroundColor: '#fff'
    },
    hint: {
        fontSize: 12,
        color: '#999',
        marginTop: 4,
        fontStyle: 'italic'
    },
    switchRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 12
    },
    saveButton: {
        backgroundColor: '#1E88E5',
        padding: 15,
        borderRadius: 8,
        alignItems: 'center',
        marginTop: 20
    },
    saveButtonDisabled: {
        backgroundColor: '#90CAF9'
    },
    saveButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600'
    }
});

import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ScrollView, Switch } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';

export default function EditAddressScreen({ navigation, route }) {
    const { address, onSuccess } = route.params || {};
    const [label, setLabel] = useState(address?.label || '');
    const [addressText, setAddressText] = useState(address?.address_text || '');
    const [isDefault, setIsDefault] = useState(address?.is_default || false);
    const [loading, setLoading] = useState(false);

    const handleSave = async () => {
        if (!label.trim()) {
            Alert.alert('Validation Error', 'Please enter an address label (e.g., Home, Work)');
            return;
        }

        if (!addressText.trim()) {
            Alert.alert('Validation Error', 'Please enter the address');
            return;
        }

        setLoading(true);
        try {
            await client.put(`/customer/addresses/${address.id}`, {
                label: label.trim(),
                address_text: addressText.trim(),
                is_default: isDefault,
                latitude: address.latitude,
                longitude: address.longitude
            });

            Alert.alert('Success', 'Address updated successfully', [
                {
                    text: 'OK',
                    onPress: () => {
                        if (onSuccess) onSuccess();
                        navigation.goBack();
                    }
                }
            ]);
        } catch (error) {
            console.error('Error updating address:', error);
            Alert.alert('Error', error.response?.data?.detail || 'Failed to update address');
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
                <Text style={styles.title}>Edit Address</Text>
                <View style={{ width: 24 }} />
            </View>

            <ScrollView style={styles.content}>
                <View style={styles.form}>
                    <Text style={styles.label}>Label *</Text>
                    <TextInput
                        style={styles.input}
                        value={label}
                        onChangeText={setLabel}
                        placeholder="e.g., Home, Work, Office"
                        maxLength={50}
                    />

                    <Text style={styles.label}>Address *</Text>
                    <TextInput
                        style={[styles.input, styles.textArea]}
                        value={addressText}
                        onChangeText={setAddressText}
                        placeholder="Enter full address"
                        multiline
                        numberOfLines={4}
                        textAlignVertical="top"
                    />

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
                            {loading ? 'Saving...' : 'Save Changes'}
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
    textArea: {
        minHeight: 100
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

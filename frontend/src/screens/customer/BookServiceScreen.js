import React, { useState, useEffect } from 'react';
import {
    View, Text, StyleSheet, TouchableOpacity, ScrollView,
    Alert, ActivityIndicator, TextInput
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';
import client from '../../api/client';

export default function BookServiceScreen({ route, navigation }) {
    const { service, vendor } = route.params;
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [addresses, setAddresses] = useState([]);
    const [phones, setPhones] = useState([]);
    const [selectedAddress, setSelectedAddress] = useState(null);
    const [selectedPhone, setSelectedPhone] = useState(null);
    const [scheduledTime, setScheduledTime] = useState(new Date(Date.now() + 3600000)); // 1 hour from now
    const [showDatePicker, setShowDatePicker] = useState(false);
    const [showTimePicker, setShowTimePicker] = useState(false);
    const [newAddress, setNewAddress] = useState('');
    const [newPhone, setNewPhone] = useState('');
    const [showAddAddress, setShowAddAddress] = useState(false);
    const [showAddPhone, setShowAddPhone] = useState(false);

    useEffect(() => {
        fetchUserData();
    }, []);

    const fetchUserData = async () => {
        try {
            const [addressRes, phoneRes] = await Promise.all([
                client.get('/customer/addresses'),
                client.get('/customer/phones')
            ]);
            setAddresses(addressRes.data);
            setPhones(phoneRes.data);

            // Auto-select defaults
            const defaultAddr = addressRes.data.find(a => a.is_default) || addressRes.data[0];
            const defaultPhone = phoneRes.data.find(p => p.is_default) || phoneRes.data[0];
            setSelectedAddress(defaultAddr?.id || null);
            setSelectedPhone(defaultPhone?.id || null);
        } catch (e) {
            console.log('Error fetching user data:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleAddAddress = async () => {
        if (!newAddress.trim()) return;
        try {
            const res = await client.post('/customer/addresses', {
                label: 'Address',
                address_text: newAddress.trim(),
                is_default: addresses.length === 0
            });
            setAddresses([...addresses, res.data]);
            setSelectedAddress(res.data.id);
            setNewAddress('');
            setShowAddAddress(false);
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to add address');
        }
    };

    const handleAddPhone = async () => {
        if (!newPhone.trim()) return;
        try {
            const res = await client.post('/customer/phones', {
                number: newPhone.trim(),
                is_default: phones.length === 0
            });
            setPhones([...phones, res.data]);
            setSelectedPhone(res.data.id);
            setNewPhone('');
            setShowAddPhone(false);
        } catch (e) {
            Alert.alert('Error', e.response?.data?.detail || 'Failed to add phone');
        }
    };

    const handleDateChange = (event, date) => {
        setShowDatePicker(false);
        if (date) {
            const newDateTime = new Date(scheduledTime);
            newDateTime.setFullYear(date.getFullYear(), date.getMonth(), date.getDate());
            setScheduledTime(newDateTime);
        }
    };

    const handleTimeChange = (event, date) => {
        setShowTimePicker(false);
        if (date) {
            const newDateTime = new Date(scheduledTime);
            newDateTime.setHours(date.getHours(), date.getMinutes());
            setScheduledTime(newDateTime);
        }
    };

    const handleBookNow = async () => {
        if (!selectedAddress) {
            Alert.alert('Error', 'Please select or add an address');
            return;
        }
        if (!selectedPhone) {
            Alert.alert('Error', 'Please select or add a phone number');
            return;
        }

        setSubmitting(true);
        try {
            const res = await client.post('/customer/bookings', {
                service_id: service.id,
                scheduled_time: scheduledTime.toISOString(),
                address_id: selectedAddress,
                phone_id: selectedPhone
            });

            Alert.alert(
                'Booking Created!',
                `Your booking has been placed. The vendor will confirm soon.`,
                [{ text: 'OK', onPress: () => navigation.navigate('Bookings') }]
            );
        } catch (e) {
            Alert.alert('Booking Failed', e.response?.data?.detail || 'Something went wrong');
        } finally {
            setSubmitting(false);
        }
    };

    const formatPrice = (price) => `₹${price.toLocaleString('en-IN')}`;

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
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#333" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Book Service</Text>
            </View>

            <ScrollView style={styles.content}>
                {/* Service Summary */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Service Details</Text>
                    <Text style={styles.serviceName}>{service.name}</Text>
                    <Text style={styles.vendorName}>{vendor.business_name}</Text>
                    <View style={styles.priceRow}>
                        <Text style={styles.price}>{formatPrice(service.base_price)}</Text>
                        <Text style={styles.duration}>{service.duration_minutes} mins</Text>
                    </View>
                </View>

                {/* Schedule */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Schedule</Text>
                    <View style={styles.scheduleRow}>
                        <TouchableOpacity
                            style={styles.scheduleButton}
                            onPress={() => setShowDatePicker(true)}
                        >
                            <Ionicons name="calendar-outline" size={20} color="#1E88E5" />
                            <Text style={styles.scheduleText}>
                                {scheduledTime.toLocaleDateString()}
                            </Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={styles.scheduleButton}
                            onPress={() => setShowTimePicker(true)}
                        >
                            <Ionicons name="time-outline" size={20} color="#1E88E5" />
                            <Text style={styles.scheduleText}>
                                {scheduledTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </Text>
                        </TouchableOpacity>
                    </View>
                </View>

                {/* Address */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardTitle}>Address</Text>
                        {addresses.length < 2 && !showAddAddress && (
                            <TouchableOpacity onPress={() => setShowAddAddress(true)}>
                                <Ionicons name="add-circle" size={24} color="#1E88E5" />
                            </TouchableOpacity>
                        )}
                    </View>

                    {showAddAddress && (
                        <View style={styles.addForm}>
                            <TextInput
                                style={styles.input}
                                placeholder="Enter address"
                                value={newAddress}
                                onChangeText={setNewAddress}
                                multiline
                            />
                            <View style={styles.addFormButtons}>
                                <TouchableOpacity
                                    style={styles.cancelBtn}
                                    onPress={() => { setShowAddAddress(false); setNewAddress(''); }}
                                >
                                    <Text style={styles.cancelBtnText}>Cancel</Text>
                                </TouchableOpacity>
                                <TouchableOpacity style={styles.addBtn} onPress={handleAddAddress}>
                                    <Text style={styles.addBtnText}>Add</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    )}

                    {addresses.map(addr => (
                        <TouchableOpacity
                            key={addr.id}
                            style={[
                                styles.optionItem,
                                selectedAddress === addr.id && styles.optionItemSelected
                            ]}
                            onPress={() => setSelectedAddress(addr.id)}
                        >
                            <Ionicons
                                name={selectedAddress === addr.id ? 'radio-button-on' : 'radio-button-off'}
                                size={20}
                                color="#1E88E5"
                            />
                            <Text style={styles.optionText}>{addr.address_text}</Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* Phone */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardTitle}>Phone</Text>
                        {phones.length < 2 && !showAddPhone && (
                            <TouchableOpacity onPress={() => setShowAddPhone(true)}>
                                <Ionicons name="add-circle" size={24} color="#1E88E5" />
                            </TouchableOpacity>
                        )}
                    </View>

                    {showAddPhone && (
                        <View style={styles.addForm}>
                            <TextInput
                                style={styles.input}
                                placeholder="Enter phone number"
                                value={newPhone}
                                onChangeText={setNewPhone}
                                keyboardType="phone-pad"
                            />
                            <View style={styles.addFormButtons}>
                                <TouchableOpacity
                                    style={styles.cancelBtn}
                                    onPress={() => { setShowAddPhone(false); setNewPhone(''); }}
                                >
                                    <Text style={styles.cancelBtnText}>Cancel</Text>
                                </TouchableOpacity>
                                <TouchableOpacity style={styles.addBtn} onPress={handleAddPhone}>
                                    <Text style={styles.addBtnText}>Add</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    )}

                    {phones.map(phone => (
                        <TouchableOpacity
                            key={phone.id}
                            style={[
                                styles.optionItem,
                                selectedPhone === phone.id && styles.optionItemSelected
                            ]}
                            onPress={() => setSelectedPhone(phone.id)}
                        >
                            <Ionicons
                                name={selectedPhone === phone.id ? 'radio-button-on' : 'radio-button-off'}
                                size={20}
                                color="#1E88E5"
                            />
                            <Text style={styles.optionText}>{phone.number}</Text>
                        </TouchableOpacity>
                    ))}
                </View>
            </ScrollView>

            {/* Book Button */}
            <View style={styles.footer}>
                <View style={styles.totalRow}>
                    <Text style={styles.totalLabel}>Total</Text>
                    <Text style={styles.totalPrice}>{formatPrice(service.base_price)}</Text>
                </View>
                <TouchableOpacity
                    style={[styles.bookButton, submitting && styles.bookButtonDisabled]}
                    onPress={handleBookNow}
                    disabled={submitting}
                >
                    <Text style={styles.bookButtonText}>
                        {submitting ? 'Booking...' : 'Confirm Booking'}
                    </Text>
                </TouchableOpacity>
            </View>

            {showDatePicker && (
                <DateTimePicker
                    value={scheduledTime}
                    mode="date"
                    minimumDate={new Date()}
                    onChange={handleDateChange}
                />
            )}
            {showTimePicker && (
                <DateTimePicker
                    value={scheduledTime}
                    mode="time"
                    onChange={handleTimeChange}
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    backButton: { marginRight: 15 },
    headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#333' },
    content: { flex: 1, padding: 15 },
    card: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 15,
        marginBottom: 15,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 10
    },
    cardTitle: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 10 },
    serviceName: { fontSize: 18, fontWeight: 'bold', color: '#1E88E5' },
    vendorName: { fontSize: 14, color: '#666', marginTop: 4 },
    priceRow: { flexDirection: 'row', alignItems: 'center', marginTop: 10 },
    price: { fontSize: 20, fontWeight: 'bold', color: '#333' },
    duration: { fontSize: 14, color: '#999', marginLeft: 15 },
    scheduleRow: { flexDirection: 'row', gap: 10 },
    scheduleButton: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#E3F2FD',
        padding: 12,
        borderRadius: 8
    },
    scheduleText: { marginLeft: 8, color: '#1E88E5', fontWeight: '500' },
    addForm: { marginBottom: 10 },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 14
    },
    addFormButtons: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 10, gap: 10 },
    cancelBtn: { padding: 10 },
    cancelBtnText: { color: '#999' },
    addBtn: { backgroundColor: '#1E88E5', paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8 },
    addBtnText: { color: '#fff', fontWeight: '600' },
    optionItem: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 12,
        borderRadius: 8,
        marginBottom: 8,
        backgroundColor: '#f9f9f9'
    },
    optionItemSelected: { backgroundColor: '#E3F2FD' },
    optionText: { marginLeft: 10, flex: 1, color: '#333' },
    footer: {
        backgroundColor: '#fff',
        padding: 20,
        borderTopWidth: 1,
        borderTopColor: '#eee'
    },
    totalRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 15 },
    totalLabel: { fontSize: 16, color: '#666' },
    totalPrice: { fontSize: 24, fontWeight: 'bold', color: '#1E88E5' },
    bookButton: {
        backgroundColor: '#1E88E5',
        padding: 16,
        borderRadius: 12,
        alignItems: 'center'
    },
    bookButtonDisabled: { backgroundColor: '#90CAF9' },
    bookButtonText: { color: '#fff', fontSize: 18, fontWeight: '600' }
});

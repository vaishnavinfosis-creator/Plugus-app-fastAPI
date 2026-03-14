import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import client from '../../api/client';
import FormField from '../../components/FormField';
import ErrorDisplay from '../../components/ErrorDisplay';
import { getStructuredError } from '../../api/client';

export default function CreateComplaintScreen({ navigation, route }) {
    const { bookingId } = route.params || {};
    const [bookings, setBookings] = useState([]);
    const [selectedBooking, setSelectedBooking] = useState(bookingId || null);
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [fieldErrors, setFieldErrors] = useState({});

    useEffect(() => {
        fetchBookings();
    }, []);

    const fetchBookings = async () => {
        try {
            const res = await client.get('/customer/bookings');
            // Filter bookings that can have complaints (completed or in progress)
            const eligibleBookings = res.data.filter(b => 
                ['COMPLETED', 'PAYMENT_UPLOADED', 'IN_PROGRESS'].includes(b.status)
            );
            setBookings(eligibleBookings);
        } catch (e) {
            setError(getStructuredError(e));
        } finally {
            setLoading(false);
        }
    };

    const validateForm = () => {
        const errors = {};
        
        if (!selectedBooking) {
            errors.booking = 'Please select a booking';
        }
        
        if (!description.trim()) {
            errors.description = 'Please describe your complaint';
        } else if (description.trim().length < 10) {
            errors.description = 'Description must be at least 10 characters';
        }
        
        setFieldErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleSubmit = async () => {
        if (!validateForm()) {
            return;
        }

        setSubmitting(true);
        setError(null);

        try {
            await client.post('/complaints', {
                booking_id: selectedBooking,
                description: description.trim()
            });

            Alert.alert(
                'Success',
                'Your complaint has been submitted successfully. We will review it shortly.',
                [
                    {
                        text: 'OK',
                        onPress: () => navigation.goBack()
                    }
                ]
            );
        } catch (e) {
            const structuredError = getStructuredError(e);
            
            // Handle validation errors
            if (e.response?.data?.detail && Array.isArray(e.response.data.detail)) {
                const errors = {};
                e.response.data.detail.forEach(err => {
                    if (err.loc && err.loc.length > 1) {
                        errors[err.loc[1]] = err.msg;
                    }
                });
                setFieldErrors(errors);
            } else {
                setError(structuredError);
            }
        } finally {
            setSubmitting(false);
        }
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
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
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#333" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>File a Complaint</Text>
            </View>

            <ScrollView style={styles.content}>
                {error && (
                    <ErrorDisplay error={error} onDismiss={() => setError(null)} />
                )}

                {bookings.length === 0 ? (
                    <View style={styles.noBookingsContainer}>
                        <Ionicons name="alert-circle-outline" size={60} color="#ccc" />
                        <Text style={styles.noBookingsText}>No eligible bookings</Text>
                        <Text style={styles.noBookingsSubtext}>
                            You can only file complaints for completed or in-progress bookings
                        </Text>
                    </View>
                ) : (
                    <>
                        <Text style={styles.sectionTitle}>Select Booking</Text>
                        {fieldErrors.booking && (
                            <ErrorDisplay error={{ message: fieldErrors.booking }} fieldMode />
                        )}
                        
                        {bookings.map((booking) => (
                            <TouchableOpacity
                                key={booking.id}
                                style={[
                                    styles.bookingCard,
                                    selectedBooking === booking.id && styles.bookingCardSelected
                                ]}
                                onPress={() => {
                                    setSelectedBooking(booking.id);
                                    setFieldErrors({ ...fieldErrors, booking: null });
                                }}
                            >
                                <View style={styles.bookingHeader}>
                                    <View style={styles.radioButton}>
                                        {selectedBooking === booking.id && (
                                            <View style={styles.radioButtonInner} />
                                        )}
                                    </View>
                                    <View style={styles.bookingInfo}>
                                        <Text style={styles.bookingId}>Booking #{booking.id}</Text>
                                        <Text style={styles.bookingDate}>{formatDate(booking.scheduled_time)}</Text>
                                    </View>
                                </View>
                            </TouchableOpacity>
                        ))}

                        <FormField
                            label="Describe your complaint"
                            icon="chatbox-outline"
                            value={description}
                            onChangeText={setDescription}
                            error={fieldErrors.description}
                            onClearError={() => setFieldErrors({ ...fieldErrors, description: null })}
                            placeholder="Please provide details about your complaint..."
                            multiline
                            numberOfLines={6}
                        />

                        <TouchableOpacity
                            style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
                            onPress={handleSubmit}
                            disabled={submitting}
                        >
                            {submitting ? (
                                <ActivityIndicator color="#fff" />
                            ) : (
                                <>
                                    <Ionicons name="send" size={20} color="#fff" />
                                    <Text style={styles.submitButtonText}>Submit Complaint</Text>
                                </>
                            )}
                        </TouchableOpacity>
                    </>
                )}
            </ScrollView>
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
    sectionTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
        marginBottom: 12,
        marginTop: 10
    },
    noBookingsContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 40,
        marginTop: 60
    },
    noBookingsText: {
        marginTop: 15,
        fontSize: 18,
        fontWeight: '600',
        color: '#666'
    },
    noBookingsSubtext: {
        marginTop: 8,
        fontSize: 14,
        color: '#999',
        textAlign: 'center'
    },
    bookingCard: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 15,
        marginBottom: 10,
        borderWidth: 2,
        borderColor: '#eee'
    },
    bookingCardSelected: {
        borderColor: '#1E88E5',
        backgroundColor: '#E3F2FD'
    },
    bookingHeader: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    radioButton: {
        width: 24,
        height: 24,
        borderRadius: 12,
        borderWidth: 2,
        borderColor: '#1E88E5',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12
    },
    radioButtonInner: {
        width: 12,
        height: 12,
        borderRadius: 6,
        backgroundColor: '#1E88E5'
    },
    bookingInfo: { flex: 1 },
    bookingId: { fontSize: 16, fontWeight: '600', color: '#333' },
    bookingDate: { fontSize: 13, color: '#666', marginTop: 2 },
    submitButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#1E88E5',
        padding: 16,
        borderRadius: 12,
        marginTop: 20,
        marginBottom: 30
    },
    submitButtonDisabled: {
        backgroundColor: '#90CAF9'
    },
    submitButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
        marginLeft: 8
    }
});

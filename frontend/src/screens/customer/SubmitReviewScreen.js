import React, { useState } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    StyleSheet,
    ScrollView,
    Alert,
    ActivityIndicator
} from 'react-native';
import client from '../../api/client';

const SubmitReviewScreen = ({ route, navigation }) => {
    const { bookingId } = route.params;
    
    const [rating, setRating] = useState(0);
    const [comment, setComment] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async () => {
        // Validate rating
        if (rating === 0) {
            Alert.alert('Error', 'Please select a rating');
            return;
        }

        // Validate comment length
        if (comment.length > 500) {
            Alert.alert('Error', 'Comment must not exceed 500 characters');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            await client.post(`/bookings/${bookingId}/review`, {
                booking_id: bookingId,
                rating,
                comment: comment.trim() || null
            });

            Alert.alert(
                'Success',
                'Thank you for your review!',
                [
                    {
                        text: 'OK',
                        onPress: () => navigation.goBack()
                    }
                ]
            );
        } catch (err) {
            const errorMessage = err.response?.data?.detail || 'Failed to submit review';
            setError(errorMessage);
            Alert.alert('Error', errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const renderStars = () => {
        const stars = [];
        for (let i = 1; i <= 5; i++) {
            stars.push(
                <TouchableOpacity
                    key={i}
                    onPress={() => setRating(i)}
                    style={styles.starButton}
                >
                    <Text style={[
                        styles.star,
                        i <= rating && styles.starFilled
                    ]}>
                        ★
                    </Text>
                </TouchableOpacity>
            );
        }
        return stars;
    };

    return (
        <ScrollView style={styles.container}>
            <View style={styles.content}>
                <Text style={styles.title}>Rate Your Experience</Text>
                
                {/* Star Rating */}
                <View style={styles.ratingContainer}>
                    <Text style={styles.label}>Rating *</Text>
                    <View style={styles.starsRow}>
                        {renderStars()}
                    </View>
                    {rating > 0 && (
                        <Text style={styles.ratingText}>
                            {rating} {rating === 1 ? 'star' : 'stars'}
                        </Text>
                    )}
                </View>

                {/* Comment */}
                <View style={styles.commentContainer}>
                    <Text style={styles.label}>
                        Comment (Optional)
                    </Text>
                    <TextInput
                        style={styles.commentInput}
                        placeholder="Share your experience..."
                        value={comment}
                        onChangeText={setComment}
                        multiline
                        numberOfLines={6}
                        maxLength={500}
                        textAlignVertical="top"
                    />
                    <Text style={styles.characterCount}>
                        {comment.length}/500 characters
                    </Text>
                </View>

                {/* Error Message */}
                {error && (
                    <View style={styles.errorContainer}>
                        <Text style={styles.errorText}>{error}</Text>
                    </View>
                )}

                {/* Submit Button */}
                <TouchableOpacity
                    style={[
                        styles.submitButton,
                        (loading || rating === 0) && styles.submitButtonDisabled
                    ]}
                    onPress={handleSubmit}
                    disabled={loading || rating === 0}
                >
                    {loading ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.submitButtonText}>Submit Review</Text>
                    )}
                </TouchableOpacity>

                {/* Cancel Button */}
                <TouchableOpacity
                    style={styles.cancelButton}
                    onPress={() => navigation.goBack()}
                    disabled={loading}
                >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    content: {
        padding: 20,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 30,
        textAlign: 'center',
    },
    ratingContainer: {
        marginBottom: 30,
        alignItems: 'center',
    },
    label: {
        fontSize: 16,
        fontWeight: '600',
        marginBottom: 10,
    },
    starsRow: {
        flexDirection: 'row',
        justifyContent: 'center',
        marginVertical: 10,
    },
    starButton: {
        padding: 5,
    },
    star: {
        fontSize: 40,
        color: '#ddd',
    },
    starFilled: {
        color: '#FFD700',
    },
    ratingText: {
        fontSize: 14,
        color: '#666',
        marginTop: 5,
    },
    commentContainer: {
        marginBottom: 20,
    },
    commentInput: {
        backgroundColor: '#fff',
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        minHeight: 120,
    },
    characterCount: {
        fontSize: 12,
        color: '#666',
        textAlign: 'right',
        marginTop: 5,
    },
    errorContainer: {
        backgroundColor: '#ffebee',
        padding: 12,
        borderRadius: 8,
        marginBottom: 20,
    },
    errorText: {
        color: '#c62828',
        fontSize: 14,
    },
    submitButton: {
        backgroundColor: '#007AFF',
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
        marginBottom: 10,
    },
    submitButtonDisabled: {
        backgroundColor: '#ccc',
    },
    submitButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    },
    cancelButton: {
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
    },
    cancelButtonText: {
        color: '#666',
        fontSize: 16,
    },
});

export default SubmitReviewScreen;

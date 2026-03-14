import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    ScrollView,
    StyleSheet,
    ActivityIndicator,
    TouchableOpacity,
    Alert
} from 'react-native';
import client from '../../api/client';

const ServiceDetailScreen = ({ route, navigation }) => {
    const { serviceId } = route.params;
    
    const [service, setService] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [averageRating, setAverageRating] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadServiceDetails();
    }, [serviceId]);

    const loadServiceDetails = async () => {
        setLoading(true);
        setError(null);

        try {
            // Load service details, reviews, and average rating in parallel
            const [serviceRes, reviewsRes, ratingRes] = await Promise.all([
                client.get(`/customer/services/${serviceId}`),
                client.get(`/services/${serviceId}/reviews`),
                client.get(`/services/${serviceId}/average-rating`)
            ]);

            setService(serviceRes.data);
            setReviews(reviewsRes.data);
            setAverageRating(ratingRes.data);
        } catch (err) {
            const errorMessage = err.response?.data?.detail || 'Failed to load service details';
            setError(errorMessage);
            Alert.alert('Error', errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const renderStars = (rating) => {
        const stars = [];
        for (let i = 1; i <= 5; i++) {
            stars.push(
                <Text
                    key={i}
                    style={[
                        styles.star,
                        i <= rating && styles.starFilled
                    ]}
                >
                    ★
                </Text>
            );
        }
        return stars;
    };

    const renderReview = (review) => (
        <View key={review.id} style={styles.reviewCard}>
            <View style={styles.reviewHeader}>
                <View style={styles.starsRow}>
                    {renderStars(review.rating)}
                </View>
                <Text style={styles.reviewDate}>
                    {new Date(review.created_at).toLocaleDateString()}
                </Text>
            </View>
            {review.comment && (
                <Text style={styles.reviewComment}>{review.comment}</Text>
            )}
        </View>
    );

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#007AFF" />
            </View>
        );
    }

    if (error || !service) {
        return (
            <View style={styles.centerContainer}>
                <Text style={styles.errorText}>{error || 'Service not found'}</Text>
                <TouchableOpacity
                    style={styles.retryButton}
                    onPress={loadServiceDetails}
                >
                    <Text style={styles.retryButtonText}>Retry</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <ScrollView style={styles.container}>
            {/* Service Details */}
            <View style={styles.serviceCard}>
                <Text style={styles.serviceName}>{service.name}</Text>
                {service.description && (
                    <Text style={styles.serviceDescription}>{service.description}</Text>
                )}
                <View style={styles.serviceInfo}>
                    <Text style={styles.price}>${service.base_price}</Text>
                    <Text style={styles.duration}>{service.duration_minutes} min</Text>
                </View>
            </View>

            {/* Average Rating Section */}
            {averageRating && averageRating.review_count > 0 && (
                <View style={styles.ratingSection}>
                    <Text style={styles.sectionTitle}>Customer Reviews</Text>
                    <View style={styles.averageRatingContainer}>
                        <Text style={styles.averageRatingNumber}>
                            {averageRating.average_rating.toFixed(1)}
                        </Text>
                        <View>
                            <View style={styles.starsRow}>
                                {renderStars(Math.round(averageRating.average_rating))}
                            </View>
                            <Text style={styles.reviewCount}>
                                Based on {averageRating.review_count} {averageRating.review_count === 1 ? 'review' : 'reviews'}
                            </Text>
                        </View>
                    </View>
                </View>
            )}

            {/* Reviews List */}
            {reviews.length > 0 ? (
                <View style={styles.reviewsSection}>
                    <Text style={styles.sectionTitle}>
                        All Reviews ({reviews.length})
                    </Text>
                    {reviews.map(renderReview)}
                </View>
            ) : (
                <View style={styles.noReviewsContainer}>
                    <Text style={styles.noReviewsText}>
                        No reviews yet. Be the first to review this service!
                    </Text>
                </View>
            )}

            {/* Book Service Button */}
            <TouchableOpacity
                style={styles.bookButton}
                onPress={() => navigation.navigate('BookService', { serviceId })}
            >
                <Text style={styles.bookButtonText}>Book This Service</Text>
            </TouchableOpacity>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    serviceCard: {
        backgroundColor: '#fff',
        padding: 20,
        marginBottom: 10,
    },
    serviceName: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 10,
    },
    serviceDescription: {
        fontSize: 16,
        color: '#666',
        marginBottom: 15,
        lineHeight: 22,
    },
    serviceInfo: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    price: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#007AFF',
    },
    duration: {
        fontSize: 16,
        color: '#666',
    },
    ratingSection: {
        backgroundColor: '#fff',
        padding: 20,
        marginBottom: 10,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 15,
    },
    averageRatingContainer: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    averageRatingNumber: {
        fontSize: 48,
        fontWeight: 'bold',
        marginRight: 20,
        color: '#007AFF',
    },
    starsRow: {
        flexDirection: 'row',
        marginBottom: 5,
    },
    star: {
        fontSize: 20,
        color: '#ddd',
        marginRight: 2,
    },
    starFilled: {
        color: '#FFD700',
    },
    reviewCount: {
        fontSize: 14,
        color: '#666',
    },
    reviewsSection: {
        backgroundColor: '#fff',
        padding: 20,
        marginBottom: 10,
    },
    reviewCard: {
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
        paddingVertical: 15,
    },
    reviewHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    reviewDate: {
        fontSize: 12,
        color: '#999',
    },
    reviewComment: {
        fontSize: 14,
        color: '#333',
        lineHeight: 20,
    },
    noReviewsContainer: {
        backgroundColor: '#fff',
        padding: 40,
        alignItems: 'center',
        marginBottom: 10,
    },
    noReviewsText: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
    },
    bookButton: {
        backgroundColor: '#007AFF',
        padding: 16,
        margin: 20,
        borderRadius: 8,
        alignItems: 'center',
    },
    bookButtonText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: '600',
    },
    errorText: {
        fontSize: 16,
        color: '#c62828',
        textAlign: 'center',
        marginBottom: 20,
    },
    retryButton: {
        backgroundColor: '#007AFF',
        padding: 12,
        paddingHorizontal: 30,
        borderRadius: 8,
    },
    retryButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    },
});

export default ServiceDetailScreen;

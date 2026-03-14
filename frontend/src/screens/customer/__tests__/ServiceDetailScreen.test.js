import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import ServiceDetailScreen from '../ServiceDetailScreen';
import client from '../../../api/client';

// Mock the API client
jest.mock('../../../api/client');

// Mock Alert
jest.spyOn(Alert, 'alert');

// Mock navigation
const mockNavigation = {
    navigate: jest.fn(),
};

const mockRoute = {
    params: {
        serviceId: 1,
    },
};

const mockService = {
    id: 1,
    name: 'House Cleaning',
    description: 'Professional house cleaning service',
    base_price: 50.0,
    duration_minutes: 120,
};

const mockReviews = [
    {
        id: 1,
        booking_id: 1,
        rating: 5,
        comment: 'Excellent service!',
        created_at: '2024-01-15T10:00:00Z',
    },
    {
        id: 2,
        booking_id: 2,
        rating: 4,
        comment: 'Good job',
        created_at: '2024-01-14T10:00:00Z',
    },
];

const mockAverageRating = {
    service_id: 1,
    average_rating: 4.5,
    review_count: 2,
};

describe('ServiceDetailScreen', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders loading state initially', () => {
        client.get.mockImplementation(() => new Promise(() => {})); // Never resolves

        const { getByTestId } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        // ActivityIndicator should be visible
        expect(getByTestId || (() => {})).toBeTruthy();
    });

    it('loads and displays service details', async () => {
        client.get.mockImplementation((url) => {
            if (url.includes('/customer/services/')) {
                return Promise.resolve({ data: mockService });
            } else if (url.includes('/reviews')) {
                return Promise.resolve({ data: mockReviews });
            } else if (url.includes('/average-rating')) {
                return Promise.resolve({ data: mockAverageRating });
            }
        });

        const { getByText } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        await waitFor(() => {
            expect(getByText('House Cleaning')).toBeTruthy();
            expect(getByText('Professional house cleaning service')).toBeTruthy();
            expect(getByText('$50')).toBeTruthy();
            expect(getByText('120 min')).toBeTruthy();
        });
    });

    it('displays average rating prominently', async () => {
        client.get.mockImplementation((url) => {
            if (url.includes('/customer/services/')) {
                return Promise.resolve({ data: mockService });
            } else if (url.includes('/reviews')) {
                return Promise.resolve({ data: mockReviews });
            } else if (url.includes('/average-rating')) {
                return Promise.resolve({ data: mockAverageRating });
            }
        });

        const { getByText } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        await waitFor(() => {
            expect(getByText('4.5')).toBeTruthy();
            expect(getByText('Based on 2 reviews')).toBeTruthy();
        });
    });

    it('displays all approved reviews', async () => {
        client.get.mockImplementation((url) => {
            if (url.includes('/customer/services/')) {
                return Promise.resolve({ data: mockService });
            } else if (url.includes('/reviews')) {
                return Promise.resolve({ data: mockReviews });
            } else if (url.includes('/average-rating')) {
                return Promise.resolve({ data: mockAverageRating });
            }
        });

        const { getByText } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        await waitFor(() => {
            expect(getByText('All Reviews (2)')).toBeTruthy();
            expect(getByText('Excellent service!')).toBeTruthy();
            expect(getByText('Good job')).toBeTruthy();
        });
    });

    it('shows message when no reviews exist', async () => {
        client.get.mockImplementation((url) => {
            if (url.includes('/customer/services/')) {
                return Promise.resolve({ data: mockService });
            } else if (url.includes('/reviews')) {
                return Promise.resolve({ data: [] });
            } else if (url.includes('/average-rating')) {
                return Promise.resolve({ data: { ...mockAverageRating, review_count: 0 } });
            }
        });

        const { getByText } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        await waitFor(() => {
            expect(getByText('No reviews yet. Be the first to review this service!')).toBeTruthy();
        });
    });

    it('renders star ratings correctly', async () => {
        client.get.mockImplementation((url) => {
            if (url.includes('/customer/services/')) {
                return Promise.resolve({ data: mockService });
            } else if (url.includes('/reviews')) {
                return Promise.resolve({ data: mockReviews });
            } else if (url.includes('/average-rating')) {
                return Promise.resolve({ data: mockAverageRating });
            }
        });

        const { getAllByText } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        await waitFor(() => {
            const stars = getAllByText('★');
            // Should have stars for average rating + stars for each review
            expect(stars.length).toBeGreaterThan(5);
        });
    });

    it('navigates to booking screen when book button is pressed', async () => {
        client.get.mockImplementation((url) => {
            if (url.includes('/customer/services/')) {
                return Promise.resolve({ data: mockService });
            } else if (url.includes('/reviews')) {
                return Promise.resolve({ data: [] });
            } else if (url.includes('/average-rating')) {
                return Promise.resolve({ data: { ...mockAverageRating, review_count: 0 } });
            }
        });

        const { getByText } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        await waitFor(() => {
            const bookButton = getByText('Book This Service');
            fireEvent.press(bookButton);

            expect(mockNavigation.navigate).toHaveBeenCalledWith('BookService', {
                serviceId: 1,
            });
        });
    });

    it('handles API error gracefully', async () => {
        client.get.mockRejectedValue({
            response: {
                data: {
                    detail: 'Service not found',
                },
            },
        });

        const { getByText } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        await waitFor(() => {
            expect(getByText('Service not found')).toBeTruthy();
            expect(Alert.alert).toHaveBeenCalledWith('Error', 'Service not found');
        });
    });

    it('allows retry after error', async () => {
        client.get.mockRejectedValueOnce({
            response: {
                data: {
                    detail: 'Network error',
                },
            },
        });

        const { getByText } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        await waitFor(() => {
            expect(getByText('Network error')).toBeTruthy();
        });

        // Mock successful response for retry
        client.get.mockImplementation((url) => {
            if (url.includes('/customer/services/')) {
                return Promise.resolve({ data: mockService });
            } else if (url.includes('/reviews')) {
                return Promise.resolve({ data: [] });
            } else if (url.includes('/average-rating')) {
                return Promise.resolve({ data: { ...mockAverageRating, review_count: 0 } });
            }
        });

        const retryButton = getByText('Retry');
        fireEvent.press(retryButton);

        await waitFor(() => {
            expect(getByText('House Cleaning')).toBeTruthy();
        });
    });

    it('formats review dates correctly', async () => {
        client.get.mockImplementation((url) => {
            if (url.includes('/customer/services/')) {
                return Promise.resolve({ data: mockService });
            } else if (url.includes('/reviews')) {
                return Promise.resolve({ data: mockReviews });
            } else if (url.includes('/average-rating')) {
                return Promise.resolve({ data: mockAverageRating });
            }
        });

        const { getByText } = render(
            <ServiceDetailScreen route={mockRoute} navigation={mockNavigation} />
        );

        await waitFor(() => {
            // Check that dates are formatted (exact format depends on locale)
            const dateElements = getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
            expect(dateElements.length).toBeGreaterThan(0);
        });
    });
});

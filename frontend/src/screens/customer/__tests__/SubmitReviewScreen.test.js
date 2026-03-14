import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import SubmitReviewScreen from '../SubmitReviewScreen';
import client from '../../../api/client';

// Mock the API client
jest.mock('../../../api/client');

// Mock Alert
jest.spyOn(Alert, 'alert');

// Mock navigation
const mockNavigation = {
    goBack: jest.fn(),
};

const mockRoute = {
    params: {
        bookingId: 1,
    },
};

describe('SubmitReviewScreen', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders correctly', () => {
        const { getByText, getByPlaceholderText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        expect(getByText('Rate Your Experience')).toBeTruthy();
        expect(getByText('Rating *')).toBeTruthy();
        expect(getByText('Comment (Optional)')).toBeTruthy();
        expect(getByPlaceholderText('Share your experience...')).toBeTruthy();
        expect(getByText('Submit Review')).toBeTruthy();
    });

    it('displays 5 stars for rating', () => {
        const { getAllByText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        const stars = getAllByText('★');
        expect(stars).toHaveLength(5);
    });

    it('updates rating when star is clicked', () => {
        const { getAllByText, getByText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        const stars = getAllByText('★');
        fireEvent.press(stars[3]); // Click 4th star

        expect(getByText('4 stars')).toBeTruthy();
    });

    it('updates comment text', () => {
        const { getByPlaceholderText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        const commentInput = getByPlaceholderText('Share your experience...');
        fireEvent.changeText(commentInput, 'Great service!');

        expect(commentInput.props.value).toBe('Great service!');
    });

    it('shows character count', () => {
        const { getByPlaceholderText, getByText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        const commentInput = getByPlaceholderText('Share your experience...');
        fireEvent.changeText(commentInput, 'Test comment');

        expect(getByText('12/500 characters')).toBeTruthy();
    });

    it('shows error when submitting without rating', () => {
        const { getByText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        const submitButton = getByText('Submit Review');
        fireEvent.press(submitButton);

        expect(Alert.alert).toHaveBeenCalledWith('Error', 'Please select a rating');
    });

    it('submits review successfully', async () => {
        client.post.mockResolvedValueOnce({ data: { id: 1 } });

        const { getAllByText, getByText, getByPlaceholderText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        // Set rating
        const stars = getAllByText('★');
        fireEvent.press(stars[4]); // 5 stars

        // Set comment
        const commentInput = getByPlaceholderText('Share your experience...');
        fireEvent.changeText(commentInput, 'Excellent service!');

        // Submit
        const submitButton = getByText('Submit Review');
        fireEvent.press(submitButton);

        await waitFor(() => {
            expect(client.post).toHaveBeenCalledWith('/bookings/1/review', {
                booking_id: 1,
                rating: 5,
                comment: 'Excellent service!'
            });
        });

        expect(Alert.alert).toHaveBeenCalledWith(
            'Success',
            'Thank you for your review!',
            expect.any(Array)
        );
    });

    it('handles API error', async () => {
        client.post.mockRejectedValueOnce({
            response: {
                data: {
                    detail: 'Review already exists for this booking'
                }
            }
        });

        const { getAllByText, getByText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        // Set rating
        const stars = getAllByText('★');
        fireEvent.press(stars[2]); // 3 stars

        // Submit
        const submitButton = getByText('Submit Review');
        fireEvent.press(submitButton);

        await waitFor(() => {
            expect(Alert.alert).toHaveBeenCalledWith(
                'Error',
                'Review already exists for this booking'
            );
        });
    });

    it('validates comment length', () => {
        const { getByPlaceholderText, getByText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        const commentInput = getByPlaceholderText('Share your experience...');
        const longComment = 'a'.repeat(501);
        fireEvent.changeText(commentInput, longComment);

        const stars = getAllByText('★');
        fireEvent.press(stars[4]);

        const submitButton = getByText('Submit Review');
        fireEvent.press(submitButton);

        expect(Alert.alert).toHaveBeenCalledWith(
            'Error',
            'Comment must not exceed 500 characters'
        );
    });

    it('navigates back on cancel', () => {
        const { getByText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        const cancelButton = getByText('Cancel');
        fireEvent.press(cancelButton);

        expect(mockNavigation.goBack).toHaveBeenCalled();
    });

    it('disables submit button while loading', async () => {
        client.post.mockImplementation(() => new Promise(() => {})); // Never resolves

        const { getAllByText, getByText } = render(
            <SubmitReviewScreen route={mockRoute} navigation={mockNavigation} />
        );

        // Set rating
        const stars = getAllByText('★');
        fireEvent.press(stars[4]);

        // Submit
        const submitButton = getByText('Submit Review');
        fireEvent.press(submitButton);

        await waitFor(() => {
            expect(submitButton.props.accessibilityState.disabled).toBe(true);
        });
    });
});

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import RegisterScreen from '../RegisterScreen';
import client from '../../../api/client';

jest.mock('../../../api/client');
jest.mock('../../../store/authStore', () => ({
    useAuthStore: () => ({
        setToken: jest.fn()
    })
}));

describe('RegisterScreen - Vendor Region Selection', () => {
    const mockNavigation = { goBack: jest.fn() };
    const mockRegions = [
        { id: 1, name: 'North Region' },
        { id: 2, name: 'South Region' },
        { id: 3, name: 'East Region' }
    ];

    beforeEach(() => {
        jest.clearAllMocks();
        client.get.mockResolvedValue({ data: mockRegions });
    });

    test('should display region selection when vendor role is selected', async () => {
        const { getByText, queryByText } = render(<RegisterScreen navigation={mockNavigation} />);

        // Initially, region selection should not be visible (customer is default)
        expect(queryByText('Select Region *')).toBeNull();

        // Switch to vendor role
        const vendorButton = getByText('Vendor');
        fireEvent.press(vendorButton);

        // Wait for regions to load
        await waitFor(() => {
            expect(client.get).toHaveBeenCalledWith('/admin/regions');
        });

        // Region selection should now be visible
        await waitFor(() => {
            expect(getByText('Select Region *')).toBeTruthy();
        });
    });

    test('should load and display available regions for vendor registration', async () => {
        const { getByText } = render(<RegisterScreen navigation={mockNavigation} />);

        // Switch to vendor role
        fireEvent.press(getByText('Vendor'));

        // Wait for regions to load and be displayed
        await waitFor(() => {
            expect(getByText('North Region')).toBeTruthy();
            expect(getByText('South Region')).toBeTruthy();
            expect(getByText('East Region')).toBeTruthy();
        });
    });

    test('should require region selection for vendor registration', async () => {
        const { getByText, getByPlaceholderText } = render(<RegisterScreen navigation={mockNavigation} />);

        // Switch to vendor role
        fireEvent.press(getByText('Vendor'));

        await waitFor(() => {
            expect(getByText('North Region')).toBeTruthy();
        });

        // Fill in required fields but don't select region
        fireEvent.changeText(getByPlaceholderText('Email *'), 'vendor@test.com');
        fireEvent.changeText(getByPlaceholderText('Business Name *'), 'Test Business');
        fireEvent.changeText(getByPlaceholderText('Password *'), 'password123');
        fireEvent.changeText(getByPlaceholderText('Confirm Password *'), 'password123');

        // Try to submit without selecting region
        fireEvent.press(getByText('Create Account'));

        // Should show error alert (we can't easily test Alert.alert, but the function should not proceed)
        expect(client.post).not.toHaveBeenCalled();
    });

    test('should include selected region_id in registration payload', async () => {
        client.post.mockResolvedValueOnce({ data: { id: 1 } })
            .mockResolvedValueOnce({ data: { access_token: 'test-token' } });

        const { getByText, getByPlaceholderText } = render(<RegisterScreen navigation={mockNavigation} />);

        // Switch to vendor role
        fireEvent.press(getByText('Vendor'));

        await waitFor(() => {
            expect(getByText('North Region')).toBeTruthy();
        });

        // Fill in all required fields
        fireEvent.changeText(getByPlaceholderText('Email *'), 'vendor@test.com');
        fireEvent.changeText(getByPlaceholderText('Business Name *'), 'Test Business');
        fireEvent.changeText(getByPlaceholderText('Password *'), 'password123');
        fireEvent.changeText(getByPlaceholderText('Confirm Password *'), 'password123');

        // Select a region
        fireEvent.press(getByText('South Region'));

        // Submit form
        fireEvent.press(getByText('Create Account'));

        // Verify registration payload includes region_id
        await waitFor(() => {
            expect(client.post).toHaveBeenCalledWith('/auth/register', expect.objectContaining({
                email: 'vendor@test.com',
                role: 'VENDOR',
                business_name: 'Test Business',
                region_id: 2 // South Region has id 2
            }));
        });
    });

    test('should not require region for customer registration', async () => {
        client.post.mockResolvedValueOnce({ data: { id: 1 } })
            .mockResolvedValueOnce({ data: { access_token: 'test-token' } });

        const { getByText, getByPlaceholderText, queryByText } = render(<RegisterScreen navigation={mockNavigation} />);

        // Customer role is default, region selection should not be visible
        expect(queryByText('Select Region *')).toBeNull();

        // Fill in required fields for customer
        fireEvent.changeText(getByPlaceholderText('Email *'), 'customer@test.com');
        fireEvent.changeText(getByPlaceholderText('Password *'), 'password123');
        fireEvent.changeText(getByPlaceholderText('Confirm Password *'), 'password123');

        // Submit form
        fireEvent.press(getByText('Create Account'));

        // Verify registration payload does not include region_id
        await waitFor(() => {
            expect(client.post).toHaveBeenCalledWith('/auth/register', expect.objectContaining({
                email: 'customer@test.com',
                role: 'CUSTOMER'
            }));
            expect(client.post).toHaveBeenCalledWith('/auth/register', expect.not.objectContaining({
                region_id: expect.anything()
            }));
        });
    });
});

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import ProfileScreen from '../ProfileScreen';
import client from '../../../api/client';
import { useAuthStore } from '../../../store/authStore';

// Mock dependencies
jest.mock('../../../api/client');
jest.mock('../../../store/authStore');
jest.spyOn(Alert, 'alert');

describe('ProfileScreen', () => {
    const mockNavigation = {
        navigate: jest.fn(),
        goBack: jest.fn()
    };

    const mockUser = {
        id: 1,
        email: 'customer@example.com',
        full_name: 'John Doe',
        role: 'CUSTOMER'
    };

    beforeEach(() => {
        jest.clearAllMocks();
        useAuthStore.mockReturnValue({
            user: mockUser,
            logout: jest.fn(),
            setUser: jest.fn()
        });
    });

    describe('Name Management', () => {
        it('should display user name correctly', async () => {
            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] }); // addresses
            client.get.mockResolvedValueOnce({ data: [] }); // phones

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('John Doe')).toBeTruthy();
            });
        });

        it('should allow editing name', async () => {
            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] });
            client.get.mockResolvedValueOnce({ data: [] });

            const { getByText, getByPlaceholderText } = render(
                <ProfileScreen navigation={mockNavigation} />
            );

            await waitFor(() => {
                expect(getByText('John Doe')).toBeTruthy();
            });

            // Click edit button
            const editButton = getByText('Personal Information').parent.parent;
            const editIcon = editButton.findByProps({ name: 'create-outline' });
            fireEvent.press(editIcon);

            // Input should be visible
            const input = getByPlaceholderText('Enter full name');
            expect(input).toBeTruthy();
        });

        it('should update name successfully', async () => {
            const updatedUser = { ...mockUser, full_name: 'Jane Smith' };
            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] });
            client.get.mockResolvedValueOnce({ data: [] });
            client.put.mockResolvedValueOnce({
                data: { message: 'Profile updated successfully', profile: updatedUser }
            });

            const mockSetUser = jest.fn();
            useAuthStore.mockReturnValue({
                user: mockUser,
                logout: jest.fn(),
                setUser: mockSetUser
            });

            const { getByText, getByPlaceholderText } = render(
                <ProfileScreen navigation={mockNavigation} />
            );

            await waitFor(() => {
                expect(getByText('John Doe')).toBeTruthy();
            });

            // Click edit button
            const editButton = getByText('Personal Information').parent.parent;
            const editIcon = editButton.findByProps({ name: 'create-outline' });
            fireEvent.press(editIcon);

            // Change name
            const input = getByPlaceholderText('Enter full name');
            fireEvent.changeText(input, 'Jane Smith');

            // Save
            const saveButton = getByText('Save Changes');
            fireEvent.press(saveButton);

            await waitFor(() => {
                expect(client.put).toHaveBeenCalledWith(
                    '/customer/profile',
                    null,
                    { params: { full_name: 'Jane Smith' } }
                );
                expect(mockSetUser).toHaveBeenCalledWith(updatedUser);
                expect(Alert.alert).toHaveBeenCalledWith('Success', 'Profile updated successfully');
            });
        });

        it('should show error when name is empty', async () => {
            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] });
            client.get.mockResolvedValueOnce({ data: [] });

            const { getByText, getByPlaceholderText } = render(
                <ProfileScreen navigation={mockNavigation} />
            );

            await waitFor(() => {
                expect(getByText('John Doe')).toBeTruthy();
            });

            // Click edit button
            const editButton = getByText('Personal Information').parent.parent;
            const editIcon = editButton.findByProps({ name: 'create-outline' });
            fireEvent.press(editIcon);

            // Clear name
            const input = getByPlaceholderText('Enter full name');
            fireEvent.changeText(input, '   ');

            // Try to save
            const saveButton = getByText('Save Changes');
            fireEvent.press(saveButton);

            await waitFor(() => {
                expect(Alert.alert).toHaveBeenCalledWith('Error', 'Please enter your full name');
                expect(client.put).not.toHaveBeenCalled();
            });
        });
    });

    describe('Address Management', () => {
        it('should display addresses', async () => {
            const addresses = [
                { id: 1, label: 'Home', address_text: '123 Main St', is_default: true },
                { id: 2, label: 'Work', address_text: '456 Office Blvd', is_default: false }
            ];

            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: addresses });
            client.get.mockResolvedValueOnce({ data: [] });

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('Home')).toBeTruthy();
                expect(getByText('123 Main St')).toBeTruthy();
                expect(getByText('Work')).toBeTruthy();
                expect(getByText('456 Office Blvd')).toBeTruthy();
            });
        });

        it('should show empty state when no addresses', async () => {
            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] });
            client.get.mockResolvedValueOnce({ data: [] });

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('No addresses added yet')).toBeTruthy();
            });
        });

        it('should navigate to add address screen', async () => {
            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] });
            client.get.mockResolvedValueOnce({ data: [] });

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('Addresses')).toBeTruthy();
            });

            // Find and click add button
            const addButton = getByText('Addresses').parent.parent.findByProps({ name: 'add-circle' });
            fireEvent.press(addButton);

            expect(mockNavigation.navigate).toHaveBeenCalledWith('AddAddress', expect.any(Object));
        });

        it('should delete address with confirmation', async () => {
            const addresses = [
                { id: 1, label: 'Home', address_text: '123 Main St', is_default: true }
            ];

            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: addresses });
            client.get.mockResolvedValueOnce({ data: [] });
            client.delete.mockResolvedValueOnce({ data: { message: 'Address deleted successfully' } });

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('Home')).toBeTruthy();
            });

            // Find and click delete button
            const deleteButton = getByText('Home').parent.parent.findByProps({ name: 'trash-outline' });
            fireEvent.press(deleteButton);

            // Confirm deletion in alert
            expect(Alert.alert).toHaveBeenCalledWith(
                'Delete Address',
                'Are you sure you want to delete this address?',
                expect.any(Array)
            );

            // Simulate user confirming
            const alertCall = Alert.alert.mock.calls[0];
            const deleteAction = alertCall[2].find(action => action.text === 'Delete');
            await deleteAction.onPress();

            await waitFor(() => {
                expect(client.delete).toHaveBeenCalledWith('/customer/addresses/1');
                expect(Alert.alert).toHaveBeenCalledWith('Success', 'Address deleted successfully');
            });
        });
    });

    describe('Phone Number Management', () => {
        it('should display phone numbers', async () => {
            const phones = [
                { id: 1, number: '+1234567890', is_default: true },
                { id: 2, number: '+0987654321', is_default: false }
            ];

            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] });
            client.get.mockResolvedValueOnce({ data: phones });

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('+1234567890')).toBeTruthy();
                expect(getByText('+0987654321')).toBeTruthy();
            });
        });

        it('should show empty state when no phone numbers', async () => {
            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] });
            client.get.mockResolvedValueOnce({ data: [] });

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('No phone numbers added yet')).toBeTruthy();
            });
        });

        it('should navigate to add phone screen', async () => {
            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] });
            client.get.mockResolvedValueOnce({ data: [] });

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('Phone Numbers')).toBeTruthy();
            });

            // Find and click add button
            const addButton = getByText('Phone Numbers').parent.parent.findByProps({ name: 'add-circle' });
            fireEvent.press(addButton);

            expect(mockNavigation.navigate).toHaveBeenCalledWith('AddPhone', expect.any(Object));
        });
    });

    describe('Validation', () => {
        it('should show limit reached for addresses', async () => {
            const addresses = [
                { id: 1, label: 'Home', address_text: '123 Main St', is_default: true },
                { id: 2, label: 'Work', address_text: '456 Office Blvd', is_default: false }
            ];

            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: addresses });
            client.get.mockResolvedValueOnce({ data: [] });

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('Home')).toBeTruthy();
            });

            // Add button should not be visible when limit reached
            const addressesCard = getByText('Addresses').parent.parent;
            const addButton = addressesCard.findByProps({ name: 'add-circle' });
            expect(addButton).toBeNull();
        });

        it('should show limit reached for phone numbers', async () => {
            const phones = [
                { id: 1, number: '+1234567890', is_default: true },
                { id: 2, number: '+0987654321', is_default: false }
            ];

            client.get.mockResolvedValueOnce({ data: mockUser });
            client.get.mockResolvedValueOnce({ data: [] });
            client.get.mockResolvedValueOnce({ data: phones });

            const { getByText } = render(<ProfileScreen navigation={mockNavigation} />);

            await waitFor(() => {
                expect(getByText('+1234567890')).toBeTruthy();
            });

            // Add button should not be visible when limit reached
            const phonesCard = getByText('Phone Numbers').parent.parent;
            const addButton = phonesCard.findByProps({ name: 'add-circle' });
            expect(addButton).toBeNull();
        });
    });
});

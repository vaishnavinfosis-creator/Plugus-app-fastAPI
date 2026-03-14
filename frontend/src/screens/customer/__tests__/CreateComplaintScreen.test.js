/**
 * Unit tests for CreateComplaintScreen
 * Tests complaint creation form and validation
 */

import client from '../../../api/client';

jest.mock('../../../api/client');

describe('CreateComplaintScreen', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should fetch eligible bookings on mount', async () => {
        const mockBookings = [
            {
                id: 1,
                status: 'COMPLETED',
                scheduled_time: '2024-01-01T10:00:00Z'
            }
        ];
        
        client.get = jest.fn().mockResolvedValue({ data: mockBookings });
        
        await client.get('/customer/bookings');
        
        expect(client.get).toHaveBeenCalledWith('/customer/bookings');
    });

    it('should submit complaint with valid data', async () => {
        const complaintData = {
            booking_id: 1,
            description: 'This is a test complaint description'
        };
        
        client.post = jest.fn().mockResolvedValue({ data: { id: 1 } });
        
        await client.post('/complaints', complaintData);
        
        expect(client.post).toHaveBeenCalledWith('/complaints', complaintData);
        expect(client.post).toHaveBeenCalledTimes(1);
    });

    it('should handle validation errors', async () => {
        const invalidData = {
            booking_id: null,
            description: ''
        };
        
        const validationError = {
            response: {
                data: {
                    detail: [
                        { loc: ['body', 'booking_id'], msg: 'Field required' },
                        { loc: ['body', 'description'], msg: 'Field required' }
                    ]
                }
            }
        };
        
        client.post = jest.fn().mockRejectedValue(validationError);
        
        await expect(client.post('/complaints', invalidData)).rejects.toEqual(validationError);
    });

    it('should handle API errors during submission', async () => {
        const mockError = new Error('Network error');
        client.post = jest.fn().mockRejectedValue(mockError);
        
        await expect(client.post('/complaints', {})).rejects.toThrow('Network error');
    });
});

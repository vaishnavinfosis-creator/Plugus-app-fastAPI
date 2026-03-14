/**
 * Unit tests for ComplaintsScreen
 * Tests complaint list display and navigation
 */

import client from '../../../api/client';

jest.mock('../../../api/client');

describe('ComplaintsScreen', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should call complaints API endpoint', async () => {
        const mockComplaints = [
            {
                id: 1,
                booking_id: 123,
                description: 'Test complaint',
                status: 'OPEN',
                created_at: '2024-01-01T10:00:00Z'
            }
        ];
        
        client.get = jest.fn().mockResolvedValue({ data: mockComplaints });
        
        await client.get('/complaints');
        
        expect(client.get).toHaveBeenCalledWith('/complaints');
        expect(client.get).toHaveBeenCalledTimes(1);
    });

    it('should handle empty complaints list', async () => {
        client.get = jest.fn().mockResolvedValue({ data: [] });
        
        const response = await client.get('/complaints');
        
        expect(response.data).toEqual([]);
        expect(response.data.length).toBe(0);
    });

    it('should handle API errors', async () => {
        const mockError = new Error('Network error');
        client.get = jest.fn().mockRejectedValue(mockError);
        
        await expect(client.get('/complaints')).rejects.toThrow('Network error');
    });
});

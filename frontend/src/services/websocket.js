/**
 * WebSocket Service for Real-time Updates
 */

class WebSocketService {
    constructor(baseUrl = 'ws://localhost:8000/api/v1/ws') {
        this.baseUrl = baseUrl;
        this.connections = new Map();
    }

    /**
     * Connect to booking updates channel
     */
    connectBookingUpdates(bookingId, token, onMessage, onError) {
        const url = `${this.baseUrl}/booking/${bookingId}?token=${token}`;
        return this._connect(`booking:${bookingId}`, url, onMessage, onError);
    }

    /**
     * Connect to worker tracking channel
     */
    connectWorkerTracking(bookingId, token, onMessage, onError) {
        const url = `${this.baseUrl}/tracking/${bookingId}?token=${token}`;
        return this._connect(`tracking:${bookingId}`, url, onMessage, onError);
    }

    /**
     * Connect as worker to send location updates
     */
    connectWorkerLocation(token, onConnected, onError) {
        const url = `${this.baseUrl}/worker/location?token=${token}`;
        const ws = new WebSocket(url);

        ws.onopen = () => {
            this.connections.set('worker:location', ws);
            if (onConnected) onConnected();
        };

        ws.onerror = (error) => {
            if (onError) onError(error);
        };

        ws.onclose = () => {
            this.connections.delete('worker:location');
        };

        return {
            sendLocation: (bookingId, lat, lng) => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ booking_id: bookingId, lat, lng }));
                }
            },
            close: () => ws.close()
        };
    }

    _connect(key, url, onMessage, onError) {
        // Close existing connection if any
        if (this.connections.has(key)) {
            this.connections.get(key).close();
        }

        const ws = new WebSocket(url);

        ws.onopen = () => {
            this.connections.set(key, ws);
            // Start ping interval
            const pingInterval = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                } else {
                    clearInterval(pingInterval);
                }
            }, 30000);
        };

        ws.onmessage = (event) => {
            if (event.data === 'pong') return; // Ignore pong

            try {
                const data = JSON.parse(event.data);
                if (onMessage) onMessage(data);
            } catch (e) {
                console.log('WebSocket message:', event.data);
            }
        };

        ws.onerror = (error) => {
            if (onError) onError(error);
        };

        ws.onclose = () => {
            this.connections.delete(key);
        };

        return {
            close: () => ws.close(),
            isConnected: () => ws.readyState === WebSocket.OPEN
        };
    }

    /**
     * Disconnect all connections
     */
    disconnectAll() {
        this.connections.forEach((ws) => ws.close());
        this.connections.clear();
    }
}

export default new WebSocketService();

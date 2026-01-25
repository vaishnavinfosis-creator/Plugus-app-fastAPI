"""
WebSocket - Real-time updates
"""
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import json


class ConnectionManager:
    """Manages WebSocket connections per channel"""
    
    def __init__(self):
        # channel_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
    
    async def send_to_channel(self, channel: str, message: dict):
        """Send message to all connections in a channel"""
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.active_connections[channel].discard(conn)
    
    async def broadcast_booking_update(self, booking_id: int, status: str, data: dict = None):
        """Broadcast booking status update"""
        message = {
            "type": "booking_update",
            "booking_id": booking_id,
            "status": status,
            "data": data or {}
        }
        # Send to customer channel
        await self.send_to_channel(f"booking:{booking_id}", message)
    
    async def broadcast_worker_location(self, booking_id: int, lat: float, lng: float):
        """Broadcast worker location for tracking"""
        message = {
            "type": "worker_location",
            "booking_id": booking_id,
            "latitude": lat,
            "longitude": lng
        }
        await self.send_to_channel(f"tracking:{booking_id}", message)


# Global connection manager
manager = ConnectionManager()

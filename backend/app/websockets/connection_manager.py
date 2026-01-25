from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # role -> user_id -> websocket
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {
            "CUSTOMER": {},
            "VENDOR": {},
            "WORKER": {},
            "ADMIN": {} # Regional/Super
        }

    async def connect(self, websocket: WebSocket, role: str, user_id: int):
        await websocket.accept()
        if role not in self.active_connections:
            self.active_connections[role] = {}
        self.active_connections[role][user_id] = websocket

    def disconnect(self, role: str, user_id: int):
        if role in self.active_connections and user_id in self.active_connections[role]:
            del self.active_connections[role][user_id]

    async def send_personal_message(self, message: dict, role: str, user_id: int):
        if role in self.active_connections and user_id in self.active_connections[role]:
            await self.active_connections[role][user_id].send_json(message)

    async def broadcast(self, message: dict, role: str):
        if role in self.active_connections:
            for connection in self.active_connections[role].values():
                await connection.send_json(message)

manager = ConnectionManager()

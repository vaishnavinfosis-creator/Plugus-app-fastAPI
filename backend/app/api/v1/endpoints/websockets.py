from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.websockets.connection_manager import manager
from app.core import security
from app.api import deps
from jose import jwt, JWTError
from app.core.config import settings
from app.models.user import UserRole

router = APIRouter()

async def get_token_from_query(token: str = Query(...)):
    return token

@router.websocket("/ws/{role}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    role: str,
    user_id: int,
    token: str = Query(...)
):
    # Verify token
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_sub = payload.get("sub")
        if token_sub is None or int(token_sub) != user_id:
             await websocket.close(code=1008)
             return
    except JWTError:
        await websocket.close(code=1008)
        return

    # Map role string to Enum if needed, or just use string
    # Simple validation
    if role not in ["CUSTOMER", "VENDOR", "WORKER", "ADMIN"]:
         await websocket.close(code=1008)
         return

    await manager.connect(websocket, role, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming messages (e.g. location update from worker)
            if role == "WORKER" and data.get("type") == "LOCATION_UPDATE":
                # Broadcast to relevant customer/vendor
                # This requires knowing which booking is active.
                # For now, just echo or log.
                # In a real app, we would look up the active booking and send to customer.
                pass
    except WebSocketDisconnect:
        manager.disconnect(role, user_id)

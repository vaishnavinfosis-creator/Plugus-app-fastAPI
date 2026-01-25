"""
WebSocket Endpoints for Real-time Updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.core.websocket import manager
from app.core.security import verify_token
import json

router = APIRouter()


@router.websocket("/booking/{booking_id}")
async def booking_updates(websocket: WebSocket, booking_id: int, token: str = Query(...)):
    """
    WebSocket for booking status updates.
    Customer connects to receive real-time status changes.
    """
    # Verify token
    try:
        payload = verify_token(token)
        if not payload:
            await websocket.close(code=4001)
            return
    except:
        await websocket.close(code=4001)
        return
    
    channel = f"booking:{booking_id}"
    await manager.connect(websocket, channel)
    
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/tracking/{booking_id}")
async def worker_tracking(websocket: WebSocket, booking_id: int, token: str = Query(...)):
    """
    WebSocket for worker location tracking.
    Customer connects to receive real-time worker location.
    """
    try:
        payload = verify_token(token)
        if not payload:
            await websocket.close(code=4001)
            return
    except:
        await websocket.close(code=4001)
        return
    
    channel = f"tracking:{booking_id}"
    await manager.connect(websocket, channel)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/worker/location")
async def worker_location_update(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket for worker to send location updates.
    Worker connects to broadcast their location.
    """
    try:
        payload = verify_token(token)
        if not payload:
            await websocket.close(code=4001)
            return
    except:
        await websocket.close(code=4001)
        return
    
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            # Expected: { "booking_id": 123, "lat": 12.34, "lng": 56.78 }
            if "booking_id" in data and "lat" in data and "lng" in data:
                await manager.broadcast_worker_location(
                    data["booking_id"],
                    data["lat"],
                    data["lng"]
                )
    except WebSocketDisconnect:
        pass

"""
API Router - Combines all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, customer, vendor, worker, admin, websocket

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(customer.router, prefix="/customer", tags=["customer"])
api_router.include_router(vendor.router, prefix="/vendor", tags=["vendor"])
api_router.include_router(worker.router, prefix="/worker", tags=["worker"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])

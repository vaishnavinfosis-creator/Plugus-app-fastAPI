"""
Audit Logging System
Tracks critical operations for compliance and debugging
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class AuditLog(Base):
    """Audit log for tracking critical operations"""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, etc.
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Booking, Payment, etc.
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    changes: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON of changes
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action}, entity={self.entity_type}:{self.entity_id})>"


def create_audit_log(
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    changes: dict = None,
    ip_address: str = None,
    user_agent: str = None,
    db = None
):
    """
    Helper function to create audit log entries
    
    Args:
        user_id: ID of user performing action
        action: Action type (CREATE, UPDATE, DELETE, etc.)
        entity_type: Type of entity (Booking, Payment, etc.)
        entity_id: ID of entity
        changes: Dictionary of changes made
        ip_address: IP address of request
        user_agent: User agent string
        db: Database session
    """
    if db is None:
        return
    
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(audit_log)
    # Note: Caller should commit the transaction
    
    return audit_log

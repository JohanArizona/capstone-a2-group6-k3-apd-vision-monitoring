"""
Notification Request/Response Schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class NotificationResponse(BaseModel):
    """Response model untuk single notification"""
    id: UUID
    violation_id: UUID
    message: str
    is_read: bool
    sent_at: datetime
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response model untuk list notifications"""
    id: UUID
    violation_id: UUID
    message: str
    is_read: bool
    sent_at: datetime
    
    class Config:
        from_attributes = True


class NotificationReadUpdate(BaseModel):
    """Request model untuk mark as read"""
    pass

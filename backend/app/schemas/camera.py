from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.camera import CameraStatus
from uuid import UUID

class CameraCreate(BaseModel):
    """Schema untuk create camera"""
    name: str
    location: str
    rtsp_url: str
    status: CameraStatus = CameraStatus.ACTIVE

class CameraResponse(BaseModel):
    """Schema untuk camera response"""
    id: UUID
    name: str
    location: str
    rtsp_url: str
    status: CameraStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CameraUpdate(BaseModel):
    """Schema untuk update camera"""
    name: Optional[str] = None
    location: Optional[str] = None
    rtsp_url: Optional[str] = None
    status: Optional[CameraStatus] = None

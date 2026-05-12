"""
Schemas untuk Camera Management
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

class CameraBase(BaseModel):
    """Base schema untuk Camera"""
    name: str = Field(..., min_length=1, max_length=100, description="Nama kamera")
    location: str = Field(..., min_length=1, max_length=100, description="Lokasi kamera")
    rtsp_url: str = Field(..., min_length=1, max_length=255, description="RTSP stream URL")
    status: Literal["Active", "Inactive", "Maintenance"] = Field(default="Active", description="Status kamera")

class CameraCreate(CameraBase):
    """Schema untuk membuat Camera baru (Admin)"""
    pass

class CameraUpdate(BaseModel):
    """Schema untuk update Camera (Admin)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    rtsp_url: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[Literal["Active", "Inactive", "Maintenance"]] = None

class CameraResponse(CameraBase):
    """Schema untuk response Camera"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CameraListResponse(BaseModel):
    """Schema untuk response list Camera"""
    id: UUID
    name: str
    location: str
    status: Literal["Active", "Inactive", "Maintenance"]
    
    model_config = ConfigDict(from_attributes=True)

class CameraDetailResponse(CameraResponse):
    """Schema untuk response detail Camera"""
    pass

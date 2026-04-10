from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.violation import ViolationStatus
from uuid import UUID
from decimal import Decimal

class ViolationCreate(BaseModel):
    """Schema untuk create violation"""
    camera_id: UUID
    missing_apd: Dict[str, Any]  # {"helmet": True, "vest": False}
    confidence_score: Decimal
    snapshot_path: str

class ViolationResponse(BaseModel):
    """Schema untuk violation response"""
    id: UUID
    camera_id: UUID
    missing_apd: Dict[str, Any]
    confidence_score: Decimal
    snapshot_path: str
    timestamp: datetime
    status: ViolationStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

class ViolationUpdate(BaseModel):
    """Schema untuk update violation status"""
    status: Optional[ViolationStatus] = None

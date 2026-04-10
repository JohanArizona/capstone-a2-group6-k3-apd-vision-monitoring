"""
Schemas untuk Violations Management
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional, Literal, Dict
import json

class ViolationBase(BaseModel):
    """Base schema untuk Violation"""
    camera_id: UUID = Field(..., description="Camera ID")
    missing_apd: Dict[str, bool] = Field(..., description="APD yang hilang {'helmet': True, 'vest': False}")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")

class ViolationCreate(ViolationBase):
    """Schema untuk membuat Violation baru (dari Edge AI)"""
    # snapshot_path dihandle separate di endpoint
    pass

class ViolationStatusUpdate(BaseModel):
    """Schema untuk update status violation"""
    status: Literal["Verified", "False_Positive"] = Field(..., description="Status hasil verifikasi")
    notes: Optional[str] = Field(None, max_length=500, description="Catatan verifikasi")

class ViolationResponse(ViolationBase):
    """Schema untuk response Violation"""
    id: UUID
    snapshot_path: str
    timestamp: datetime
    status: Literal["Unverified", "Verified", "False_Positive"]
    notes: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ViolationListResponse(BaseModel):
    """Schema untuk response list Violation (dashboard)"""
    id: UUID
    camera_id: UUID
    missing_apd: Dict[str, bool]
    confidence_score: float
    snapshot_path: str
    timestamp: datetime
    status: Literal["Unverified", "Verified", "False_Positive"]
    notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ViolationDetailResponse(ViolationResponse):
    """Schema untuk response detail Violation"""
    pass

class ViolationExportRow(BaseModel):
    """Schema untuk export Excel row"""
    id: str
    camera_id: str
    timestamp: str
    missing_apd: str
    confidence_score: float
    status: str
    snapshot_path: str

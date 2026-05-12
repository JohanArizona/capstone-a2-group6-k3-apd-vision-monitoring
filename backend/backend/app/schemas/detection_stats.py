"""
Schemas untuk Detection Statistics
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional

class DetectionStatsBase(BaseModel):
    """Base schema untuk Detection Stats"""
    camera_id: UUID = Field(..., description="ID kamera")
    total_workers: int = Field(..., ge=0, description="Total jumlah pekerja yang terdeteksi")
    compliant_workers: int = Field(..., ge=0, description="Jumlah pekerja yang compliance")
    violating_workers: int = Field(..., ge=0, description="Jumlah pekerja yang violation")

class DetectionStatsCreate(DetectionStatsBase):
    """Schema untuk membuat Detection Stats baru (dari Edge AI)"""
    timestamp: Optional[datetime] = Field(None, description="Timestamp pengiriman (auto jika None)")

class DetectionStatsResponse(DetectionStatsBase):
    """Schema untuk response Detection Stats"""
    id: UUID
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DetectionStatsListResponse(BaseModel):
    """Schema untuk response list Detection Stats (untuk chart)"""
    id: UUID
    camera_id: UUID
    timestamp: datetime
    total_workers: int
    compliant_workers: int
    violating_workers: int
    
    model_config = ConfigDict(from_attributes=True)

class DetectionStatsSummary(BaseModel):
    """Schema untuk summary statistics"""
    total_records: int = Field(..., description="Total records dalam periode")
    average_workers: float = Field(..., description="Rata-rata jumlah pekerja")
    average_compliance_rate: float = Field(..., description="Rata-rata compliance rate (%)")
    peak_workers: int = Field(..., description="Peak jumlah pekerja")
    total_violations: int = Field(..., description="Total violations dalam periode")

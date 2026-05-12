from enum import Enum
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, ENUM
from uuid import uuid4
from app.core import Base

class CameraStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    MAINTENANCE = "Maintenance"

class Camera(Base):
    __tablename__ = "camera"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    location = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    rtsp_url = Column(String(255), nullable=False)
    status = Column(ENUM('Active', 'Inactive', 'Maintenance', name='camera_status'), nullable=False, default='Active')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Camera(id={self.id}, name={self.name}, location={self.location})>"

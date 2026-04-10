from enum import Enum
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Index, JSON, func
from sqlalchemy.dialects.postgresql import UUID, ENUM
from uuid import uuid4
from app.core import Base

class ViolationStatus(str, Enum):
    UNVERIFIED = "Unverified"
    VERIFIED = "Verified"
    FALSE_POSITIVE = "False_Positive"

class Violation(Base):
    __tablename__ = "violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("camera.id", ondelete="CASCADE"), nullable=False)
    missing_apd = Column(JSON, nullable=False)  # {"helmet": True, "vest": False}
    confidence_score = Column(Numeric(5, 4), nullable=False)
    snapshot_path = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(ENUM('Unverified', 'Verified', 'False_Positive', name='violation_status'), nullable=False, default='Unverified')
    notes = Column(String(500), nullable=True)  # Catatan verifikasi
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_violations_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<Violation(id={self.id}, camera_id={self.camera_id}, status={self.status})>"

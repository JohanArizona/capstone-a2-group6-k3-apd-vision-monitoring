from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.core import Base

class DetectionStats(Base):
    __tablename__ = "detection_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("camera.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    total_workers = Column(Integer, default=0)
    compliant_workers = Column(Integer, default=0)
    violating_workers = Column(Integer, default=0)
    
    __table_args__ = (
        Index("idx_detection_stats_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<DetectionStats(id={self.id}, camera_id={self.camera_id}, total_workers={self.total_workers})>"

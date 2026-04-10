from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.core import Base

class Notification(Base):
    __tablename__ = "notification"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    violation_id = Column(UUID(as_uuid=True), ForeignKey("violations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_notification_user_id", "user_id"),
    )
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, is_read={self.is_read})>"

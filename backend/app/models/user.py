from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, ENUM
from uuid import uuid4
from app.core import Base

class UserRole(str, Enum):
    ADMIN_IT = "Admin_IT"
    PENGAWAS_K3 = "Pengawas_K3"
    MANAGER_HR = "Manager_HR"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    telegram_id = Column(String(50), nullable=True)
    role = Column(ENUM('Admin_IT', 'Pengawas_K3', 'Manager_HR', name='user_role'), nullable=False, default='Pengawas_K3')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

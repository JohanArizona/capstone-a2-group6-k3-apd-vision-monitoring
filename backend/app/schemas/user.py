from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
from uuid import UUID

class UserCreate(BaseModel):
    """Schema untuk create user"""
    username: str
    password: str
    full_name: str
    email: EmailStr
    telegram_id: Optional[str] = None
    role: UserRole = UserRole.PENGAWAS_K3

class UserResponse(BaseModel):
    """Schema untuk user response"""
    id: UUID
    username: str
    full_name: str
    email: str
    telegram_id: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema untuk update user"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    telegram_id: Optional[str] = None
    is_active: Optional[bool] = None

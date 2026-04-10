from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserUpdate(BaseModel):
    """Schema untuk update profil user sendiri"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    telegram_id: Optional[str] = None

class UserCreateAdmin(BaseModel):
    """Schema untuk create user (admin only)"""
    username: str
    password: str
    full_name: str
    email: EmailStr
    telegram_id: Optional[str] = None
    role: str = "Pengawas_K3"

class UserUpdateAdmin(BaseModel):
    """Schema untuk update user (admin only)"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    telegram_id: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserDetailResponse(BaseModel):
    """Schema untuk response detail user"""
    id: UUID
    username: str
    full_name: str
    email: str
    telegram_id: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """Schema untuk response list user"""
    id: UUID
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

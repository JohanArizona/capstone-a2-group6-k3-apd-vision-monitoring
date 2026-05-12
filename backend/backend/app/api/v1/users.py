"""
Users Routes - User Management (Admin & Self-Profile)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_admin_user
from app.core.security import get_password_hash
from app.models import User
from app.schemas.user import UserResponse
from app.schemas.users_admin import (
    UserUpdate, 
    UserCreateAdmin, 
    UserUpdateAdmin,
    UserDetailResponse,
    UserListResponse
)

router = APIRouter(prefix="/api/users", tags=["users"])

# ============ SELF PROFILE ENDPOINTS ============

@router.put("/me", response_model=UserResponse)
async def update_own_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update own profile (All Role)
    - Dapat mengubah: full_name, email, password, telegram_id
    """
    if update_data.full_name:
        current_user.full_name = update_data.full_name
    
    if update_data.email:
        # Check if email already exists
        existing_user = db.query(User).filter(
            User.email == update_data.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email sudah digunakan"
            )
        current_user.email = update_data.email
    
    if update_data.password:
        current_user.password = get_password_hash(update_data.password)
    
    if update_data.telegram_id is not None:
        current_user.telegram_id = update_data.telegram_id
    
    db.commit()
    db.refresh(current_user)
    return current_user

# ============ ADMIN ENDPOINTS ============

@router.get("", response_model=List[UserListResponse])
async def list_all_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all users (Admin only)
    """
    users = db.query(User).all()
    return users

@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: UUID,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user detail by ID (Admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("", response_model=UserDetailResponse)
async def create_user(
    user_data: UserCreateAdmin,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create new user (Admin only)
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username sudah ada"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah digunakan"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        email=user_data.email,
        telegram_id=user_data.telegram_id,
        role=user_data.role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    update_data: UserUpdateAdmin,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user data (Admin only)
    - Dapat mengubah: full_name, email, password, role, is_active, telegram_id
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin dari mengubah dirinya sendiri ke role lain
    if user_id == admin.id and update_data.role and update_data.role != admin.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak boleh mengubah role diri sendiri"
        )
    
    if update_data.full_name:
        user.full_name = update_data.full_name
    
    if update_data.email:
        # Check if email already exists
        existing_user = db.query(User).filter(
            User.email == update_data.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email sudah digunakan"
            )
        user.email = update_data.email
    
    if update_data.password:
        user.password = get_password_hash(update_data.password)
    
    if update_data.role:
        user.role = update_data.role
    
    if update_data.is_active is not None:
        user.is_active = update_data.is_active
    
    if update_data.telegram_id is not None:
        user.telegram_id = update_data.telegram_id
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete/deactivate user (Admin only)
    - Soft delete: set is_active = False
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin dari menghapus dirinya sendiri
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak boleh menghapus akun diri sendiri"
        )
    
    # Soft delete
    user.is_active = False
    db.commit()
    
    return None

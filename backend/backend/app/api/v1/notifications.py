"""
Notifications Management Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, Notification
from app.schemas.notifications import (
    NotificationResponse,
    NotificationListResponse,
    NotificationReadUpdate
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationListResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """
    Mengambil list notifikasi milik user yang login
    
    Akses: Semua role (authenticated users)
    
    Query Parameters:
    - limit: Max records (1-500), default 50
    - offset: Pagination offset, default 0
    
    Returns: List notifikasi dengan pagination
    """
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(
        Notification.sent_at.desc()
    ).limit(limit).offset(offset).all()
    
    return notifications


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mengubah is_read menjadi TRUE pada satu notifikasi
    
    Akses: Semua role (authenticated users)
    
    URL Parameter:
    - notification_id: UUID dari notifikasi
    
    Returns: Notifikasi yang sudah di-update
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    
    return notification


@router.put("/read-all", response_model=dict)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tandai semua notifikasi user sebagai telah dibaca
    
    Akses: Semua role (authenticated users)
    
    Returns: Count notifikasi yang di-update
    """
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({Notification.is_read: True})
    
    db.commit()
    
    return {
        "message": "All notifications marked as read",
        "count": count
    }

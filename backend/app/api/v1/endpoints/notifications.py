from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse], summary="List user notifications")
def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve notifications stream for the current user and their active role."""
    role_name = current_user.role.name.value if (current_user.role and hasattr(current_user.role.name, "value")) else str(current_user.role.name) if current_user.role else None
    return NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        role_name=role_name,
        unread_only=unread_only,
        limit=limit,
    )


@router.get("/unread-count", response_model=UnreadCountResponse, summary="Get unread notifications count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get real-time count of unread and critical notifications for the navbar bell icon."""
    role_name = current_user.role.name.value if (current_user.role and hasattr(current_user.role.name, "value")) else str(current_user.role.name) if current_user.role else None
    return NotificationService.get_unread_count(
        db=db,
        user_id=current_user.id,
        role_name=role_name,
    )


@router.post("/{notification_id}/read", response_model=NotificationResponse, summary="Mark notification as read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a specific notification as read."""
    notif = NotificationService.mark_as_read(db=db, notification_id=notification_id, user_id=current_user.id)
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notif


@router.post("/read-all", summary="Mark all user notifications as read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark all notifications for the active user and role as read."""
    role_name = current_user.role.name.value if (current_user.role and hasattr(current_user.role.name, "value")) else str(current_user.role.name) if current_user.role else None
    count = NotificationService.mark_all_as_read(db=db, user_id=current_user.id, role_name=role_name)
    return {"success": True, "marked_count": count}

import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.notification import (
    NotificationType,
    NotificationPriority,
)


class NotificationCreate(BaseModel):
    user_id: Optional[int] = None
    role_target: Optional[str] = None
    type: NotificationType = NotificationType.INFO
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    related_entity: Optional[str] = None
    related_entity_id: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    role_target: Optional[str] = None
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    related_entity: Optional[str] = None
    related_entity_id: Optional[str] = None
    is_read: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    unread_count: int
    critical_unread_count: int

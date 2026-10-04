import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models.notification import (
    Notification,
    NotificationType,
    NotificationPriority,
)
from app.models.user import User
from app.core.logging import logger


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        title: str,
        message: str,
        user_id: Optional[int] = None,
        role_target: Optional[str] = None,
        type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        related_entity: Optional[str] = None,
        related_entity_id: Optional[str] = None,
    ) -> Notification:
        """Create and persist a notification targeting a specific user or role group."""
        notif = Notification(
            user_id=user_id,
            role_target=role_target,
            type=type,
            title=title,
            message=message,
            priority=priority,
            related_entity=related_entity,
            related_entity_id=str(related_entity_id) if related_entity_id else None,
            is_read=False,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(notif)
        db.flush()
        logger.info(f"Notification created: [{priority.value}] {title} (User: {user_id}, Role: {role_target})")
        return notif

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        role_name: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """Fetch notifications relevant to the user (direct assignments or role-targeted)."""
        query = db.query(Notification)
        
        conditions = [Notification.user_id == user_id]
        if role_name:
            conditions.append(Notification.role_target == role_name.upper())
            conditions.append(Notification.role_target == "ALL")
            
        query = query.filter(or_(*conditions))
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
            
        return query.order_by(desc(Notification.created_at)).limit(limit).all()

    @staticmethod
    def get_unread_count(db: Session, user_id: int, role_name: Optional[str] = None) -> dict:
        """Return count of unread and critical unread notifications."""
        conditions = [Notification.user_id == user_id]
        if role_name:
            conditions.append(Notification.role_target == role_name.upper())
            conditions.append(Notification.role_target == "ALL")
            
        base_query = db.query(Notification).filter(or_(*conditions), Notification.is_read == False)
        
        unread_count = base_query.count()
        critical_unread = base_query.filter(
            or_(
                Notification.priority == NotificationPriority.URGENT,
                Notification.priority == NotificationPriority.HIGH,
                Notification.type == NotificationType.CRITICAL,
                Notification.type == NotificationType.ALERT,
            )
        ).count()
        
        return {
            "unread_count": unread_count,
            "critical_unread_count": critical_unread,
        }

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark a single notification as read."""
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if notif:
            notif.is_read = True
            db.commit()
            db.refresh(notif)
        return notif

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int, role_name: Optional[str] = None) -> int:
        """Mark all notifications for the user as read."""
        conditions = [Notification.user_id == user_id]
        if role_name:
            conditions.append(Notification.role_target == role_name.upper())
            conditions.append(Notification.role_target == "ALL")
            
        notifs = db.query(Notification).filter(or_(*conditions), Notification.is_read == False).all()
        count = len(notifs)
        for n in notifs:
            n.is_read = True
        db.commit()
        return count

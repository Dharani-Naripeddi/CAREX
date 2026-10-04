import enum
import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class NotificationType(str, enum.Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"


class NotificationPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Can target a specific user OR a whole role group (e.g. all PHARMACISTs)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    role_target = Column(String(50), nullable=True, index=True)
    
    type = Column(
        SQLEnum(NotificationType, values_callable=lambda obj: [e.value for e in obj]),
        default=NotificationType.INFO,
        nullable=False,
    )
    
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    priority = Column(
        SQLEnum(NotificationPriority, values_callable=lambda obj: [e.value for e in obj]),
        default=NotificationPriority.NORMAL,
        nullable=False,
        index=True,
    )
    
    # Entity linkages for 1-click navigation in frontend
    related_entity = Column(String(50), nullable=True)  # LAB_ORDER, PRESCRIPTION, INVOICE, APPOINTMENT, EMERGENCY, ADMISSION, INVENTORY
    related_entity_id = Column(String(100), nullable=True)
    
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)

    user = relationship("User")

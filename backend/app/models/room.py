import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class RoomType(str, enum.Enum):
    ICU = "ICU"
    GENERAL_WARD = "GENERAL_WARD"
    SEMI_PRIVATE = "SEMI_PRIVATE"
    PRIVATE = "PRIVATE"
    ISOLATION = "ISOLATION"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(50), nullable=False, index=True)  # e.g. "ICU-101", "RM-204"
    ward_id = Column(Integer, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)

    room_type = Column(
        SQLEnum(RoomType, values_callable=lambda obj: [e.value for e in obj]),
        default=RoomType.GENERAL_WARD,
        nullable=False,
    )
    has_oxygen_support = Column(Boolean, default=True, nullable=False)
    daily_rate = Column(Float, default=150.0, nullable=False)

    # Relationships
    ward = relationship("Ward", back_populates="rooms")
    beds = relationship("Bed", back_populates="room", cascade="all, delete-orphan")

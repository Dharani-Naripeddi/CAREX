import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class BedStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    CLEANING = "CLEANING"
    MAINTENANCE = "MAINTENANCE"


class Bed(Base):
    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True)
    bed_number = Column(String(50), nullable=False, unique=True, index=True)  # e.g. "ICU-BED-01", "SURG-BED-104"
    ward_id = Column(Integer, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True, index=True)

    status = Column(
        SQLEnum(BedStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=BedStatus.AVAILABLE,
        nullable=False,
        index=True,
    )

    has_oxygen_support = Column(Boolean, default=True, nullable=False)
    has_ventilator = Column(Boolean, default=False, nullable=False)
    current_admission_id = Column(Integer, ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    ward = relationship("Ward", back_populates="beds")
    room = relationship("Room", back_populates="beds")
    current_admission = relationship("Admission", foreign_keys=[current_admission_id], post_update=True)

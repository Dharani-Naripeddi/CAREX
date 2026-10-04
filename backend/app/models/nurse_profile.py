import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class ShiftEnum(str, enum.Enum):
    MORNING = "MORNING"    # 07:00 - 15:00
    EVENING = "EVENING"    # 15:00 - 23:00
    NIGHT = "NIGHT"        # 23:00 - 07:00
    ROTATING = "ROTATING"


class NurseProfile(Base):
    __tablename__ = "nurse_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)

    qualification = Column(String(150), nullable=False)  # e.g. "BSN, RN, CCRN"
    shift = Column(
        SQLEnum(ShiftEnum, values_callable=lambda obj: [e.value for e in obj]),
        default=ShiftEnum.MORNING,
        nullable=False,
    )
    ward_assigned = Column(String(100), nullable=True)  # e.g. "Ward 4B - Acute Cardiac Care"
    is_on_duty = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", backref="nurse_profile")
    department = relationship("Department", backref="nurses")

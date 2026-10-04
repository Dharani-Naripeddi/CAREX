import enum
from sqlalchemy import Column, Integer, String, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class RoleEnum(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    RECEPTIONIST = "RECEPTIONIST"
    PHARMACIST = "PHARMACIST"
    LAB_TECHNICIAN = "LAB_TECHNICIAN"
    PATIENT = "PATIENT"


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        SQLEnum(RoleEnum, values_callable=lambda obj: [e.value for e in obj]),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, default=list, nullable=False)

    users = relationship("User", back_populates="role", cascade="all, delete-orphan")

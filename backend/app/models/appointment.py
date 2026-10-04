import enum
from sqlalchemy import Column, Integer, String, Text, Date, Time, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CHECKED_IN = "CHECKED_IN"
    WAITING = "WAITING"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class AppointmentType(str, enum.Enum):
    OPD = "OPD"
    EMERGENCY = "EMERGENCY"
    FOLLOW_UP = "FOLLOW_UP"
    ROUTINE_CHECKUP = "ROUTINE_CHECKUP"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. APT-2026-0001

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)

    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(String(10), nullable=False)  # e.g. "10:30"

    type = Column(
        SQLEnum(AppointmentType, values_callable=lambda obj: [e.value for e in obj]),
        default=AppointmentType.OPD,
        nullable=False,
    )
    status = Column(
        SQLEnum(AppointmentStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
        index=True,
    )

    chief_complaint = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("User", foreign_keys=[doctor_id])
    department = relationship("Department")
    created_by = relationship("User", foreign_keys=[created_by_id])
    tokens = relationship("OpdToken", back_populates="appointment")

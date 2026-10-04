import enum
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class TokenStatus(str, enum.Enum):
    ISSUED = "ISSUED"        # Waiting in queue
    CALLED = "CALLED"        # Doctor/Nurse paged token
    IN_ROOM = "IN_ROOM"      # Currently in consultation room
    SERVICED = "SERVICED"    # Consultation completed
    SKIPPED = "SKIPPED"      # Patient did not respond
    CANCELLED = "CANCELLED"  # Token revoked


class TokenPriority(str, enum.Enum):
    NORMAL = "NORMAL"
    URGENT = "URGENT"
    STAT = "STAT"


class OpdToken(Base):
    __tablename__ = "opd_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_number = Column(Integer, nullable=False, index=True)  # Daily sequence: 1, 2, 3...
    token_code = Column(String(50), nullable=False, index=True)  # Display code: e.g. "CARD-001"
    date = Column(Date, nullable=False, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)

    priority = Column(
        SQLEnum(TokenPriority, values_callable=lambda obj: [e.value for e in obj]),
        default=TokenPriority.NORMAL,
        nullable=False,
    )
    status = Column(
        SQLEnum(TokenStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=TokenStatus.ISSUED,
        nullable=False,
        index=True,
    )

    estimated_wait_minutes = Column(Integer, default=15, nullable=False)
    called_at = Column(DateTime(timezone=True), nullable=True)
    serviced_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="tokens")
    doctor = relationship("User", foreign_keys=[doctor_id])
    department = relationship("Department")
    appointment = relationship("Appointment", back_populates="tokens")

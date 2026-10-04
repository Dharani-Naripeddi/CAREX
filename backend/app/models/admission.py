import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class AdmissionStatus(str, enum.Enum):
    ADMITTED = "ADMITTED"
    TRANSFERRED = "TRANSFERRED"
    DISCHARGED = "DISCHARGED"


class DischargeCondition(str, enum.Enum):
    RECOVERED = "RECOVERED"
    IMPROVED = "IMPROVED"
    STABLE = "STABLE"
    TRANSFERRED_EXTERNAL = "TRANSFERRED_EXTERNAL"
    AGAINST_MEDICAL_ADVICE = "AGAINST_MEDICAL_ADVICE"
    DECEASED = "DECEASED"


class Admission(Base):
    __tablename__ = "admissions"

    id = Column(Integer, primary_key=True, index=True)
    admission_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. ADM-2026-0001

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    admitting_doctor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id", ondelete="RESTRICT"), nullable=False, index=True)
    bed_id = Column(Integer, ForeignKey("beds.id", ondelete="RESTRICT"), nullable=False, index=True)

    admission_date = Column(DateTime(timezone=True), nullable=False, index=True)
    discharge_date = Column(DateTime(timezone=True), nullable=True)

    admission_reason = Column(Text, nullable=False)
    expected_stay_days = Column(Integer, default=3, nullable=False)
    status = Column(
        SQLEnum(AdmissionStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=AdmissionStatus.ADMITTED,
        nullable=False,
        index=True,
    )

    emergency_case_id = Column(Integer, ForeignKey("emergency_cases.id", ondelete="SET NULL"), nullable=True)

    # Discharge Summary details
    discharge_diagnosis = Column(Text, nullable=True)
    discharge_summary = Column(Text, nullable=True)
    discharge_condition = Column(
        SQLEnum(DischargeCondition, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
    )
    discharge_medications = Column(JSON, default=list, nullable=True)
    follow_up_instructions = Column(Text, nullable=True)
    discharged_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    patient = relationship("Patient", backref="admissions")
    admitting_doctor = relationship("User", foreign_keys=[admitting_doctor_id])
    discharged_by = relationship("User", foreign_keys=[discharged_by_id])
    ward = relationship("Ward")
    bed = relationship("Bed", foreign_keys=[bed_id])
    emergency_case = relationship("EmergencyCase", foreign_keys=[emergency_case_id], back_populates="admission")
    transfers = relationship("BedTransfer", back_populates="admission", cascade="all, delete-orphan")

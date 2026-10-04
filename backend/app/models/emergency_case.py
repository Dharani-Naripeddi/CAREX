import enum
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class TriageLevel(str, enum.Enum):
    RED = "RED"          # Immediate / Resuscitation
    ORANGE = "ORANGE"    # Emergent / Very Urgent
    YELLOW = "YELLOW"    # Urgent
    GREEN = "GREEN"      # Non-Urgent


class ConsciousnessLevel(str, enum.Enum):
    ALERT = "ALERT"                # Fully awake & oriented
    VOICE = "VOICE"                # Responds to vocal stimuli
    PAIN = "PAIN"                  # Responds to painful stimuli only
    UNRESPONSIVE = "UNRESPONSIVE"  # Comatose / Unresponsive


class EmergencyCaseStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"              # Arrived in ER
    TRIAGED = "TRIAGED"            # Triage evaluated & prioritized
    ADMITTED_IPD = "ADMITTED_IPD"  # Admitted to Inpatient / ICU
    DISCHARGED = "DISCHARGED"      # Treated and discharged
    DECEASED = "DECEASED"


class EmergencyCase(Base):
    __tablename__ = "emergency_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. EMR-2026-0001

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    patient_name = Column(String(150), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    arrival_time = Column(DateTime(timezone=True), nullable=False, index=True)

    symptoms = Column(Text, nullable=False)
    injury_type = Column(String(150), nullable=True)  # e.g. "Severe MVC Blunt Chest Trauma", "None / Medical"

    # Vital Signs
    heart_rate = Column(Integer, nullable=False)       # bpm (e.g. 142)
    bp_systolic = Column(Integer, nullable=False)      # mmHg (e.g. 85)
    bp_diastolic = Column(Integer, nullable=False)     # mmHg (e.g. 50)
    spo2 = Column(Float, nullable=False)               # % (e.g. 88.0)
    temperature = Column(Float, nullable=False)        # °C (e.g. 38.8)
    respiratory_rate = Column(Integer, nullable=False) # breaths/min (e.g. 32)
    consciousness = Column(
        SQLEnum(ConsciousnessLevel, values_callable=lambda obj: [e.value for e in obj]),
        default=ConsciousnessLevel.ALERT,
        nullable=False,
    )

    # Rule-Based Triage Decision Support Output
    triage_level = Column(
        SQLEnum(TriageLevel, values_callable=lambda obj: [e.value for e in obj]),
        default=TriageLevel.YELLOW,
        nullable=False,
        index=True,
    )
    contributing_factors = Column(JSON, default=list, nullable=False)
    recommended_action = Column(Text, nullable=False)
    triage_notes = Column(Text, nullable=True)

    status = Column(
        SQLEnum(EmergencyCaseStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=EmergencyCaseStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    doctor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    nurse_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    patient = relationship("Patient", backref="emergency_cases")
    doctor = relationship("User", foreign_keys=[doctor_id])
    nurse = relationship("User", foreign_keys=[nurse_id])
    admission = relationship("Admission", back_populates="emergency_case", uselist=False)

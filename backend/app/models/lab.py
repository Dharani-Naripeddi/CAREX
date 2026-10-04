import enum
import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    JSON,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class LabOrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    SAMPLE_COLLECTED = "SAMPLE_COLLECTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    CANCELLED = "CANCELLED"


class LabOrderPriority(str, enum.Enum):
    NORMAL = "NORMAL"
    URGENT = "URGENT"
    STAT = "STAT"


class LabResultFlag(str, enum.Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LabReportStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    ARCHIVED = "ARCHIVED"


class LabTest(Base):
    __tablename__ = "lab_tests"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # e.g. CBC, GLU_R, LIPID_PANEL
    name = Column(String(200), nullable=False, index=True)  # e.g. Complete Blood Count
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    category = Column(String(100), nullable=False, default="Hematology", index=True)  # Hematology, Biochemistry, etc.
    description = Column(Text, nullable=True)
    sample_type = Column(String(100), nullable=False, default="Whole Blood (EDTA)")  # Serum, Plasma, Urine, etc.
    normal_range = Column(String(255), nullable=True)  # General reference string
    unit = Column(String(50), nullable=True)  # Default unit if single parameter
    price = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Structured parameter definitions for structured entry & calculation
    # Format: [{"name": "Hemoglobin", "unit": "g/dL", "min_val": 13.5, "max_val": 17.5, "critical_low": 7.0, "critical_high": 20.0}]
    parameters = Column(JSON, default=list, nullable=False)

    department = relationship("Department")
    orders = relationship("LabOrder", back_populates="test")


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. LAB-2026-0001
    
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey("lab_tests.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Linkages with clinical encounters
    admission_id = Column(Integer, ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)
    emergency_case_id = Column(Integer, ForeignKey("emergency_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    
    priority = Column(
        SQLEnum(LabOrderPriority, values_callable=lambda obj: [e.value for e in obj]),
        default=LabOrderPriority.NORMAL,
        nullable=False,
        index=True,
    )
    status = Column(
        SQLEnum(LabOrderStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=LabOrderStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    clinical_notes = Column(Text, nullable=True)
    sample_type = Column(String(100), nullable=True)
    
    # Workflow timestamps & actors
    order_date = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    sample_collected_at = Column(DateTime(timezone=True), nullable=True)
    collected_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    completed_at = Column(DateTime(timezone=True), nullable=True)
    performed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    cancellation_reason = Column(Text, nullable=True)

    # Relationships
    patient = relationship("Patient", backref="lab_orders")
    doctor = relationship("User", foreign_keys=[doctor_id])
    test = relationship("LabTest", back_populates="orders")
    collected_by = relationship("User", foreign_keys=[collected_by_id])
    performed_by = relationship("User", foreign_keys=[performed_by_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    
    result = relationship("LabResult", back_populates="order", uselist=False, cascade="all, delete-orphan")
    report = relationship("LabReport", back_populates="order", uselist=False, cascade="all, delete-orphan")


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    technician_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    result_summary = Column(Text, nullable=True)
    technician_notes = Column(Text, nullable=True)  # Internal notes (hidden from patient)
    is_abnormal = Column(Boolean, default=False, nullable=False)
    is_critical = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    order = relationship("LabOrder", back_populates="result")
    patient = relationship("Patient")
    technician = relationship("User", foreign_keys=[technician_id])
    parameters = relationship("LabResultParameter", back_populates="lab_result", cascade="all, delete-orphan")


class LabResultParameter(Base):
    __tablename__ = "lab_result_parameters"

    id = Column(Integer, primary_key=True, index=True)
    lab_result_id = Column(Integer, ForeignKey("lab_results.id", ondelete="CASCADE"), nullable=False, index=True)
    
    parameter_name = Column(String(150), nullable=False)
    result_value = Column(String(100), nullable=False)  # String representation e.g. "14.2" or "Negative"
    numeric_value = Column(Float, nullable=True)       # For range computations
    unit = Column(String(50), nullable=True)
    reference_range = Column(String(100), nullable=True)
    
    flag = Column(
        SQLEnum(LabResultFlag, values_callable=lambda obj: [e.value for e in obj]),
        default=LabResultFlag.NORMAL,
        nullable=False,
    )
    is_critical = Column(Boolean, default=False, nullable=False)

    lab_result = relationship("LabResult", back_populates="parameters")


class LabReport(Base):
    __tablename__ = "lab_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. RPT-2026-0001
    order_id = Column(Integer, ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    lab_result_id = Column(Integer, ForeignKey("lab_results.id", ondelete="CASCADE"), nullable=False, index=True)
    
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    technician_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    verified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    report_date = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    status = Column(
        SQLEnum(LabReportStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=LabReportStatus.DRAFT,
        nullable=False,
    )
    
    clinical_impression = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    print_html = Column(Text, nullable=True)  # Pre-compiled HTML layout for rapid printing/viewing

    # Relationships
    order = relationship("LabOrder", back_populates="report")
    lab_result = relationship("LabResult")
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    technician = relationship("User", foreign_keys=[technician_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])

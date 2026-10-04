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
    Date,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class PharmacyTransactionType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    DISPENSE = "DISPENSE"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN = "RETURN"
    EXPIRED = "EXPIRED"
    DAMAGED = "DAMAGED"


class PrescriptionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARTIALLY_DISPENSED = "PARTIALLY_DISPENSED"
    DISPENSED = "DISPENSED"
    CANCELLED = "CANCELLED"


class PrescriptionItemStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARTIALLY_DISPENSED = "PARTIALLY_DISPENSED"
    DISPENSED = "DISPENSED"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # e.g. MED-001
    name = Column(String(200), nullable=False, index=True)  # e.g. Atorvastatin 20mg
    generic_name = Column(String(200), nullable=False, index=True)  # e.g. Atorvastatin Calcium
    category = Column(String(100), nullable=False, index=True)  # Cardiovascular, Antibiotics, etc.
    manufacturer = Column(String(200), nullable=True)
    unit = Column(String(50), nullable=False, default="Tablets")  # Tablets, Capsules, Syrup, Vials
    
    reorder_level = Column(Integer, nullable=False, default=50)
    max_stock_level = Column(Integer, nullable=False, default=500)
    unit_price = Column(Float, nullable=False, default=0.0)  # Default base selling price
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    batches = relationship("MedicineBatch", back_populates="medicine", cascade="all, delete-orphan")
    transactions = relationship("PharmacyTransaction", back_populates="medicine")


class MedicineBatch(Base):
    __tablename__ = "medicine_batches"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_number = Column(String(100), nullable=False, index=True)  # e.g. BATCH-2026-A1
    
    quantity = Column(Integer, nullable=False, default=0)  # Current stock in this batch
    initial_quantity = Column(Integer, nullable=False, default=0)
    purchase_price = Column(Float, nullable=False, default=0.0)
    selling_price = Column(Float, nullable=False, default=0.0)
    
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False, index=True)
    supplier = Column(String(200), nullable=True)
    storage_location = Column(String(100), nullable=True, default="Main Pharmacy Shelf A-1")
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    medicine = relationship("Medicine", back_populates="batches")
    transactions = relationship("PharmacyTransaction", back_populates="batch")


class PharmacyTransaction(Base):
    __tablename__ = "pharmacy_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. TXN-2026-0001
    
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("medicine_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    
    transaction_type = Column(
        SQLEnum(PharmacyTransactionType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
    )
    
    quantity = Column(Integer, nullable=False)  # Quantity delta (+ for purchase/return, - for dispense/expired)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    
    reference_type = Column(String(50), nullable=True)  # PRESCRIPTION, DISPENSE, PURCHASE_ORDER, MANUAL_ADJUSTMENT
    reference_id = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    performed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)

    medicine = relationship("Medicine", back_populates="transactions")
    batch = relationship("MedicineBatch", back_populates="transactions")
    performed_by = relationship("User")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    prescription_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. RX-2026-0001
    
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)
    emergency_case_id = Column(Integer, ForeignKey("emergency_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    
    diagnosis = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(
        SQLEnum(PrescriptionStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=PrescriptionStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    patient = relationship("Patient", backref="prescriptions")
    doctor = relationship("User", foreign_keys=[doctor_id])
    appointment = relationship("Appointment")
    admission = relationship("Admission")
    emergency_case = relationship("EmergencyCase")
    
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")
    dispensings = relationship("Dispensing", back_populates="prescription")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    dosage = Column(String(100), nullable=False)  # e.g. "500mg" or "20mg"
    frequency = Column(String(100), nullable=False)  # e.g. "1-0-1 (Twice daily after meals)"
    duration = Column(String(100), nullable=False)  # e.g. "7 days" or "1 month"
    quantity_prescribed = Column(Integer, nullable=False, default=1)
    quantity_dispensed = Column(Integer, nullable=False, default=0)
    instructions = Column(Text, nullable=True)
    
    status = Column(
        SQLEnum(PrescriptionItemStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=PrescriptionItemStatus.PENDING,
        nullable=False,
    )

    prescription = relationship("Prescription", back_populates="items")
    medicine = relationship("Medicine")


class Dispensing(Base):
    __tablename__ = "dispensings"

    id = Column(Integer, primary_key=True, index=True)
    dispensing_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. DSP-2026-0001
    
    prescription_id = Column(Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    total_amount = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    prescription = relationship("Prescription", back_populates="dispensings")
    patient = relationship("Patient")
    pharmacist = relationship("User", foreign_keys=[pharmacist_id])
    items = relationship("DispensingItem", back_populates="dispensing", cascade="all, delete-orphan")


class DispensingItem(Base):
    __tablename__ = "dispensing_items"

    id = Column(Integer, primary_key=True, index=True)
    dispensing_id = Column(Integer, ForeignKey("dispensings.id", ondelete="CASCADE"), nullable=False, index=True)
    prescription_item_id = Column(Integer, ForeignKey("prescription_items.id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(Integer, ForeignKey("medicine_batches.id", ondelete="RESTRICT"), nullable=False)
    
    quantity_dispensed = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    dispensing = relationship("Dispensing", back_populates="items")
    prescription_item = relationship("PrescriptionItem")
    medicine = relationship("Medicine")
    batch = relationship("MedicineBatch")

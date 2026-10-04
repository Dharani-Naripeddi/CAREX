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


class BillingCategory(str, enum.Enum):
    CONSULTATION = "CONSULTATION"
    ROOM = "ROOM"
    LAB = "LAB"
    MEDICINE = "MEDICINE"
    PROCEDURE = "PROCEDURE"
    OTHER = "OTHER"


class InvoicePaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    CARD = "CARD"
    UPI = "UPI"
    OTHER = "OTHER"


class BillingItem(Base):
    __tablename__ = "billing_items"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # e.g. SRV-CONSULT, SRV-ROOM-ICU
    name = Column(String(200), nullable=False, index=True)  # e.g. Cardiologist Specialist Consultation
    
    category = Column(
        SQLEnum(BillingCategory, values_callable=lambda obj: [e.value for e in obj]),
        default=BillingCategory.CONSULTATION,
        nullable=False,
        index=True,
    )
    
    unit_price = Column(Float, nullable=False, default=0.0)
    tax_percent = Column(Float, nullable=False, default=0.0)  # e.g. 5.0 for 5%
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. INV-2026-0001
    
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)
    emergency_case_id = Column(Integer, ForeignKey("emergency_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    
    date = Column(Date, default=datetime.date.today, nullable=False)
    due_date = Column(Date, nullable=True)
    
    subtotal = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    paid_amount = Column(Float, nullable=False, default=0.0)
    balance_amount = Column(Float, nullable=False, default=0.0)
    
    payment_status = Column(
        SQLEnum(InvoicePaymentStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=InvoicePaymentStatus.UNPAID,
        nullable=False,
        index=True,
    )
    
    notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    patient = relationship("Patient", backref="invoices")
    appointment = relationship("Appointment")
    admission = relationship("Admission")
    emergency_case = relationship("EmergencyCase")
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    billing_item_id = Column(Integer, ForeignKey("billing_items.id", ondelete="SET NULL"), nullable=True)
    
    description = Column(String(255), nullable=False)
    category = Column(
        SQLEnum(BillingCategory, values_callable=lambda obj: [e.value for e in obj]),
        default=BillingCategory.OTHER,
        nullable=False,
    )
    
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    discount = Column(Float, nullable=False, default=0.0)
    tax_percent = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    
    # Traceability back to source clinical event (to avoid duplicate billing)
    reference_type = Column(String(50), nullable=True)  # LAB_ORDER, PRESCRIPTION, DISPENSING, ADMISSION_ROOM, CONSULTATION
    reference_id = Column(String(100), nullable=True)

    invoice = relationship("Invoice", back_populates="items")
    billing_item = relationship("BillingItem")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. PAY-2026-0001
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    payment_method = Column(
        SQLEnum(PaymentMethod, values_callable=lambda obj: [e.value for e in obj]),
        default=PaymentMethod.CASH,
        nullable=False,
    )
    
    reference_number = Column(String(100), nullable=True)  # Transaction ID, Cheque #, UPI ID
    notes = Column(Text, nullable=True)
    payment_date = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    recorded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    invoice = relationship("Invoice", back_populates="payments")
    patient = relationship("Patient")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])

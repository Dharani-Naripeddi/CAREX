import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.billing import (
    BillingCategory,
    InvoicePaymentStatus,
    PaymentMethod,
)


# Billing Item Schemas
class BillingItemBase(BaseModel):
    code: str
    name: str
    category: BillingCategory = BillingCategory.CONSULTATION
    unit_price: float = 0.0
    tax_percent: float = 0.0
    description: Optional[str] = None
    is_active: bool = True


class BillingItemCreate(BillingItemBase):
    pass


class BillingItemResponse(BillingItemBase):
    id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# Invoice Item Schemas
class InvoiceItemInput(BaseModel):
    billing_item_id: Optional[int] = None
    description: str
    category: BillingCategory = BillingCategory.OTHER
    quantity: float = 1.0
    unit_price: float
    discount: float = 0.0
    tax_percent: float = 0.0
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None


class InvoiceItemResponse(BaseModel):
    id: int
    invoice_id: int
    billing_item_id: Optional[int] = None
    description: str
    category: BillingCategory
    quantity: float
    unit_price: float
    discount: float
    tax_percent: float
    total_price: float
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Payment Schemas
class PaymentCreate(BaseModel):
    amount: float
    payment_method: PaymentMethod = PaymentMethod.CASH
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    payment_number: str
    invoice_id: int
    patient_id: int
    patient_name: Optional[str] = None
    amount: float
    payment_method: PaymentMethod
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    payment_date: datetime.datetime
    recorded_by_id: Optional[int] = None
    recorded_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Invoice Schemas
class InvoiceCreate(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    admission_id: Optional[int] = None
    emergency_case_id: Optional[int] = None
    due_date: Optional[datetime.date] = None
    notes: Optional[str] = None
    items: List[InvoiceItemInput] = []


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    patient_id: int
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    patient_address: Optional[str] = None
    
    appointment_id: Optional[int] = None
    admission_id: Optional[int] = None
    emergency_case_id: Optional[int] = None
    
    date: datetime.date
    due_date: Optional[datetime.date] = None
    
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    balance_amount: float
    payment_status: InvoicePaymentStatus
    
    notes: Optional[str] = None
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: datetime.datetime
    
    items: List[InvoiceItemResponse] = []
    payments: List[PaymentResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Summary Schemas for Inpatient & Operations
class AdmissionDischargeBillingSummary(BaseModel):
    admission_id: int
    admission_number: str
    patient_id: int
    patient_name: str
    stay_days: int
    daily_room_rate: float
    room_charges_total: float
    lab_charges_total: float
    pharmacy_charges_total: float
    procedure_charges_total: float
    other_charges_total: float
    estimated_subtotal: float
    estimated_tax: float
    estimated_total: float
    existing_invoices_count: int
    unpaid_balance: float


class BillingDashboardStats(BaseModel):
    today_revenue: float = 0.0
    month_revenue: float = 0.0
    outstanding_bills_count: int = 0
    total_unpaid_amount: float = 0.0
    today_invoices_count: int = 0
    today_payments_count: int = 0

import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict
from app.models.pharmacy import (
    PharmacyTransactionType,
    PrescriptionStatus,
    PrescriptionItemStatus,
)


# Medicine Schemas
class MedicineBase(BaseModel):
    code: str
    name: str
    generic_name: str
    category: str
    manufacturer: Optional[str] = None
    unit: str = "Tablets"
    reorder_level: int = 50
    max_stock_level: int = 500
    unit_price: float = 0.0
    is_active: bool = True


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    generic_name: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    unit: Optional[str] = None
    reorder_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    unit_price: Optional[float] = None
    is_active: Optional[bool] = None


class MedicineBatchResponse(BaseModel):
    id: int
    medicine_id: int
    batch_number: str
    quantity: int
    initial_quantity: int
    purchase_price: float
    selling_price: float
    manufacturing_date: Optional[datetime.date] = None
    expiry_date: datetime.date
    days_to_expiry: Optional[int] = None
    expiry_status: Optional[str] = None  # EXPIRED, EXPIRING_7_DAYS, EXPIRING_30_DAYS, EXPIRING_90_DAYS, VALID
    risk_level: Optional[str] = None  # HIGH, MEDIUM, LOW
    supplier: Optional[str] = None
    storage_location: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class MedicineResponse(MedicineBase):
    id: int
    total_stock: int = 0
    batches_count: int = 0
    is_low_stock: bool = False
    suggested_reorder_qty: int = 0
    batches: List[MedicineBatchResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MedicineBatchCreate(BaseModel):
    medicine_id: int
    batch_number: str
    quantity: int
    purchase_price: float
    selling_price: float
    manufacturing_date: Optional[datetime.date] = None
    expiry_date: datetime.date
    supplier: Optional[str] = None
    storage_location: Optional[str] = "Main Pharmacy Shelf A-1"


# Pharmacy Transaction Schemas
class PharmacyTransactionCreate(BaseModel):
    medicine_id: int
    batch_id: Optional[int] = None
    transaction_type: PharmacyTransactionType
    quantity: int
    unit_price: Optional[float] = 0.0
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None


class PharmacyTransactionResponse(BaseModel):
    id: int
    transaction_number: str
    medicine_id: int
    medicine_name: Optional[str] = None
    medicine_code: Optional[str] = None
    batch_id: Optional[int] = None
    batch_number: Optional[str] = None
    transaction_type: PharmacyTransactionType
    quantity: int
    unit_price: float
    total_amount: float
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    performed_by_id: Optional[int] = None
    performed_by_name: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# Prescription Schemas
class PrescriptionItemCreate(BaseModel):
    medicine_id: int
    dosage: str
    frequency: str
    duration: str
    quantity_prescribed: int
    instructions: Optional[str] = None


class PrescriptionItemResponse(BaseModel):
    id: int
    prescription_id: int
    medicine_id: int
    medicine_name: Optional[str] = None
    medicine_code: Optional[str] = None
    medicine_unit: Optional[str] = None
    unit_price: Optional[float] = None
    available_stock: Optional[int] = None
    dosage: str
    frequency: str
    duration: str
    quantity_prescribed: int
    quantity_dispensed: int
    instructions: Optional[str] = None
    status: PrescriptionItemStatus

    model_config = ConfigDict(from_attributes=True)


class PrescriptionCreate(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    admission_id: Optional[int] = None
    emergency_case_id: Optional[int] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    items: List[PrescriptionItemCreate]


class PrescriptionResponse(BaseModel):
    id: int
    prescription_number: str
    patient_id: int
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    doctor_id: int
    doctor_name: Optional[str] = None
    appointment_id: Optional[int] = None
    admission_id: Optional[int] = None
    emergency_case_id: Optional[int] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    status: PrescriptionStatus
    created_at: datetime.datetime
    items: List[PrescriptionItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Dispensing Schemas
class DispenseItemPayload(BaseModel):
    prescription_item_id: int
    batch_id: int
    quantity: int


class DispensePayload(BaseModel):
    prescription_id: int
    items: List[DispenseItemPayload]
    notes: Optional[str] = None


class DispensingResponse(BaseModel):
    id: int
    dispensing_number: str
    prescription_id: int
    prescription_number: Optional[str] = None
    patient_id: int
    patient_name: Optional[str] = None
    pharmacist_id: int
    pharmacist_name: Optional[str] = None
    total_amount: float
    notes: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# Expiry & Low Stock Dashboard Schemas
class ExpiryClassificationItem(BaseModel):
    medicine_id: int
    medicine_name: str
    medicine_code: str
    batch_id: int
    batch_number: str
    quantity: int
    expiry_date: datetime.date
    days_remaining: int
    category: str  # EXPIRED, EXPIRING_WITHIN_7_DAYS, EXPIRING_WITHIN_30_DAYS, EXPIRING_WITHIN_90_DAYS
    risk_level: str  # HIGH, MEDIUM, LOW


class LowStockAlertItem(BaseModel):
    medicine_id: int
    medicine_name: str
    medicine_code: str
    category: str
    current_stock: int
    reorder_level: int
    max_stock_level: int
    suggested_reorder_qty: int
    unit: str


class PharmacyDashboardStats(BaseModel):
    total_medicines: int = 0
    total_stock_units: int = 0
    low_stock_count: int = 0
    expiring_soon_count: int = 0
    expired_count: int = 0
    today_dispensed_count: int = 0
    today_dispensed_amount: float = 0.0

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.models.pharmacy import PrescriptionStatus, PharmacyTransactionType
from app.schemas.pharmacy import (
    MedicineCreate,
    MedicineResponse,
    MedicineBatchCreate,
    MedicineBatchResponse,
    PharmacyTransactionResponse,
    PrescriptionCreate,
    PrescriptionResponse,
    DispensePayload,
    DispensingResponse,
    ExpiryClassificationItem,
    LowStockAlertItem,
    PharmacyDashboardStats,
)
from app.services.pharmacy_service import PharmacyService

router = APIRouter()


@router.get("/medicines", response_model=List[MedicineResponse], summary="List medicines and stock status")
def list_medicines(
    category: Optional[str] = Query(None, description="Filter by category"),
    query: Optional[str] = Query(None, description="Search by name or code"),
    low_stock_only: bool = False,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve medicines directory with live batch inventories and stock statuses."""
    return PharmacyService.get_medicines(
        db=db,
        category=category,
        query_str=query,
        low_stock_only=low_stock_only,
        active_only=active_only,
    )


@router.post(
    "/medicines",
    response_model=MedicineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new medicine to catalogue",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN, RoleEnum.PHARMACIST))],
)
def create_medicine(
    med_in: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a new medication SKU to the pharmacy directory."""
    med = PharmacyService.create_medicine(db=db, med_in=med_in, user_id=current_user.id)
    return PharmacyService.get_medicine_by_id(db, med.id)


@router.post(
    "/batches",
    response_model=MedicineBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receive new medicine batch into inventory",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN, RoleEnum.PHARMACIST))],
)
def add_batch(
    batch_in: MedicineBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Register a new batch intake with purchase transaction."""
    return PharmacyService.add_batch(db=db, batch_in=batch_in, user_id=current_user.id)


@router.get("/expiry", response_model=List[ExpiryClassificationItem], summary="Get medicine batches expiry classification")
def get_expiry_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Classify all active batches into EXPIRED, 7_DAYS, 30_DAYS, and 90_DAYS risk categories."""
    return PharmacyService.get_expiry_classification(db=db)


@router.get("/low-stock", response_model=List[LowStockAlertItem], summary="Get low stock alerts & reorder suggestions")
def get_low_stock_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve medicines currently at or below configured reorder levels."""
    return PharmacyService.get_low_stock_alerts(db=db)


@router.get("/transactions", response_model=List[PharmacyTransactionResponse], summary="List pharmacy stock audit ledger")
def list_transactions(
    medicine_id: Optional[int] = Query(None, description="Filter by medicine"),
    transaction_type: Optional[PharmacyTransactionType] = Query(None, description="Filter by transaction type"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Audit ledger of all stock purchases, dispensations, adjustments, and returns."""
    txns = PharmacyService.get_transactions(
        db=db,
        medicine_id=medicine_id,
        transaction_type=transaction_type,
        skip=skip,
        limit=limit,
    )
    res = []
    for t in txns:
        resp = PharmacyTransactionResponse.model_validate(t)
        if t.medicine:
            resp.medicine_name = t.medicine.name
            resp.medicine_code = t.medicine.code
        if t.batch:
            resp.batch_number = t.batch.batch_number
        if t.performed_by:
            resp.performed_by_name = t.performed_by.full_name
        res.append(resp)
    return res


@router.get("/prescriptions", response_model=List[PrescriptionResponse], summary="List doctor prescriptions")
def list_prescriptions(
    status: Optional[PrescriptionStatus] = Query(None, description="Filter by status"),
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve doctor prescriptions with itemized dosages and dispensing statuses."""
    if current_user.role and current_user.role.name == RoleEnum.PATIENT:
        from app.models.patient import Patient
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if pat:
            patient_id = pat.id

    prescriptions = PharmacyService.get_prescriptions(
        db=db,
        status_filter=status,
        patient_id=patient_id,
        doctor_id=doctor_id,
        skip=skip,
        limit=limit,
    )
    res = []
    for p in prescriptions:
        resp = PrescriptionResponse.model_validate(p)
        if p.patient:
            resp.patient_name = p.patient.full_name
            resp.patient_mrn = p.patient.mrn
        if p.doctor:
            resp.doctor_name = p.doctor.full_name
        for i, itm in enumerate(p.items):
            if itm.medicine:
                resp.items[i].medicine_name = itm.medicine.name
                resp.items[i].medicine_code = itm.medicine.code
                resp.items[i].medicine_unit = itm.medicine.unit
                resp.items[i].unit_price = itm.medicine.unit_price
        res.append(resp)
    return res


@router.post(
    "/prescriptions",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new prescription order",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.DOCTOR,
            )
        )
    ],
)
def create_prescription(
    rx_in: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Doctor creates an e-prescription order with medication items."""
    prescription = PharmacyService.create_prescription(db=db, rx_in=rx_in, doctor_id=current_user.id)
    resp = PrescriptionResponse.model_validate(prescription)
    if prescription.patient:
        resp.patient_name = prescription.patient.full_name
        resp.patient_mrn = prescription.patient.mrn
    if prescription.doctor:
        resp.doctor_name = prescription.doctor.full_name
    for i, itm in enumerate(prescription.items):
        if itm.medicine:
            resp.items[i].medicine_name = itm.medicine.name
            resp.items[i].medicine_code = itm.medicine.code
            resp.items[i].medicine_unit = itm.medicine.unit
            resp.items[i].unit_price = itm.medicine.unit_price
    return resp


@router.post(
    "/dispense",
    response_model=DispensingResponse,
    status_code=status.HTTP_200_OK,
    summary="Dispense prescription medications with batch stock deduction",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN, RoleEnum.PHARMACIST))],
)
def dispense_prescription(
    dispense_in: DispensePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Execute atomic dispensing: checks stock/expiry, decrements batch quantities, logs transactions."""
    dispensing = PharmacyService.dispense_prescription(db=db, dispense_in=dispense_in, pharmacist_id=current_user.id)
    resp = DispensingResponse.model_validate(dispensing)
    if dispensing.prescription:
        resp.prescription_number = dispensing.prescription.prescription_number
    if dispensing.patient:
        resp.patient_name = dispensing.patient.full_name
    if dispensing.pharmacist:
        resp.pharmacist_name = dispensing.pharmacist.full_name
    return resp


@router.get("/dashboard-stats", response_model=PharmacyDashboardStats, summary="Get pharmacy telemetry metrics")
def get_pharmacy_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get live metrics: total medicines, total stock units, low stock count, expiry counts, today's dispensations."""
    return PharmacyService.get_dashboard_stats(db=db)

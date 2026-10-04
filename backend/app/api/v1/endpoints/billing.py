from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.models.billing import BillingCategory, InvoicePaymentStatus
from app.schemas.billing import (
    BillingItemCreate,
    BillingItemResponse,
    InvoiceCreate,
    InvoiceResponse,
    PaymentCreate,
    PaymentResponse,
    AdmissionDischargeBillingSummary,
    BillingDashboardStats,
)
from app.services.billing_service import BillingService

router = APIRouter()


@router.get("/items", response_model=List[BillingItemResponse], summary="List billable items and service rates")
def list_billing_items(
    category: Optional[BillingCategory] = Query(None, description="Filter by category"),
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve billable items rate sheet."""
    return BillingService.get_billing_items(db=db, category=category, active_only=active_only)


@router.post(
    "/items",
    response_model=BillingItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new billable item / service",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN, RoleEnum.RECEPTIONIST))],
)
def create_billing_item(
    item_in: BillingItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a new fee item or rate to the hospital billing master."""
    return BillingService.create_billing_item(db=db, item_in=item_in, user_id=current_user.id)


@router.get("/invoices", response_model=List[InvoiceResponse], summary="List patient invoices")
def list_invoices(
    status: Optional[InvoicePaymentStatus] = Query(None, description="Filter by payment status"),
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve hospital invoices with itemized charges and payment balances."""
    if current_user.role and current_user.role.name == RoleEnum.PATIENT:
        from app.models.patient import Patient
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if pat:
            patient_id = pat.id

    invoices = BillingService.get_invoices(
        db=db,
        status_filter=status,
        patient_id=patient_id,
        skip=skip,
        limit=limit,
    )
    return invoices


@router.post(
    "/invoices",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a patient invoice with itemized line items",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.RECEPTIONIST,
                RoleEnum.DOCTOR,
            )
        )
    ],
)
def create_invoice(
    invoice_in: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate invoice, calculate subtotal/discount/taxes, and notify patient."""
    return BillingService.create_invoice(db=db, invoice_in=invoice_in, user_id=current_user.id)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse, summary="Get full detailed invoice view")
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve full details of a specific invoice with items and payment receipts."""
    return BillingService.get_invoice_by_id(db=db, invoice_id=invoice_id)


@router.post(
    "/invoices/{invoice_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a payment for an invoice (Cash / Card / UPI)",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.RECEPTIONIST,
            )
        )
    ],
)
def record_payment(
    invoice_id: int,
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record patient payment against an outstanding invoice."""
    payment = BillingService.record_payment(db=db, invoice_id=invoice_id, payment_in=payment_in, user_id=current_user.id)
    resp = PaymentResponse.model_validate(payment)
    if payment.patient:
        resp.patient_name = payment.patient.full_name
    if payment.recorded_by:
        resp.recorded_by_name = payment.recorded_by.full_name
    return resp


@router.get(
    "/admissions/{admission_id}/summary",
    response_model=AdmissionDischargeBillingSummary,
    summary="Calculate comprehensive admission stay billing estimation",
)
def get_admission_billing_summary(
    admission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Aggregate room charges, lab orders, dispensed medications, and procedures for an inpatient stay."""
    return BillingService.calculate_admission_billing_summary(db=db, admission_id=admission_id)


@router.get("/dashboard-stats", response_model=BillingDashboardStats, summary="Get billing and revenue metrics")
def get_billing_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get live billing telemetry: today's revenue, month revenue, outstanding balances, unpaid count."""
    return BillingService.get_dashboard_stats(db=db)

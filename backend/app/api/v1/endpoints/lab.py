from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.models.lab import LabOrderStatus, LabOrderPriority
from app.schemas.lab import (
    LabTestCreate,
    LabTestResponse,
    LabOrderCreate,
    LabOrderResponse,
    LabResultEntryRequest,
    LabReportResponse,
    LabWorkloadSummary,
)
from app.services.lab_service import LabService

router = APIRouter()


@router.get("/tests", response_model=List[LabTestResponse], summary="List diagnostic laboratory tests")
def list_lab_tests(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve all diagnostic tests in the laboratory catalogue."""
    return LabService.get_tests(db=db, category=category, active_only=active_only)


@router.post(
    "/tests",
    response_model=LabTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new diagnostic test to catalogue",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN, RoleEnum.LAB_TECHNICIAN))],
)
def create_lab_test(
    test_in: LabTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new diagnostic test in the catalogue."""
    return LabService.create_test(db=db, test_in=test_in, user_id=current_user.id)


@router.get("/orders", response_model=List[LabOrderResponse], summary="List laboratory orders")
def list_lab_orders(
    status: Optional[LabOrderStatus] = Query(None, description="Filter by order status"),
    priority: Optional[LabOrderPriority] = Query(None, description="Filter by priority"),
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve laboratory test orders with optional filters."""
    # If role is PATIENT, restrict to current patient's orders
    if current_user.role and current_user.role.name == RoleEnum.PATIENT:
        from app.models.patient import Patient
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if pat:
            patient_id = pat.id

    orders = LabService.get_orders(
        db=db,
        status_filter=status,
        priority_filter=priority,
        patient_id=patient_id,
        doctor_id=doctor_id,
        skip=skip,
        limit=limit,
    )

    response_list = []
    for o in orders:
        resp = LabOrderResponse.model_validate(o)
        if o.patient:
            resp.patient_name = o.patient.full_name
            resp.patient_mrn = o.patient.mrn
            resp.patient_gender = o.patient.gender
            resp.patient_age = o.patient.age
        if o.doctor:
            resp.doctor_name = o.doctor.full_name
        if o.test:
            resp.test_name = o.test.name
            resp.test_code = o.test.code
            resp.test_category = o.test.category
            resp.test_price = o.test.price
        if o.report:
            resp.report_id = o.report.id
            resp.report_number = o.report.report_number
        response_list.append(resp)

    return response_list


@router.post(
    "/orders",
    response_model=LabOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Order diagnostic laboratory tests for a patient",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.DOCTOR,
                RoleEnum.NURSE,
            )
        )
    ],
)
def create_lab_order(
    order_in: LabOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Doctor or Clinical Staff places a lab order for a patient."""
    order = LabService.create_order(db=db, order_in=order_in, doctor_id=current_user.id)
    resp = LabOrderResponse.model_validate(order)
    if order.patient:
        resp.patient_name = order.patient.full_name
        resp.patient_mrn = order.patient.mrn
        resp.patient_gender = order.patient.gender
        resp.patient_age = order.patient.age
    if order.doctor:
        resp.doctor_name = order.doctor.full_name
    if order.test:
        resp.test_name = order.test.name
        resp.test_code = order.test.code
        resp.test_category = order.test.category
        resp.test_price = order.test.price
    return resp


@router.get("/orders/{order_id}", response_model=LabOrderResponse, summary="Get details of a lab order")
def get_lab_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve full details of a specific lab order including structured results."""
    order = LabService.get_order_by_id(db=db, order_id=order_id)
    resp = LabOrderResponse.model_validate(order)
    if order.patient:
        resp.patient_name = order.patient.full_name
        resp.patient_mrn = order.patient.mrn
        resp.patient_gender = order.patient.gender
        resp.patient_age = order.patient.age
    if order.doctor:
        resp.doctor_name = order.doctor.full_name
    if order.test:
        resp.test_name = order.test.name
        resp.test_code = order.test.code
        resp.test_category = order.test.category
        resp.test_price = order.test.price
    if order.report:
        resp.report_id = order.report.id
        resp.report_number = order.report.report_number
    return resp


@router.post(
    "/orders/{order_id}/collect-sample",
    response_model=LabOrderResponse,
    summary="Mark specimen collected for a lab order",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.LAB_TECHNICIAN,
                RoleEnum.NURSE,
            )
        )
    ],
)
def collect_sample(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Accession order and mark sample collected."""
    order = LabService.mark_sample_collected(db=db, order_id=order_id, technician_id=current_user.id)
    resp = LabOrderResponse.model_validate(order)
    if order.patient:
        resp.patient_name = order.patient.full_name
        resp.patient_mrn = order.patient.mrn
        resp.patient_gender = order.patient.gender
        resp.patient_age = order.patient.age
    if order.doctor:
        resp.doctor_name = order.doctor.full_name
    if order.test:
        resp.test_name = order.test.name
        resp.test_code = order.test.code
        resp.test_category = order.test.category
        resp.test_price = order.test.price
    return resp


@router.post(
    "/orders/{order_id}/start-test",
    response_model=LabOrderResponse,
    summary="Start analyzer processing for a lab order",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN, RoleEnum.LAB_TECHNICIAN))],
)
def start_test(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Transition order to IN_PROGRESS."""
    order = LabService.start_test(db=db, order_id=order_id, technician_id=current_user.id)
    resp = LabOrderResponse.model_validate(order)
    if order.patient:
        resp.patient_name = order.patient.full_name
        resp.patient_mrn = order.patient.mrn
        resp.patient_gender = order.patient.gender
        resp.patient_age = order.patient.age
    if order.doctor:
        resp.doctor_name = order.doctor.full_name
    if order.test:
        resp.test_name = order.test.name
        resp.test_code = order.test.code
        resp.test_category = order.test.category
        resp.test_price = order.test.price
    return resp


@router.post(
    "/orders/{order_id}/results",
    response_model=LabOrderResponse,
    summary="Enter structured test parameter results and calculate flags",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN, RoleEnum.LAB_TECHNICIAN))],
)
def enter_results(
    order_id: int,
    result_in: LabResultEntryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Enter parameter results with automatic reference-range flag calculations."""
    order = LabService.enter_results(db=db, order_id=order_id, result_in=result_in, technician_id=current_user.id)
    resp = LabOrderResponse.model_validate(order)
    if order.patient:
        resp.patient_name = order.patient.full_name
        resp.patient_mrn = order.patient.mrn
        resp.patient_gender = order.patient.gender
        resp.patient_age = order.patient.age
    if order.doctor:
        resp.doctor_name = order.doctor.full_name
    if order.test:
        resp.test_name = order.test.name
        resp.test_code = order.test.code
        resp.test_category = order.test.category
        resp.test_price = order.test.price
    return resp


@router.post(
    "/orders/{order_id}/verify",
    response_model=LabReportResponse,
    summary="Verify and officially release a laboratory diagnostic report",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.LAB_TECHNICIAN,
                RoleEnum.DOCTOR,
            )
        )
    ],
)
def verify_lab_report(
    order_id: int,
    clinical_impression: Optional[str] = None,
    conclusion: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Verify results and release official report to doctor and patient."""
    report = LabService.verify_report(
        db=db,
        order_id=order_id,
        verified_by_id=current_user.id,
        clinical_impression=clinical_impression,
        conclusion=conclusion,
    )
    resp = LabReportResponse.model_validate(report)
    if report.patient:
        resp.patient_name = report.patient.full_name
        resp.patient_mrn = report.patient.mrn
        resp.patient_age = report.patient.age
        resp.patient_gender = report.patient.gender
    if report.doctor:
        resp.doctor_name = report.doctor.full_name
    if report.technician:
        resp.technician_name = report.technician.full_name
    if report.verified_by:
        resp.verified_by_name = report.verified_by.full_name
    if report.order and report.order.test:
        resp.test_name = report.order.test.name
        resp.test_code = report.order.test.code
        resp.sample_type = report.order.sample_type
    if report.lab_result:
        resp.parameters = report.lab_result.parameters
    return resp


@router.get("/reports", response_model=List[LabReportResponse], summary="List released laboratory reports")
def list_lab_reports(
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve verified and released laboratory diagnostic reports."""
    # Filter for Patient role
    if current_user.role and current_user.role.name == RoleEnum.PATIENT:
        from app.models.patient import Patient
        pat = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if pat:
            patient_id = pat.id

    reports = LabService.get_reports(db=db, patient_id=patient_id, doctor_id=doctor_id, skip=skip, limit=limit)
    response_list = []
    for r in reports:
        resp = LabReportResponse.model_validate(r)
        if r.patient:
            resp.patient_name = r.patient.full_name
            resp.patient_mrn = r.patient.mrn
            resp.patient_age = r.patient.age
            resp.patient_gender = r.patient.gender
        if r.doctor:
            resp.doctor_name = r.doctor.full_name
        if r.technician:
            resp.technician_name = r.technician.full_name
        if r.verified_by:
            resp.verified_by_name = r.verified_by.full_name
        if r.order and r.order.test:
            resp.test_name = r.order.test.name
            resp.test_code = r.order.test.code
            resp.sample_type = r.order.sample_type
        if r.lab_result:
            resp.parameters = r.lab_result.parameters
        response_list.append(resp)

    return response_list


@router.get("/workload-summary", response_model=LabWorkloadSummary, summary="Get laboratory workload metrics")
def get_lab_workload_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get count of pending, in-progress, urgent, and completed tests for lab technician telemetry."""
    return LabService.get_workload_summary(db=db)

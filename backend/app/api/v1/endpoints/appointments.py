import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.role import RoleEnum
from app.models.user import User
from app.models.appointment import AppointmentStatus
from app.models.patient import Patient
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentStatusUpdate,
    AppointmentReschedule,
    AppointmentResponse,
    AppointmentWithDetails,
)
from app.services.appointment_service import AppointmentService

router = APIRouter()


@router.get(
    "/",
    response_model=List[AppointmentWithDetails],
    summary="List, search, and filter appointments",
)
def list_appointments(
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor user ID"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    date: Optional[datetime.date] = Query(None, description="Filter by appointment date (YYYY-MM-DD)"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve hospital appointment schedules and status queues."""
    # If logged in as Doctor, default filter to self unless admin
    if current_user.role and current_user.role.name == RoleEnum.DOCTOR and not doctor_id:
        doctor_id = current_user.id

    # If logged in as Patient, filter to self
    if current_user.role and current_user.role.name == RoleEnum.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            patient = db.query(Patient).filter(Patient.email == current_user.email).first()
        if patient:
            patient_id = patient.id
        else:
            return []

    return AppointmentService.get_appointments(
        db=db,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department_id,
        date=date,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a new appointment",
)
def create_appointment(
    app_in: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Schedule an outpatient or consultation appointment."""
    return AppointmentService.create_appointment(
        db=db,
        app_in=app_in,
        created_by_id=current_user.id,
    )


@router.put(
    "/{appointment_id}/status",
    response_model=AppointmentResponse,
    summary="Update appointment status (Checked in, Waiting, In consultation, Completed, Cancelled, No-Show)",
)
def update_status(
    appointment_id: int,
    status_in: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update appointment lifecycle status."""
    return AppointmentService.update_appointment_status(
        db=db,
        appointment_id=appointment_id,
        status_in=status_in,
        updated_by_id=current_user.id,
    )


@router.put(
    "/{appointment_id}/reschedule",
    response_model=AppointmentResponse,
    summary="Reschedule appointment date and time",
)
def reschedule(
    appointment_id: int,
    reschedule_in: AppointmentReschedule,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Change the scheduled date or time slot of an appointment."""
    return AppointmentService.reschedule_appointment(
        db=db,
        appointment_id=appointment_id,
        reschedule_in=reschedule_in,
        updated_by_id=current_user.id,
    )

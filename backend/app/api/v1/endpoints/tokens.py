from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.role import RoleEnum
from app.models.user import User
from app.models.patient import Patient
from app.schemas.opd_token import (
    TokenGenerateRequest,
    TokenResponse,
    TokenQueueStatus,
    PatientLiveTokenStatus,
)
from app.services.token_service import TokenService

router = APIRouter()


@router.post(
    "/generate",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a daily OPD queue token",
)
def generate_token(
    token_in: TokenGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate daily sequential token for OPD / Emergency intake."""
    return TokenService.generate_token(
        db=db,
        token_in=token_in,
        generated_by_id=current_user.id,
    )


@router.get(
    "/queue",
    response_model=TokenQueueStatus,
    summary="Get live OPD token queue status by department or doctor",
)
def get_queue(
    department_id: Optional[int] = Query(None, description="Department ID"),
    doctor_id: Optional[int] = Query(None, description="Doctor user ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Fetch current serving token, waiting patient queue, and count."""
    return TokenService.get_token_queue_status(
        db=db,
        department_id=department_id,
        doctor_id=doctor_id,
    )


@router.get(
    "/patient/{patient_id}/status",
    response_model=PatientLiveTokenStatus,
    summary="Get real-time token tracking status and wait time for a patient",
)
def get_patient_token_status(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns live token, currently called token, patients ahead count, and estimated wait minutes."""
    return TokenService.get_patient_live_token_status(db=db, patient_id=patient_id)


@router.put(
    "/{token_id}/call",
    response_model=TokenResponse,
    summary="Call patient token into consultation room",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.DOCTOR,
                RoleEnum.NURSE,
                RoleEnum.RECEPTIONIST,
            )
        )
    ],
)
def call_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Page token to enter doctor consultation room."""
    return TokenService.call_token(db=db, token_id=token_id, called_by_id=current_user.id)


@router.put(
    "/{token_id}/complete",
    response_model=TokenResponse,
    summary="Complete patient consultation for token",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.DOCTOR,
                RoleEnum.NURSE,
                RoleEnum.RECEPTIONIST,
            )
        )
    ],
)
def complete_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark token consultation completed."""
    return TokenService.complete_token(db=db, token_id=token_id, completed_by_id=current_user.id)

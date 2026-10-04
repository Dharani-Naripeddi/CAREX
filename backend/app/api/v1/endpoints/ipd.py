from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.models.admission import AdmissionStatus
from app.schemas.ipd import (
    AdmissionCreate,
    AdmissionResponse,
    BedTransferCreate,
    BedTransferResponse,
    DischargeRequest,
)
from app.services.ipd_service import IpdService

router = APIRouter()


@router.get(
    "/admissions",
    response_model=List[AdmissionResponse],
    summary="List active and historical inpatient admissions",
)
def list_admissions(
    status: Optional[AdmissionStatus] = Query(None, description="Filter by admission status"),
    ward_id: Optional[int] = Query(None, description="Filter by ward ID"),
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve hospital inpatient admissions."""
    return IpdService.get_admissions(
        db=db,
        status=status,
        ward_id=ward_id,
        patient_id=patient_id,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/admissions",
    response_model=AdmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admit a patient to Inpatient Ward and allocate Bed",
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
def admit_patient(
    adm_in: AdmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create inpatient admission and allocate bed (sets bed status to OCCUPIED)."""
    return IpdService.create_admission(
        db=db,
        adm_in=adm_in,
        created_by_id=current_user.id,
    )


@router.post(
    "/admissions/{admission_id}/transfer",
    response_model=BedTransferResponse,
    summary="Transfer inpatient to a different Ward or Bed",
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
def transfer_inpatient_bed(
    admission_id: int,
    transfer_in: BedTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Transfer patient to target bed, freeing previous bed to CLEANING."""
    return IpdService.transfer_bed(
        db=db,
        admission_id=admission_id,
        transfer_in=transfer_in,
        transferred_by_id=current_user.id,
    )


@router.post(
    "/admissions/{admission_id}/discharge",
    response_model=AdmissionResponse,
    summary="Discharge inpatient and compile official discharge summary",
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
def discharge_inpatient(
    admission_id: int,
    discharge_in: DischargeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Complete discharge summary, record condition and medications, and free bed to CLEANING."""
    return IpdService.discharge_patient(
        db=db,
        admission_id=admission_id,
        discharge_in=discharge_in,
        discharged_by_id=current_user.id,
    )

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.models.emergency_case import TriageLevel, EmergencyCaseStatus
from app.schemas.emergency import EmergencyCaseCreate, EmergencyCaseUpdate, EmergencyCaseResponse
from app.services.emergency_service import EmergencyService

router = APIRouter()


@router.get(
    "/",
    response_model=List[EmergencyCaseResponse],
    summary="List active and triaged emergency cases",
)
def list_emergency_cases(
    status: Optional[EmergencyCaseStatus] = Query(None, description="Filter by case status"),
    triage_level: Optional[TriageLevel] = Query(None, description="Filter by triage level (RED, ORANGE, YELLOW, GREEN)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve prioritized emergency cases sorted by Triage Priority (RED -> ORANGE -> YELLOW -> GREEN)."""
    return EmergencyService.get_cases(
        db=db,
        status=status,
        triage_level=triage_level,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/",
    response_model=EmergencyCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new emergency case and compute rule-based triage decision support",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.RECEPTIONIST,
                RoleEnum.DOCTOR,
                RoleEnum.NURSE,
            )
        )
    ],
)
def create_emergency_case(
    case_in: EmergencyCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Register incoming trauma/medical emergency case.
    Executes rule-based Triage Decision Support algorithm and assigns triage level.
    """
    return EmergencyService.create_case(
        db=db,
        case_in=case_in,
        created_by_id=current_user.id,
    )


@router.get(
    "/{case_id}",
    response_model=EmergencyCaseResponse,
    summary="Get emergency case details by ID",
)
def get_emergency_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve full emergency case record and triage factors."""
    emr_case = EmergencyService.get_case_by_id(db, case_id)
    if not emr_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency case with ID {case_id} not found.",
        )
    return emr_case


@router.put(
    "/{case_id}",
    response_model=EmergencyCaseResponse,
    summary="Update emergency case vitals or clinical status",
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
def update_emergency_case(
    case_id: int,
    case_in: EmergencyCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update vitals or status and re-evaluates triage decision support if vitals are updated."""
    return EmergencyService.update_case(
        db=db,
        case_id=case_id,
        case_in=case_in,
        updated_by_id=current_user.id,
    )

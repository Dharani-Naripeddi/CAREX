from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.ai.brain.schemas import (
    HospitalBrainOverview,
    HospitalBrainEvent,
    DepartmentStatusSummary,
    HospitalCapacityMatrix,
    HospitalBrainActionItem,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
)
from app.ai.brain.service import HospitalBrainService

router = APIRouter()


@router.get(
    "/overview",
    response_model=HospitalBrainOverview,
    summary="Get centralized Hospital Brain operational intelligence overview & KPIs",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.DOCTOR,
                RoleEnum.NURSE,
                RoleEnum.RECEPTIONIST,
                RoleEnum.PHARMACIST,
                RoleEnum.LAB_TECHNICIAN,
            )
        )
    ],
)
def get_hospital_brain_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deliver real-time hospital operational intelligence combining Phase 5 AI predictions,

    multi-signal correlation, department matrix, and prioritized action playbooks.
    """
    return HospitalBrainService.get_overview(db)


@router.get(
    "/events",
    response_model=List[HospitalBrainEvent],
    summary="List prioritized hospital operational intelligence events feed",
)
def get_hospital_brain_events(
    status: Optional[str] = Query(None, description="ACTIVE, ACKNOWLEDGED, RESOLVED"),
    severity: Optional[str] = Query(None, description="CRITICAL, HIGH, WARNING, INFO"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return HospitalBrainService.get_events(db, status=status, severity=severity, limit=limit)


@router.get(
    "/events/active",
    response_model=List[HospitalBrainEvent],
    summary="List only active operational intelligence events",
)
def get_active_hospital_brain_events(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return HospitalBrainService.get_events(db, status="ACTIVE", limit=limit)


@router.get(
    "/events/{event_id}",
    response_model=HospitalBrainEvent,
    summary="Get granular 'Why?' explainability breakdown for a specific intelligence event",
)
def get_event_details(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    event = HospitalBrainService.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital Brain event with ID {event_id} not found.",
        )
    return event


@router.post(
    "/events/{event_id}/acknowledge",
    response_model=HospitalBrainEvent,
    summary="Acknowledge an operational intelligence event (Logs to Audit Trail)",
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
def acknowledge_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    event = HospitalBrainService.acknowledge_event(
        db,
        event_id=event_id,
        user_id=current_user.id,
        user_name=current_user.full_name or current_user.email,
    )
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital Brain event with ID {event_id} not found.",
        )
    return event


@router.post(
    "/events/{event_id}/resolve",
    response_model=HospitalBrainEvent,
    summary="Mark an operational intelligence event as resolved (Logs to Audit Trail)",
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
def resolve_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    event = HospitalBrainService.resolve_event(
        db,
        event_id=event_id,
        user_id=current_user.id,
        user_name=current_user.full_name or current_user.email,
    )
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital Brain event with ID {event_id} not found.",
        )
    return event


@router.get(
    "/departments",
    response_model=List[DepartmentStatusSummary],
    summary="Get operational load status and metrics across all hospital departments",
)
def get_departments_intelligence(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return HospitalBrainService.get_departments_intelligence(db)


@router.get(
    "/capacity",
    response_model=HospitalCapacityMatrix,
    summary="Get hospital capacity matrix (Inpatient, ICU, Wards, and Queue delays)",
)
def get_hospital_capacity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return HospitalBrainService.get_capacity_matrix(db)


@router.get(
    "/actions",
    response_model=List[HospitalBrainActionItem],
    summary="Get coordinated operational action center items and playbooks",
)
def get_hospital_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return HospitalBrainService.get_action_center(db)


@router.post(
    "/simulation",
    response_model=WhatIfSimulationResponse,
    summary="Run controlled What-If scenario simulation (Logs to Audit Trail)",
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
def run_what_if_simulation(
    request: WhatIfSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Execute scenario-based simulation projecting operational impacts on ER load,

    bed occupancy, ICU saturation, and OPD queue delays.
    """
    return HospitalBrainService.run_simulation(
        db,
        req=request,
        user_id=current_user.id,
        user_name=current_user.full_name or current_user.email,
    )

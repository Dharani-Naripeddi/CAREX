from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.models.bed import BedStatus
from app.schemas.bed import (
    BedResponse,
    WardResponse,
    BedDashboardStats,
    BedStatusUpdate,
)
from app.services.bed_service import BedService

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=BedDashboardStats,
    summary="Get Bed Management dashboard telemetry, occupancy rates, and ward summaries",
)
def get_bed_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve hospital-wide bed occupancy counters, ICU rate, and ward breakdowns."""
    return BedService.get_dashboard_stats(db)


@router.get(
    "/wards",
    response_model=List[WardResponse],
    summary="List all hospital wards with active bed occupancy counts",
)
def list_wards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve list of clinical wards with calculated occupancy."""
    return BedService.get_wards(db)


@router.get(
    "/",
    response_model=List[BedResponse],
    summary="List and filter hospital beds by ward and operational status",
)
def list_beds(
    ward_id: Optional[int] = Query(None, description="Filter by ward ID"),
    status: Optional[BedStatus] = Query(None, description="Filter by status (AVAILABLE, OCCUPIED, RESERVED, CLEANING, MAINTENANCE)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve list of beds, room locations, and occupant details."""
    return BedService.get_beds(
        db=db,
        ward_id=ward_id,
        status=status,
    )


@router.put(
    "/{bed_id}/status",
    response_model=BedResponse,
    summary="Update bed status (e.g. mark Cleaned -> Available, or Maintenance)",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.NURSE,
                RoleEnum.DOCTOR,
                RoleEnum.RECEPTIONIST,
            )
        )
    ],
)
def update_bed_status(
    bed_id: int,
    status_in: BedStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update bed status."""
    return BedService.update_bed_status(
        db=db,
        bed_id=bed_id,
        status_in=status_in,
        updated_by_id=current_user.id,
    )

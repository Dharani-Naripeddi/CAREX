from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.demo.schemas import (
    DemoScenario,
    DemoScenarioLaunchRequest,
    DemoScenarioResult,
    DemoResetResponse,
    DemoPipelineProgress,
)
from app.demo.service import DemoService
from app.ai.brain.service import HospitalBrainService
from app.ai.brain.schemas import HospitalBrainOverview

router = APIRouter()


@router.get(
    "/scenarios",
    response_model=List[DemoScenario],
    summary="List all SIH Demo Scenarios",
)
def list_demo_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve the full catalog of 7 SIH demo scenarios."""
    return DemoService.list_scenarios()


@router.post(
    "/launch",
    response_model=DemoScenarioResult,
    summary="Launch a deterministic SIH Demo Scenario",
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
def launch_demo_scenario(
    req: DemoScenarioLaunchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Execute a deterministic demo scenario and update live Hospital Brain state."""
    return DemoService.launch_scenario(
        db=db,
        scenario_code=req.scenario_code,
        user_id=current_user.id,
        user_name=current_user.full_name,
    )


@router.post(
    "/reset",
    response_model=DemoResetResponse,
    summary="Reset Demo Mode to clean baseline state",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
            )
        )
    ],
)
def reset_demo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Restore clean baseline operational state and clear demo injected alerts."""
    return DemoService.reset_demo(
        db=db,
        user_id=current_user.id,
        user_name=current_user.full_name,
    )


@router.get(
    "/pipeline-progress",
    response_model=DemoPipelineProgress,
    summary="Get real-time CAREX Intelligence Pipeline progression",
)
def get_pipeline_progress(
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve real-time step status across the 6-stage CAREX Intelligence Pipeline."""
    return DemoService.get_pipeline_progress()


@router.get(
    "/overview",
    response_model=HospitalBrainOverview,
    summary="Get Demo Command Center live overview",
)
def get_demo_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve live overview formatted for the SIH Demo Command Center."""
    return HospitalBrainService.get_overview(db)

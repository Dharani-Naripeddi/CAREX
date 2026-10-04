from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.role import RoleEnum
from app.models.nurse_profile import ShiftEnum
from app.schemas.nurse import NurseWithUser, NurseProfileUpdate, NurseProfileResponse, NurseCreate
from app.services.nurse_service import NurseService

router = APIRouter()


@router.get(
    "/",
    response_model=List[NurseWithUser],
    summary="List all nurses and ward rosters",
)
def list_nurses(
    department_id: Optional[int] = None,
    shift: Optional[ShiftEnum] = None,
    is_on_duty: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Retrieve all nursing staff, shift schedules, and ward assignments."""
    return NurseService.get_nurses(
        db=db,
        department_id=department_id,
        shift=shift,
        is_on_duty=is_on_duty,
    )


@router.post(
    "/",
    response_model=NurseWithUser,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new nursing staff member",
)
def create_nurse(
    nurse_in: NurseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Dynamically register a new nursing staff member with department, shift, and ward assignment."""
    return NurseService.register_nurse(
        db=db,
        nurse_in=nurse_in,
    )


@router.put(

    "/{user_id}",
    response_model=NurseProfileResponse,
    summary="Update nurse shift schedule and on-duty status",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.NURSE,
                RoleEnum.RECEPTIONIST,
                RoleEnum.DOCTOR,
            )
        )
    ],
)
def update_nurse(
    user_id: int,
    profile_in: NurseProfileUpdate,
    db: Session = Depends(get_db),
):
    """Update nurse shift or ward assignment."""
    return NurseService.create_or_update_nurse_profile(
        db=db,
        user_id=user_id,
        profile_in=profile_in,
    )

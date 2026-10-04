from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.role import RoleEnum
from app.schemas.doctor import DoctorWithUser, DoctorProfileUpdate, DoctorProfileResponse, DoctorCreate
from app.services.doctor_service import DoctorService

router = APIRouter()


@router.get(
    "/",
    response_model=List[DoctorWithUser],
    summary="List all doctors with specialization and department",
)
def list_doctors(
    department_id: Optional[int] = None,
    is_available: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Retrieve all doctor profiles and availability schedules."""
    return DoctorService.get_doctors(
        db=db,
        department_id=department_id,
        is_available=is_available,
    )


@router.post(
    "/",
    response_model=DoctorWithUser,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new doctor",
)
def create_doctor(
    doctor_in: DoctorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Dynamically register a new attending physician with department and consultation schedule."""
    return DoctorService.register_doctor(
        db=db,
        doctor_in=doctor_in,
    )


@router.get(
    "/{user_id}",
    response_model=DoctorWithUser,
    summary="Get doctor profile by user ID",
)
def get_doctor(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Fetch specific doctor clinical details and schedule."""
    doctor = DoctorService.get_doctor_by_user_id(db, user_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor profile for user ID {user_id} not found.",
        )
    return doctor


@router.put(
    "/{user_id}",
    response_model=DoctorProfileResponse,
    summary="Create or update doctor profile (Availability, Fee, Schedule)",
)
def update_doctor(
    user_id: int,
    profile_in: DoctorProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Update doctor consultation hours, fees, availability status, and specialization."""
    return DoctorService.create_or_update_doctor_profile(
        db=db,
        user_id=user_id,
        profile_in=profile_in,
    )


from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserWithRelations
from app.schemas.common import APIResponse
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "/",
    response_model=List[UserWithRelations],
    summary="List all users (Admin only)",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN))],
)
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retrieve all users in the hospital system."""
    return UserService.get_users(db, skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=UserWithRelations,
    summary="Get user details by ID",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a single user by ID. Users can view their own profile, Admins can view any."""
    is_admin = current_user.role and current_user.role.name in [
        RoleEnum.SUPER_ADMIN,
        RoleEnum.HOSPITAL_ADMIN,
    ]
    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you may only view your own user profile",
        )

    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return user


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (Admin only)",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN))],
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new hospital staff or patient user account."""
    return UserService.create_user(db, user_in, created_by_id=current_user.id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update an existing user",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN))],
)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update user account attributes."""
    return UserService.update_user(db, user_id, user_in, updated_by_id=current_user.id)

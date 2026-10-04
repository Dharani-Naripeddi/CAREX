from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.models.role import Role
from app.schemas.role import RoleResponse

router = APIRouter()


@router.get("/", response_model=List[RoleResponse], summary="List all hospital roles")
def get_roles(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Return all predefined system roles with their permission maps."""
    return db.query(Role).all()


@router.get("/{role_id}", response_model=RoleResponse, summary="Get role by ID")
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Retrieve specific role details."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found",
        )
    return role

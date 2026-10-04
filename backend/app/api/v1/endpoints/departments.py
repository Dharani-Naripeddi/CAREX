from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.department import Department
from app.models.role import RoleEnum
from app.schemas.department import DepartmentCreate, DepartmentResponse

router = APIRouter()


@router.get("/", response_model=List[DepartmentResponse], summary="List all hospital departments")
def get_departments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Retrieve all clinical and operational hospital departments."""
    return db.query(Department).filter(Department.is_active == True).all()


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department (Admin only)",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN))],
)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
):
    """Create a new hospital department."""
    existing = (
        db.query(Department)
        .filter((Department.name == dept_in.name) | (Department.code == dept_in.code))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with name '{dept_in.name}' or code '{dept_in.code}' already exists.",
        )

    dept = Department(
        name=dept_in.name,
        code=dept_in.code.upper(),
        description=dept_in.description,
        is_active=dept_in.is_active,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

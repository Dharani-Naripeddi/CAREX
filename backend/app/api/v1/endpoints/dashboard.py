from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.schemas.dashboard import AdminDashboardStats, RoleDashboardData
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get(
    "/admin",
    response_model=AdminDashboardStats,
    summary="Get CAREX Hospital Command Center KPIs and live stats",
    dependencies=[Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN))],
)
def get_admin_dashboard(
    db: Session = Depends(get_db),
):
    """
    Fetch live metrics for the CAREX Hospital Command Center:
    - 8 core KPIs (Total Patients, Today's OPD, Admissions, Beds, ICU, Emergency, Labs, Pharmacy)
    - Trend analysis charts
    - Department bed occupancy
    - Emergency Triage Queue
    - Recent Activity Feed
    """
    return DashboardService.get_admin_command_center_data(db)


@router.get(
    "/role/{role_name}",
    response_model=RoleDashboardData,
    summary="Get role-specific dashboard metrics and operational queue",
)
def get_role_dashboard(
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Fetch tailored operational dashboard data for the requested role
    (Doctor, Nurse, Receptionist, Pharmacist, Lab Technician, Patient)
    connected dynamically to the database.
    """
    return DashboardService.get_role_dashboard_data(db, role_name, current_user.id)

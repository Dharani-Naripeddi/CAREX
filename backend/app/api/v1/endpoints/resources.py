from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.resource import ResourceCoordinationStatus
from app.services.resource_service import ResourceService

router = APIRouter()


@router.get(
    "/coordination",
    response_model=ResourceCoordinationStatus,
    summary="Get hospital resource availability, capacity load, and operational recommendations",
)
def get_resource_coordination(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Fetch live availability across Emergency Doctors, Nurses, ICU Beds,
    General Beds, Oxygen Support, and Diagnostic Laboratory with decision support recommendations.
    """
    return ResourceService.get_resource_coordination_status(db)

import enum
from typing import List, Optional
from pydantic import BaseModel


class ResourceAvailability(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    UNAVAILABLE = "UNAVAILABLE"


class ResourceItem(BaseModel):
    name: str
    resource_type: str  # "DOCTORS", "NURSES", "ICU_BEDS", "GENERAL_BEDS", "OXYGEN_SUPPORT", "LABORATORY"
    status: ResourceAvailability
    current_capacity: int
    total_capacity: int
    utilization_percentage: float
    details: str


class ResourceCoordinationStatus(BaseModel):
    last_updated: str
    overall_status: ResourceAvailability
    resources: List[ResourceItem]
    operational_recommendations: List[str]
    disclaimer: str = (
        "AI decision support only. Final clinical decision must be made by qualified healthcare professionals."
    )

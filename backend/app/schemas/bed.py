import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.bed import BedStatus
from app.models.room import RoomType


class BedBase(BaseModel):
    bed_number: str
    ward_id: int
    room_id: Optional[int] = None
    status: BedStatus = BedStatus.AVAILABLE
    has_oxygen_support: bool = True
    has_ventilator: bool = False


class BedCreate(BedBase):
    pass


class BedStatusUpdate(BaseModel):
    status: BedStatus


class BedResponse(BedBase):
    id: int
    ward_name: Optional[str] = None
    room_number: Optional[str] = None
    current_admission_id: Optional[int] = None
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class RoomResponse(BaseModel):
    id: int
    room_number: str
    ward_id: int
    room_type: RoomType
    has_oxygen_support: bool
    daily_rate: float
    beds: List[BedResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WardResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    floor: str
    wing: str
    total_beds: int
    occupied_beds: int = 0
    available_beds: int = 0
    occupancy_rate: float = 0.0
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class BedDashboardStats(BaseModel):
    total_beds: int
    occupied_beds: int
    available_beds: int
    reserved_beds: int
    maintenance_beds: int
    cleaning_beds: int
    occupancy_rate: float
    icu_occupancy_rate: float
    wards: List[WardResponse]

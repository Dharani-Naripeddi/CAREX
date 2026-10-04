import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.department import DepartmentResponse


class DoctorProfileBase(BaseModel):
    specialization: str
    qualification: str
    experience_years: int = 5
    consultation_fee: float = 75.0
    room_number: Optional[str] = None
    availability_days: List[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    available_from: str = "09:00"
    available_to: str = "17:00"
    is_available: bool = True
    department_id: Optional[int] = None


class DoctorProfileCreate(DoctorProfileBase):
    user_id: int


class DoctorCreate(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = "+1-555-0199"
    department_id: int
    specialization: str
    qualification: str = "MBBS, MD"
    experience_years: int = 8
    consultation_fee: float = 100.0
    room_number: Optional[str] = "Consultation Suite 101"
    availability_days: List[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    available_from: str = "09:00"
    available_to: str = "17:00"
    avatar_url: Optional[str] = None
    password: Optional[str] = "Carex#2026"


class DoctorProfileUpdate(BaseModel):
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    room_number: Optional[str] = None
    availability_days: Optional[List[str]] = None
    available_from: Optional[str] = None
    available_to: Optional[str] = None
    is_available: Optional[bool] = None
    department_id: Optional[int] = None


class DoctorProfileResponse(DoctorProfileBase):
    id: int
    user_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorWithUser(DoctorProfileResponse):
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    department_name: Optional[str] = None
    department: Optional[DepartmentResponse] = None

    model_config = ConfigDict(from_attributes=True)

import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.nurse_profile import ShiftEnum
from app.schemas.department import DepartmentResponse


class NurseProfileBase(BaseModel):
    qualification: str
    shift: ShiftEnum = ShiftEnum.MORNING
    ward_assigned: Optional[str] = None
    is_on_duty: bool = True
    department_id: Optional[int] = None


class NurseProfileCreate(NurseProfileBase):
    user_id: int


class NurseCreate(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = "+1-555-0199"
    department_id: int
    qualification: str = "BSN, RN"
    shift: ShiftEnum = ShiftEnum.MORNING
    ward_assigned: Optional[str] = "General Inpatient Ward"
    is_on_duty: bool = True
    avatar_url: Optional[str] = None
    password: Optional[str] = "Carex#2026"



class NurseProfileUpdate(BaseModel):
    qualification: Optional[str] = None
    shift: Optional[ShiftEnum] = None
    ward_assigned: Optional[str] = None
    is_on_duty: Optional[bool] = None
    department_id: Optional[int] = None


class NurseProfileResponse(NurseProfileBase):
    id: int
    user_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class NurseWithUser(NurseProfileResponse):
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    department_name: Optional[str] = None
    department: Optional[DepartmentResponse] = None

    model_config = ConfigDict(from_attributes=True)

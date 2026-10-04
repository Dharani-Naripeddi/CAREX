import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.appointment import AppointmentStatus, AppointmentType
from app.schemas.patient import PatientResponse
from app.schemas.department import DepartmentResponse


class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    department_id: int
    appointment_date: datetime.date
    appointment_time: str  # e.g. "10:30"
    type: AppointmentType = AppointmentType.OPD
    chief_complaint: Optional[str] = None
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime.date] = None
    appointment_time: Optional[str] = None
    type: Optional[AppointmentType] = None
    chief_complaint: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    cancellation_reason: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    cancellation_reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentReschedule(BaseModel):
    appointment_date: datetime.date
    appointment_time: str
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: int
    appointment_number: str
    status: AppointmentStatus
    cancellation_reason: Optional[str] = None
    created_by_id: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentWithDetails(AppointmentResponse):
    patient_name: str
    patient_mrn: str
    patient_phone: str
    doctor_name: str
    doctor_specialization: Optional[str] = None
    department_name: str
    patient: Optional[PatientResponse] = None
    department: Optional[DepartmentResponse] = None

    model_config = ConfigDict(from_attributes=True)

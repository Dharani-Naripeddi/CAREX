import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.opd_token import TokenStatus, TokenPriority
from app.schemas.patient import PatientResponse


class TokenGenerateRequest(BaseModel):
    patient_id: int
    department_id: int
    doctor_id: Optional[int] = None
    appointment_id: Optional[int] = None
    priority: TokenPriority = TokenPriority.NORMAL


class TokenResponse(BaseModel):
    id: int
    token_number: int
    token_code: str
    date: datetime.date
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: int
    appointment_id: Optional[int] = None
    priority: TokenPriority
    status: TokenStatus
    estimated_wait_minutes: int
    called_at: Optional[datetime.datetime] = None
    serviced_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class TokenWithDetails(TokenResponse):
    patient_name: str
    patient_mrn: str
    doctor_name: Optional[str] = None
    department_name: str
    patient: Optional[PatientResponse] = None

    model_config = ConfigDict(from_attributes=True)


class TokenQueueStatus(BaseModel):
    department_name: str
    doctor_name: Optional[str] = None
    current_token_code: Optional[str] = None
    current_token_number: Optional[int] = None
    total_in_queue: int
    waiting_tokens: List[TokenWithDetails]


class PatientLiveTokenStatus(BaseModel):
    has_active_token: bool
    token: Optional[TokenWithDetails] = None
    current_serving_token_code: Optional[str] = None
    patients_ahead: int = 0
    estimated_wait_minutes: int = 0

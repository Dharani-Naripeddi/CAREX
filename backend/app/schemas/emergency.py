import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.emergency_case import TriageLevel, ConsciousnessLevel, EmergencyCaseStatus


class TriageEvaluation(BaseModel):
    triage_level: TriageLevel
    contributing_factors: List[str]
    recommended_action: str
    disclaimer: str = (
        "AI decision support only. Final clinical decision must be made by qualified healthcare professionals."
    )


class EmergencyCaseBase(BaseModel):
    patient_id: Optional[int] = None
    patient_name: str
    age: int
    gender: str
    symptoms: str
    injury_type: Optional[str] = None
    heart_rate: int
    bp_systolic: int
    bp_diastolic: int
    spo2: float
    temperature: float
    respiratory_rate: int
    consciousness: ConsciousnessLevel = ConsciousnessLevel.ALERT
    doctor_id: Optional[int] = None
    nurse_id: Optional[int] = None


class EmergencyCaseCreate(EmergencyCaseBase):
    arrival_time: Optional[datetime.datetime] = None


class EmergencyCaseUpdate(BaseModel):
    symptoms: Optional[str] = None
    injury_type: Optional[str] = None
    heart_rate: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    consciousness: Optional[ConsciousnessLevel] = None
    status: Optional[EmergencyCaseStatus] = None
    doctor_id: Optional[int] = None
    nurse_id: Optional[int] = None
    triage_notes: Optional[str] = None


class EmergencyCaseResponse(EmergencyCaseBase):
    id: int
    case_number: str
    arrival_time: datetime.datetime
    triage_level: TriageLevel
    contributing_factors: List[str]
    recommended_action: str
    triage_notes: Optional[str] = None
    status: EmergencyCaseStatus
    doctor_name: Optional[str] = None
    nurse_name: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    disclaimer: str = (
        "AI decision support only. Final clinical decision must be made by qualified healthcare professionals."
    )

    model_config = ConfigDict(from_attributes=True)

import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.admission import AdmissionStatus, DischargeCondition
from app.schemas.patient import PatientResponse
from app.schemas.bed import WardResponse, BedResponse


class AdmissionCreate(BaseModel):
    patient_id: int
    admitting_doctor_id: int
    ward_id: int
    bed_id: int
    admission_reason: str
    expected_stay_days: int = 3
    emergency_case_id: Optional[int] = None


class BedTransferCreate(BaseModel):
    to_bed_id: int
    transfer_reason: str


class DischargeRequest(BaseModel):
    discharge_diagnosis: str
    discharge_summary: str
    discharge_condition: DischargeCondition = DischargeCondition.STABLE
    discharge_medications: List[Dict[str, Any]] = []
    follow_up_instructions: Optional[str] = None


class BedTransferResponse(BaseModel):
    id: int
    admission_id: int
    from_bed_id: int
    to_bed_id: int
    from_bed_number: Optional[str] = None
    to_bed_number: Optional[str] = None
    transfer_reason: str
    transferred_at: datetime.datetime
    transferred_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdmissionResponse(BaseModel):
    id: int
    admission_number: str
    patient_id: int
    admitting_doctor_id: int
    ward_id: int
    bed_id: int
    admission_date: datetime.datetime
    discharge_date: Optional[datetime.datetime] = None
    admission_reason: str
    expected_stay_days: int
    status: AdmissionStatus
    emergency_case_id: Optional[int] = None

    # Discharge details
    discharge_diagnosis: Optional[str] = None
    discharge_summary: Optional[str] = None
    discharge_condition: Optional[DischargeCondition] = None
    discharge_medications: List[Dict[str, Any]] = []
    follow_up_instructions: Optional[str] = None
    discharged_by_id: Optional[int] = None

    patient_name: str
    patient_mrn: str
    doctor_name: str
    ward_name: str
    bed_number: str
    discharged_by_name: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

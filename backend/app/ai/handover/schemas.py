from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType, AIRiskLevel


class PatientHandoverSummaryItem(BaseModel):
    admission_id: int
    admission_number: str
    patient_id: int
    patient_name: str
    patient_mrn: str
    bed_number: str
    ward_name: str
    priority: AIRiskLevel
    
    current_status: str
    latest_vitals: Dict[str, str] = Field(default_factory=dict)
    pending_investigations: List[str] = Field(default_factory=list)
    active_medications: List[str] = Field(default_factory=list)
    key_tasks: List[str] = Field(default_factory=list)
    important_observations: str


class ShiftHandoverRequest(BaseModel):
    ward_id: Optional[int] = None
    shift_name: str = "MORNING"  # MORNING, EVENING, NIGHT
    to_nurse_id: Optional[int] = None


class ShiftHandoverResponse(BaseModel):
    handover_id: Optional[int] = None
    ward_id: Optional[int] = None
    ward_name: Optional[str] = None
    shift_name: str
    from_nurse_id: int
    from_nurse_name: str
    to_nurse_id: Optional[int] = None
    
    total_patients: int
    high_priority_patients: int
    patient_summaries: List[PatientHandoverSummaryItem] = Field(default_factory=list)
    important_observations: str
    next_shift_checklist: List[str] = Field(default_factory=list)
    ai_notes: str
    
    status: str  # DRAFT, APPROVED
    is_approved: bool = False
    approved_by_name: Optional[str] = None
    created_at: datetime
    
    model_provider_type: ModelProviderType
    model_version: str
    disclaimer: str = "AI-generated nursing handover. Review and explicit nurse verification are required before shift sign-off."


class HandoverApprovalRequest(BaseModel):
    important_observations: Optional[str] = None
    next_shift_checklist: Optional[List[str]] = None
    to_nurse_id: Optional[int] = None

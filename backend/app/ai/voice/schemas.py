from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType


class StructuredClinicalNoteDraft(BaseModel):
    chief_complaint: str
    duration: Optional[str] = None
    vital_signs_mentioned: Dict[str, str] = Field(default_factory=dict)
    associated_symptoms: List[str] = Field(default_factory=list)
    examination_notes: str
    suggested_assessment_plan: str


class VoiceTranscriptionRequest(BaseModel):
    audio_text: Optional[str] = None
    patient_id: Optional[int] = None
    use_demo_sample: bool = False


class VoiceTranscriptionResponse(BaseModel):
    raw_transcript: str
    structured_note: StructuredClinicalNoteDraft
    formatted_clinical_summary: str
    model_provider_type: ModelProviderType
    model_version: str
    doctor_verification_required: bool = True
    disclaimer: str = "AI-assisted voice note structuring. Doctor review, manual editing, and explicit confirmation are required before saving."

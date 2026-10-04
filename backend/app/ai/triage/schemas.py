from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType, AIRiskLevel
from app.models.emergency_case import TriageLevel, ConsciousnessLevel
from app.ai.base import StandardAIExplanation


class TriageAIRequest(BaseModel):
    patient_name: Optional[str] = None
    age: int
    gender: str
    symptoms: str
    injury_type: Optional[str] = None
    
    # Vital Signs
    heart_rate: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    consciousness: ConsciousnessLevel = ConsciousnessLevel.ALERT


class TriageAIResponse(BaseModel):
    triage_level: TriageLevel
    color_hex: str
    risk_level: AIRiskLevel
    contributing_factors: List[str]
    vital_flags: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_action: str
    target_assessment_time_minutes: int
    
    model_provider_type: ModelProviderType
    model_version: str
    explanation: StandardAIExplanation
    disclaimer: str = "AI decision support only. Final clinical assessment and priority assignment remain the strict responsibility of qualified healthcare professionals."

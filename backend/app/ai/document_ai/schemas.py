from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType, AIRiskLevel


class ExtractedParameter(BaseModel):
    parameter_name: str
    result_value: str
    numeric_value: Optional[float] = None
    unit: str
    reference_range: str
    flag: str  # NORMAL, LOW, HIGH, CRITICAL
    is_abnormal: bool = False


class DocumentAnalysisRequest(BaseModel):
    file_name: str
    file_type: str = "PDF"  # PDF, JPG, PNG
    patient_id: Optional[int] = None
    document_type: str = "LABORATORY_REPORT"
    raw_text: Optional[str] = None


class DocumentAnalysisResponse(BaseModel):
    document_id: Optional[int] = None
    file_name: str
    file_type: str
    document_type: str
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    
    extracted_parameters: List[ExtractedParameter] = Field(default_factory=list)
    abnormal_parameters_count: int = 0
    ai_summary: str
    key_findings: List[str] = Field(default_factory=list)
    
    risk_level: AIRiskLevel
    confidence: Optional[float] = 0.88
    model_provider_type: ModelProviderType
    model_version: str
    is_verified: bool = False
    disclaimer: str = "AI-generated diagnostic document summary. Always verify against original laboratory source document. Does not constitute autonomous medical diagnosis."

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType, AIRiskLevel
from app.ai.base import StandardAIExplanation


class BedPredictionRequest(BaseModel):
    ward_id: Optional[int] = None


class ForecastHorizonPoint(BaseModel):
    horizon_hours: int  # 6, 12, 24
    projected_occupancy_percent: float
    projected_admissions: int
    projected_discharges: int
    net_bed_delta: int
    risk_level: AIRiskLevel


class WardForecastSummary(BaseModel):
    ward_id: int
    ward_name: str
    ward_type: str
    total_beds: int
    occupied_beds: int
    available_beds: int
    current_occupancy_percent: float
    projected_24h_occupancy_percent: float
    risk_level: AIRiskLevel


class BedPredictionResponse(BaseModel):
    ward_id: Optional[int] = None
    ward_name: Optional[str] = None
    
    total_beds: int
    occupied_beds: int
    available_beds: int
    current_occupancy_percent: float
    
    horizons: List[ForecastHorizonPoint] = Field(default_factory=list)
    ward_breakdown: List[WardForecastSummary] = Field(default_factory=list)
    
    overall_risk_level: AIRiskLevel
    confidence: Optional[float] = None
    model_provider_type: ModelProviderType
    model_version: str
    
    explanation: StandardAIExplanation
    recommended_action: str
    alert_triggered: bool = False

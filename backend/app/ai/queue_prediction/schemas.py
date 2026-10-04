from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType, AIRiskLevel
from app.ai.base import StandardAIExplanation


class OpdQueuePredictionRequest(BaseModel):
    department_id: Optional[int] = None
    doctor_id: Optional[int] = None


class QueueTrendPoint(BaseModel):
    time_slot: str
    tokens_served: int
    avg_wait_minutes: float
    projected_wait_minutes: float


class OpdQueuePredictionResponse(BaseModel):
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    
    current_waiting_count: int
    current_serving_token: Optional[str] = None
    estimated_wait_minutes: float
    historical_avg_wait_minutes: float
    predicted_delay_minutes: float
    
    risk_level: AIRiskLevel
    confidence: Optional[float] = None
    model_provider_type: ModelProviderType
    model_version: str
    
    explanation: StandardAIExplanation
    recommended_action: str
    doctor_utilization_percent: float
    hourly_trend: List[QueueTrendPoint] = Field(default_factory=list)
    alert_triggered: bool = False

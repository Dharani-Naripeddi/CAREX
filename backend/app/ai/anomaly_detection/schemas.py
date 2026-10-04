from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType, AIRiskLevel, AIAlertSeverity


class OperationalAnomalyItem(BaseModel):
    anomaly_key: str
    title: str
    domain: str  # OPD, EMERGENCY, BEDS, PHARMACY, LABORATORY
    severity: AIAlertSeverity
    current_value: float
    expected_value: float
    unit: str
    percentage_deviation: float
    is_anomaly: bool
    
    explanation_reason: str
    recommended_action: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class AnomalyDetectionRequest(BaseModel):
    domain: Optional[str] = None  # ALL, OPD, EMERGENCY, BEDS, PHARMACY, LAB


class AnomalyDetectionResponse(BaseModel):
    total_metrics_evaluated: int
    anomalies_detected_count: int
    critical_anomalies_count: int
    high_anomalies_count: int
    
    anomalies: List[OperationalAnomalyItem] = Field(default_factory=list)
    overall_system_status: str  # NORMAL, ELEVATED_LOAD, CRITICAL_SURGE
    
    model_provider_type: ModelProviderType
    model_version: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

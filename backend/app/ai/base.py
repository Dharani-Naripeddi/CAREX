from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType, AIRiskLevel, AIAlertSeverity, AIPredictionType, AIAlertType


class StandardAIExplanation(BaseModel):
    """Standardized 'Why?' breakdown and operational recommendation."""
    summary: str
    reasons: List[str]
    contributing_factors: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_action: str
    safety_disclaimer: str = "AI decision support only. All recommendations must be reviewed and verified by qualified hospital personnel."


class AIIntelligenceEvent(BaseModel):
    """Standardized event interface connecting AI modules to the Hospital Brain (Phase 6 ready)."""
    source_module: str  # e.g., OPD_QUEUE, BED_CAPACITY, PHARMACY, EMERGENCY_TRIAGE, ANOMALY_DETECTOR
    event_type: AIAlertType
    severity: AIAlertSeverity
    current_value: Any
    prediction_value: Any
    risk_level: AIRiskLevel
    confidence: Optional[float] = None
    explanation: StandardAIExplanation
    recommended_action: str
    related_entity: str
    related_entity_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BaseAIProvider:
    """Abstract provider interface supporting ML models, statistical models, and deterministic fallbacks."""
    def __init__(self, provider_type: ModelProviderType = ModelProviderType.STATISTICAL_MODEL, model_version: str = "v1.0.0"):
        self.provider_type = provider_type
        self.model_version = model_version

    def get_provider_badge_info(self) -> Dict[str, str]:
        labels = {
            ModelProviderType.TRAINED_ML: "Trained Machine Learning Model (RandomForest / GBR)",
            ModelProviderType.STATISTICAL_MODEL: "Deterministic Statistical Moving-Average Engine",
            ModelProviderType.RULE_BASED: "Clinical Rule-Based Expert System",
            ModelProviderType.FALLBACK_SIMULATION: "Operational Estimate — Insufficient Historical Data",
        }
        return {
            "type": self.provider_type.value,
            "label": labels.get(self.provider_type, "Operational Forecast"),
            "version": self.model_version,
        }


class AIConfidenceHelper:
    """Calculates realistic confidence based on historical sample size and variance (Never fabricate fake confidence)."""
    @staticmethod
    def calculate_sample_confidence(sample_count: int, min_samples_for_high: int = 50) -> Optional[float]:
        if sample_count == 0:
            return None
        if sample_count < 5:
            return round(min(0.40, sample_count * 0.08), 2)
        if sample_count < min_samples_for_high:
            return round(0.40 + (sample_count / min_samples_for_high) * 0.45, 2)
        return 0.90

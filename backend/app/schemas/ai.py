from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.models.ai import (
    ModelProviderType,
    AIRiskLevel,
    AIAlertSeverity,
    AIAlertStatus,
    AIPredictionType,
    AIAlertType,
)
from app.ai.base import StandardAIExplanation

# Re-export sub-schemas
from app.ai.queue_prediction.schemas import (
    OpdQueuePredictionRequest,
    OpdQueuePredictionResponse,
    QueueTrendPoint,
)
from app.ai.bed_prediction.schemas import (
    BedPredictionRequest,
    BedPredictionResponse,
    ForecastHorizonPoint,
    WardForecastSummary,
)
from app.ai.pharmacy_prediction.schemas import (
    PharmacyPredictionRequest,
    PharmacyPredictionResponse,
    MedicineDepletionForecast,
    ConsumptionTrendPoint,
)
from app.ai.triage.schemas import (
    TriageAIRequest,
    TriageAIResponse,
)
from app.ai.document_ai.schemas import (
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    ExtractedParameter,
)
from app.ai.voice.schemas import (
    VoiceTranscriptionRequest,
    VoiceTranscriptionResponse,
    StructuredClinicalNoteDraft,
)
from app.ai.handover.schemas import (
    ShiftHandoverRequest,
    ShiftHandoverResponse,
    PatientHandoverSummaryItem,
    HandoverApprovalRequest,
)
from app.ai.anomaly_detection.schemas import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    OperationalAnomalyItem,
)


class AIAlertOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    alert_type: AIAlertType
    severity: AIAlertSeverity
    title: str
    description: str
    reason: Any
    recommended_action: str
    related_entity: str
    related_entity_id: Optional[str] = None
    status: AIAlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime] = None


class AIPredictionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    prediction_type: AIPredictionType
    entity_type: str
    entity_id: Optional[str] = None
    prediction_value: Any
    risk_level: AIRiskLevel
    confidence: Optional[float] = None
    model_name: str
    model_version: str
    model_provider_type: ModelProviderType
    explanation: Any
    recommended_action: str
    generated_at: datetime


class AIFeedbackCreate(BaseModel):
    rating: str  # USEFUL, NOT_USEFUL, INCORRECT, NEEDS_REVIEW
    notes: Optional[str] = None
    prediction_id: Optional[int] = None
    alert_id: Optional[int] = None


class AIFeedbackOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    rating: str
    notes: Optional[str] = None
    prediction_id: Optional[int] = None
    alert_id: Optional[int] = None
    created_at: datetime


class SimulationTriggerRequest(BaseModel):
    scenario_type: str  # OPD_DELAY, ICU_CAPACITY, PHARMACY_DEPLETION, EMERGENCY_SURGE

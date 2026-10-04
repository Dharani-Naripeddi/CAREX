from datetime import datetime
from typing import List, Dict, Any, Optional
import enum
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType, AIRiskLevel, AIAlertSeverity, AIAlertStatus


class HospitalSystemStatus(str, enum.Enum):
    STABLE = "STABLE"
    WATCH = "WATCH"
    HIGH_LOAD = "HIGH_LOAD"
    CRITICAL = "CRITICAL"


class HospitalBrainEventType(str, enum.Enum):
    OPD_DELAY = "OPD_DELAY"
    BED_CAPACITY_RISK = "BED_CAPACITY_RISK"
    PHARMACY_DEPLETION = "PHARMACY_DEPLETION"
    EMERGENCY_SURGE = "EMERGENCY_SURGE"
    LAB_BACKLOG = "LAB_BACKLOG"
    STAFFING_RISK = "STAFFING_RISK"
    OPERATIONAL_ANOMALY = "OPERATIONAL_ANOMALY"
    HOSPITAL_CAPACITY_RISK = "HOSPITAL_CAPACITY_RISK"


class HospitalBrainSourceModule(str, enum.Enum):
    OPD = "OPD"
    EMERGENCY = "EMERGENCY"
    BED = "BED"
    PHARMACY = "PHARMACY"
    LAB = "LAB"
    STAFF = "STAFF"
    PATIENT_FLOW = "PATIENT_FLOW"
    AI_ENGINE = "AI_ENGINE"
    SYSTEM = "SYSTEM"


class PriorityFactor(BaseModel):
    name: str
    weight_pct: float
    contribution: float
    reason: str


class OperationalPriorityBreakdown(BaseModel):
    score: int = Field(ge=0, le=100, description="0 to 100 Operational Priority Score")
    rating: str = Field(description="LOW, MODERATE, HIGH, CRITICAL")
    factors: List[PriorityFactor] = Field(default_factory=list)
    summary_explanation: str


class HospitalBrainExplanation(BaseModel):
    what_is_happening: str
    what_is_expected: str
    why_flagged: List[str]
    affected_departments: List[str]
    affected_resources: List[str]
    recommended_operational_review: str
    data_sources: List[str]
    model_provider_type: ModelProviderType
    model_version: str
    confidence: Optional[float] = None
    safety_disclaimer: str = (
        "AI decision support only. All clinical and operational decisions remain the sole responsibility of qualified healthcare professionals."
    )


class HospitalBrainEvent(BaseModel):
    id: int
    source_module: HospitalBrainSourceModule
    event_type: HospitalBrainEventType
    severity: AIAlertSeverity
    title: str
    description: str
    current_value: Optional[Any] = None
    predicted_value: Optional[Any] = None
    unit: Optional[str] = None
    risk_level: AIRiskLevel
    priority: OperationalPriorityBreakdown
    explanation: HospitalBrainExplanation
    recommended_action: str
    related_entity_type: str
    related_entity_id: Optional[str] = None
    correlated_sources: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    status: AIAlertStatus = AIAlertStatus.ACTIVE
    source_prediction_id: Optional[int] = None
    is_composite_correlation: bool = False

    model_config = {"from_attributes": True}


class DepartmentStatusSummary(BaseModel):
    department_id: Optional[int] = None
    department_name: str
    department_code: str
    status: HospitalSystemStatus
    load_level: str  # e.g., "NORMAL", "MODERATE", "WATCH", "HIGH", "CRITICAL"
    active_events_count: int
    key_metrics: Dict[str, Any]
    recommended_reviews: List[str]


class TopKPIsSummary(BaseModel):
    hospital_capacity_percent: float
    hospital_status: HospitalSystemStatus
    emergency_load_level: str
    active_emergency_count: int
    opd_predicted_wait_minutes: int
    opd_queue_count: int
    available_beds_count: int
    total_beds_count: int
    pharmacy_critical_depletion_count: int
    lab_pending_orders_count: int
    active_intelligence_count: int
    critical_alerts_count: int
    departments_affected_count: int


class HospitalBrainOverview(BaseModel):
    hospital_status: HospitalSystemStatus
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    kpis: TopKPIsSummary
    active_events: List[HospitalBrainEvent]
    department_matrix: List[DepartmentStatusSummary]
    top_recommended_actions: List[str]
    is_simulation_mode: bool = False


class HospitalCapacityMatrix(BaseModel):
    total_beds: int
    occupied_beds: int
    available_beds: int
    current_occupancy_percent: float
    projected_24h_occupancy_percent: float
    icu_total: int
    icu_occupied: int
    icu_available: int
    icu_occupancy_percent: float
    wards: List[Dict[str, Any]]
    queue_wait_summary: Dict[str, Any]


class HospitalBrainActionItem(BaseModel):
    id: int
    event_id: int
    title: str
    recommended_action: str
    severity: AIAlertSeverity
    responsible_department: str
    status: AIAlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_name: Optional[str] = None


class WhatIfSimulationRequest(BaseModel):
    emergency_arrival_delta_pct: float = Field(default=0.0, ge=-50.0, le=200.0, description="Change in ER arrivals %")
    icu_occupancy_delta_pct: float = Field(default=0.0, ge=-50.0, le=100.0, description="Change in ICU occupancy %")
    opd_demand_delta_pct: float = Field(default=0.0, ge=-50.0, le=200.0, description="Change in OPD queue demand %")
    ward_discharge_rate_delta_pct: float = Field(default=0.0, ge=-80.0, le=100.0, description="Change in discharge speed %")


class WhatIfSimulationImpact(BaseModel):
    baseline_value: float
    simulated_value: float
    delta_value: float
    unit: str
    risk_level: AIRiskLevel
    impact_description: str


class WhatIfSimulationResponse(BaseModel):
    scenario_title: str
    simulation_label: str = "SIMULATION: Scenario-based estimate. Not a real-time forecast."
    projected_hospital_status: HospitalSystemStatus
    impacts: Dict[str, WhatIfSimulationImpact]
    affected_departments: List[str]
    emerging_risks: List[str]
    recommended_preemptive_actions: List[str]
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

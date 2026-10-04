from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.ai.brain.schemas import HospitalSystemStatus, HospitalBrainEvent, TopKPIsSummary


class DemoScenarioCategory(str):
    BASELINE = "BASELINE"
    QUEUE = "QUEUE"
    EMERGENCY = "EMERGENCY"
    CAPACITY = "CAPACITY"
    INVENTORY = "INVENTORY"
    DIAGNOSTICS = "DIAGNOSTICS"
    CORRELATED_CRISIS = "CORRELATED_CRISIS"


class DemoScenario(BaseModel):
    id: int
    code: str
    title: str
    description: str
    category: str
    button_label: str
    expected_intelligence: str
    expected_risks: List[str]
    affected_departments: List[str]
    is_flagship: bool = False
    target_metrics: Dict[str, Any] = Field(default_factory=dict)


class DemoScenarioLaunchRequest(BaseModel):
    scenario_code: str


class DemoScenarioResult(BaseModel):
    scenario_code: str
    title: str
    hospital_status: HospitalSystemStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    telemetry_impact: Dict[str, Any]
    generated_events: List[HospitalBrainEvent]
    pipeline_stage: int
    message: str


class DemoResetResponse(BaseModel):
    status: str
    message: str
    reset_timestamp: datetime = Field(default_factory=datetime.utcnow)
    baseline_kpis: Dict[str, Any]


class DemoPipelineStep(BaseModel):
    step_number: int
    step_name: str
    description: str
    is_completed: bool
    is_active: bool
    detected_at: Optional[datetime] = None
    contributing_signals: List[str] = Field(default_factory=list)


class DemoPipelineProgress(BaseModel):
    active_scenario_code: str
    active_scenario_title: str
    hospital_status: HospitalSystemStatus
    steps: List[DemoPipelineStep]
    summary_recommendation: str


class PatientJourneyEvent(BaseModel):
    stage_id: int
    stage_name: str  # e.g., Registration, Appointment, OPD Token, Consultation, Lab, Pharmacy, Billing, Admission, Bed, Discharge
    timestamp: str
    department: str
    responsible_role: str
    status: str
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
    ai_insight: Optional[str] = None
    is_clinical_alert: bool = False


class PatientJourneyResponse(BaseModel):
    patient_id: int
    mrn: str
    patient_name: str
    age: int
    gender: str
    blood_group: Optional[str] = None
    allergies: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    admission_status: str
    events_count: int
    journey_stages: List[PatientJourneyEvent]

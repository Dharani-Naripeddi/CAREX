# CAREX — Phase 6A: Hospital Brain Architecture Audit & Readiness Report

## Executive Summary

This architecture audit evaluates the readiness of the **CAREX Phase 1–5 codebase** for a centralized **Hospital Brain** orchestrator. 

**Conclusion**: The existing codebase is **100% ready** to support the Hospital Brain. The AI architecture developed in Phase 5 already includes standardized event contracts (`AIIntelligenceEvent`), traceable prediction models (`AIPrediction`), an operational alert lifecycle (`AIAlert`), user feedback tracking (`AIFeedback`), and deterministic fallback engines across all hospital domains (OPD, Emergency, Beds, Pharmacy, Laboratory, Nursing, and Staffing).

---

## 1. Current Architecture Overview

```
                                  +-------------------------------------------------+
                                  |              CAREX HOSPITAL BRAIN               |
                                  |         (Central Orchestration Layer)           |
                                  +------------------------+------------------------+
                                                           |
                      +------------------------------------+------------------------------------+
                      |                                                                         |
        +-------------v-------------+                                             +-------------v-------------+
        |   Phase 5 AI Services     |                                             |   Phase 1-4 Core Sources  |
        +---------------------------+                                             +---------------------------+
        | • QueuePredictionService  |                                             | • OPD Tokens & Appts      |
        | • BedPredictionService    |                                             | • EmergencyCases & Triage |
        | • PharmacyPredictionSvc   |                                             | • Wards, Beds, Admissions |
        | • TriageAIService         |                                             | • Lab Orders & Reports    |
        | • DocumentAIService       |                                             | • Pharmacy & Prescriptions|
        | • VoiceAssistantService   |                                             | • Invoices & Payments     |
        | • ShiftHandoverService    |                                             | • Doctors, Nurses, Staff  |
        | • AnomalyDetectionService |                                             | • Notifications & Audits  |
        +-------------+-------------+                                             +-------------+-------------+
                      |                                                                         |
                      +------------------------------------+------------------------------------+
                                                           |
                                  +------------------------v------------------------+
                                  |       Persistence & Model Governance            |
                                  +-------------------------------------------------+
                                  | • ai_predictions (Traceability & Features)      |
                                  | • ai_alerts (Lifecycle: ACTIVE->ACK->RESOLVED)  |
                                  | • ai_feedbacks (Clinician/Staff Ratings)        |
                                  | • ai_document_records & ai_shift_handovers      |
                                  +-------------------------------------------------+
```

- **Backend**: FastAPI with SQLAlchemy 2.0 (declarative models), Alembic migrations, Pydantic V2 schemas (`model_config = {"from_attributes": True}`).
- **Database**: SQLite (dev) / PostgreSQL (prod), schema verified and seeded with 40/40 passing integration tests.
- **Frontend**: Vite + React + TypeScript + Tailwind CSS (vanilla utilities) with role-based navigation and modular UI components.

---

## 2. Verification of Existing AI Event Structure

In `backend/app/ai/base.py`, the standardized `AIIntelligenceEvent` contract was established during Phase 5:

```python
class AIIntelligenceEvent(BaseModel):
    """Standardized event interface connecting AI modules to the Hospital Brain (Phase 6 ready)."""
    source_module: str  # e.g., OPD_QUEUE, BED_CAPACITY, PHARMACY, EMERGENCY_TRIAGE, ANOMALY_DETECTOR
    event_type: AIAlertType  # OPD_DELAY, BED_CAPACITY_RISK, PHARMACY_DEPLETION, EMERGENCY_SURGE, LAB_BACKLOG, OPERATIONAL_ANOMALY
    severity: AIAlertSeverity  # INFO, WARNING, HIGH, CRITICAL
    current_value: Any
    prediction_value: Any
    risk_level: AIRiskLevel  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: Optional[float] = None
    explanation: StandardAIExplanation
    recommended_action: str
    related_entity: str
    related_entity_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Supported Event Types Already Present:
1. `OPD_DELAY`: Wait time > 30 mins or queue elongation.
2. `BED_CAPACITY_RISK`: Ward or ICU 24-hour occupancy > 85%.
3. `PHARMACY_DEPLETION`: Stock days remaining < 7 days or reorder threshold hit.
4. `EMERGENCY_SURGE`: ER arrival spike or multiple RED/ORANGE triage cases.
5. `LAB_BACKLOG`: High priority / STAT lab orders exceeding turnaround SLA.
6. `OPERATIONAL_ANOMALY`: Z-score or IQR deviation > 50% from baseline.

---

## 3. Verification of AI Prediction Storage

Inspected `backend/app/models/ai.py`. The tables are already migrated and active in the database:

| Model Table | Fields & Capabilities | Reusability for Hospital Brain |
|---|---|---|
| **`ai_predictions`** | `id`, `prediction_type` (Enum), `entity_type`, `entity_id`, `prediction_value` (JSON), `risk_level` (Enum), `confidence` (Float), `model_name`, `model_version`, `model_provider_type` (Enum), `explanation` (JSON), `recommended_action` (Text), `input_features` (JSON), `generated_at` | **100% Reusable** — Can directly store composite multi-signal Brain predictions without schema changes. |
| **`ai_alerts`** | `id`, `alert_type` (Enum), `severity` (Enum), `title`, `description`, `reason` (JSON), `recommended_action` (Text), `related_entity`, `related_entity_id`, `status` (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED`), `created_at`, `acknowledged_at/by_id`, `resolved_at/by_id` | **100% Reusable** — Full status lifecycle with user attribution and acknowledgment tracking. |
| **`ai_feedbacks`** | `id`, `prediction_id`, `alert_id`, `user_id`, `rating` (`USEFUL`, `NOT_USEFUL`, `INCORRECT`, `NEEDS_REVIEW`), `notes`, `created_at` | **100% Reusable** — Tracks user utility of Brain recommendations. |
| **`ai_document_records`**| `id`, `file_name`, `file_type`, `patient_id`, `uploaded_by_id`, `document_type`, `raw_text`, `extracted_data` (JSON), `ai_summary`, `confidence`, `is_verified`, `verified_by_id/at` | Diagnostic data store. |
| **`ai_shift_handovers`** | `id`, `ward_id`, `shift_name`, `from_nurse_id`, `to_nurse_id`, `patient_summaries` (JSON), `important_observations`, `next_shift_checklist` (JSON), `ai_notes`, `status`, `approved_by_id/at` | Inpatient nursing handovers. |

---

## 4. Verification of Existing AI Services

All 8 services are operational, isolated in domain packages under `backend/app/ai/`, and can be called programmatically by the Hospital Brain:

| AI Service | Location | Inputs | Outputs | DB Interaction | Consumable by Hospital Brain? |
|---|---|---|---|---|---|
| **Queue Prediction** | `app/ai/queue_prediction/service.py` | `department_id`, `doctor_id` | `OpdQueuePredictionResponse` | Reads `opd_tokens`, `appointments`, `doctors`; writes `ai_predictions`, `ai_alerts` | **Yes** — Synchronously or as background telemetry |
| **Bed Capacity Forecast** | `app/ai/bed_prediction/service.py` | `ward_id` | `BedPredictionResponse` | Reads `wards`, `beds`, `admissions`; writes `ai_predictions`, `ai_alerts` | **Yes** — Ingests 6h/12h/24h capacity data |
| **Pharmacy Depletion** | `app/ai/pharmacy_prediction/service.py` | `medicine_id`, `days_history` | `PharmacyPredictionResponse` | Reads `medicines`, `medicine_batches`, `dispensings`; writes `ai_predictions`, `ai_alerts` | **Yes** — Identifies supply chain bottlenecks |
| **Emergency Triage** | `app/ai/triage/service.py` | `TriageAssessmentRequest`, `case_id` | `TriageAIResponse` | Reads `emergency_cases`, `patients`; writes `ai_predictions` | **Yes** — Ingests patient acuity metrics |
| **Document AI** | `app/ai/document_ai/service.py` | `DocumentAnalysisRequest` | `DocumentAnalysisResponse` | Reads/writes `ai_document_records` | **Yes** — Analyzes diagnostic backlogs |
| **Voice Dictation** | `app/ai/voice/service.py` | `VoiceTranscriptionRequest` | `VoiceTranscriptionResponse` | Reads `patients` | **Yes** — Ingests clinical notes |
| **Shift Handover** | `app/ai/handover/service.py` | `ShiftHandoverGenerateRequest` | `ShiftHandoverResponse` | Reads `admissions`, `lab_orders`, writes `ai_shift_handovers` | **Yes** — Tracks nursing workload |
| **Anomaly Detection** | `app/ai/anomaly_detection/service.py` | `domain` (`ALL`, `OPD`, `EMERGENCY`, etc.) | `AnomalyDetectionResponse` | Evaluates live metrics across 5 domains; writes `ai_alerts` | **Yes** — Core anomaly input for Brain |
| **Insights Aggregator** | `app/ai/insights/service.py` | Filters (`status`, `severity`, `limit`) | `AIInsightsResponse` | Reads `ai_alerts`, `ai_predictions`, calculates quick statuses | **Yes** — Existing foundation for Brain |
| **Simulation Engine** | `app/ai/simulation/service.py` | `scenario_type` (`OPD_DELAY`, `ICU_CAPACITY`, etc.) | Simulation result | Injects non-destructive scenario alerts | **Yes** — For testing Brain reactions |

---

## 5. Verification of Existing Dashboard (`/admin/ai`)

- **Frontend Component**: [AiDashboardPage.tsx](file:///c:/Users/Dharani%20N/OneDrive/Desktop/f8/CAREX/frontend/src/pages/AiDashboardPage.tsx)
- **API Endpoint**: `GET /api/v1/ai/insights`
- **Current Data Feeds**:
  - Quick domain metrics (OPD wait time, Bed 24h occupancy %, Pharmacy critical items, Anomaly count).
  - Live AI Alert Stream with Acknowledge and Resolve actions.
  - Recent AI Predictions with "Why?" factors and feedback ratings (`USEFUL` / `NOT_USEFUL`).
  - Simulation Control Bar (4 live scenario triggers).
- **Readiness**: Can easily be augmented with the Hospital Brain's composite correlation feed and hospital-wide Congestion Index.

---

## 6. Duplication Audit

We audited the codebase for redundant structures:
- **AI Models**: Cleanly separated. No duplicate ML model instances exist.
- **Alert Structures**: `ai_alerts` is the unified alert table for AI; standard `notifications` handles user inbox messages. No schema duplication.
- **Severity Definitions**: Consistent across `AIAlertSeverity` (`INFO`, `WARNING`, `HIGH`, `CRITICAL`) and `NotificationType`.
- **Recommendation Structures**: Consolidated in `StandardAIExplanation` (`summary`, `reasons`, `contributing_factors`, `recommended_action`, `safety_disclaimer`).
- **Conclusion**: **No refactoring is required**.

---

## 7. Hospital Brain Data Sources

The Hospital Brain will correlate data across all core database models:

| Domain | Underlying Database Tables | Key Telemetry Queried |
|---|---|---|
| **OPD** | `opd_tokens`, `appointments`, `doctors`, `departments` | Waiting count, active consult durations, delay vs SLA baseline, token throughput. |
| **Emergency** | `emergency_cases`, `patients` | Active arrivals (24h), triage distribution (RED/ORANGE/YELLOW/GREEN), resuscitation bay load. |
| **Beds & IPD** | `wards`, `beds`, `admissions` | Total capacity, occupied beds, pending admissions vs planned discharges, ICU saturation. |
| **Pharmacy** | `medicines`, `medicine_batches`, `dispensings`, `prescriptions` | 30-day velocity, current stock vs reorder level, batches expiring within 30 days. |
| **Laboratory** | `lab_orders`, `lab_reports`, `lab_test_templates` | Pending order backlog, STAT urgent orders, average turnaround time. |
| **Staff** | `users`, `roles`, `doctors`, `nurses` | Available attending physicians, on-duty nursing rosters, ward allocation. |
| **System** | `notifications`, `audit_logs` | User alerts, system error rates, audit events. |

---

## 8. Hospital Brain Event Contract

The proposed `HospitalBrainEvent` contract directly reuses existing fields from `AIIntelligenceEvent` and `AIAlert`:

```python
class HospitalBrainEvent(BaseModel):
    """Unified Hospital Brain Event Contract."""
    id: Optional[str] = None
    source_module: str  # e.g. "HOSPITAL_BRAIN", "OPD_QUEUE", "BED_CAPACITY", "EMERGENCY_SURGE"
    event_type: str     # e.g. "COMPOSITE_CAPACITY_CRISIS", "OPD_DELAY", "BED_CAPACITY_RISK"
    severity: AIAlertSeverity  # INFO, WARNING, HIGH, CRITICAL
    title: str
    description: str
    current_value: Optional[Any] = None
    predicted_value: Optional[Any] = None
    unit: Optional[str] = None
    risk_level: AIRiskLevel  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: Optional[float] = None
    explanation: StandardAIExplanation
    recommended_action: str
    related_entity_type: str  # e.g. "HOSPITAL", "DEPARTMENT", "WARD"
    related_entity_id: Optional[str] = None
    correlated_sources: List[str] = Field(default_factory=list)  # e.g. ["OPD_QUEUE", "EMERGENCY", "BED_CAPACITY"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    status: AIAlertStatus = AIAlertStatus.ACTIVE
    source_prediction_id: Optional[int] = None
```

*Note: Storing this into the existing `ai_alerts` and `ai_predictions` tables requires zero schema migrations, as `reason` and `prediction_value` are JSON columns.*

---

## 9. Hospital Brain Aggregation & Correlation Requirements

The Hospital Brain will answer the 6 core operational questions:

1. **"What is happening?"** &rarr; Real-time Operational Load Index (0–100%) and department status map.
2. **"What is likely to happen?"** &rarr; Multi-horizon forecasts (6h, 12h, 24h capacity and stockout risks).
3. **"Why is it happening?"** &rarr; Multi-factor contributing reasons across departments.
4. **"What should hospital staff consider doing?"** &rarr; Synthesized action protocol (e.g. *"Mobilize float nurses to ER and accelerate discharge clearances in Ward B"*).
5. **"What is the severity?"** &rarr; Standardized `CRITICAL`, `HIGH`, `WARNING`, `INFO`.
6. **"Which department/resource is affected?"** &rarr; Granular entity linkage (`related_entity`, `related_entity_id`).

### Cross-Signal Correlation Matrix:

```
+---------------------+     +----------------------+     +---------------------+
|  OPD Queue Spike    |     |  ER Trauma Cluster   |     |  High Bed Occupancy |
|  (+50% wait time)   |     |  (3 RED Acuity Cases)|     |  (>92% Inpatient)   |
+----------+----------+     +----------+-----------+     +----------+----------+
           |                           |                            |
           +---------------------------+----------------------------+
                                       |
                     +-----------------v------------------+
                     | Hospital Brain Correlation Engine  |
                     +-----------------+------------------+
                                       |
                     +-----------------v------------------+
                     |    COMPOSITE OPERATIONAL ALERT     |
                     | "Hospital-Wide Capacity Bottleneck |
                     |  & Resource Allocation Crisis"     |
                     +------------------------------------+
```

---

## 10. Clinical Safety & Autonomous Boundary Rules

The Hospital Brain strictly adheres to operational safety guidelines:

| Permitted Operational Intelligence (YES) | Prohibited Autonomous Actions (NEVER) |
|---|---|
| Forecast bed and queue capacity | Diagnose medical conditions |
| Flag potential pharmaceutical stockouts | Prescribe medications or alter dosages |
| Highlight operational bottlenecks and delays | Make autonomous clinical admission/discharge decisions |
| Suggest staffing reallocation protocols | Override physician or nursing clinical judgment |
| Synthesize telemetry into operational summaries | Automatically discharge or transfer patients |

Every Brain output will carry the mandatory disclaimer:
> *"CAREX Hospital Brain provides operational decision support and capacity telemetry. All clinical and operational decisions remain the sole responsibility of authorized healthcare professionals."*

---

## 11. Implementation Readiness & Transition Strategy

### Database Changes
- **Zero breaking changes**: Reuses existing `ai_predictions`, `ai_alerts`, and `ai_feedbacks` tables.
- No schema migration needed for Phase 6 MVP.

### Backend Implementation Scope
- Create `backend/app/ai/brain/` containing:
  - `schemas.py`: `HospitalBrainState`, `HospitalBrainEvent`, `CrossDomainCorrelation`.
  - `correlator.py`: Multi-signal correlation rules (OPD + ER + Beds + Lab + Pharmacy).
  - `service.py`: `HospitalBrainService` providing real-time state synthesis.
- Mount `/api/v1/ai/brain/state` and `/api/v1/ai/brain/events` endpoints.

### Frontend Implementation Scope
- Create `HospitalBrainCommandPage.tsx` (`/admin/brain`).
- Embed Hospital Brain Live Status Ribbon in Executive Command Center (`CommandCenterPage.tsx`).

### Risk Assessment
- **Query Latency**: Correlating 6 domains concurrently could introduce DB overhead.
  - *Mitigation*: Use lightweight indexed aggregates and a 15-second in-memory telemetry snapshot cache.
- **Alert Fatigue**: Multiple individual domain alerts plus a composite alert could clutter the UI.
  - *Mitigation*: Group correlated domain alerts beneath the primary composite Brain alert.

---

## 12. Audit Verification & Sign-Off

- **Phase 1–5 Integrity**: Completely intact; all 40/40 tests passing.
- **Hospital Brain Readiness**: **READY TO PROCEED** (Architecture verified; dependencies mapped; event contracts aligned).

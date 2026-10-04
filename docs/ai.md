# CAREX AI Intelligence Layer — Phase 5 Documentation

## 1. Architectural Overview

The **CAREX AI Intelligence Layer** provides real-time decision support, capacity forecasting, and operational anomaly detection across hospital domains without external third-party API dependencies or vendor lock-in.

```
                                +-----------------------------------+
                                |     CAREX Hospital System API     |
                                +-----------------+-----------------+
                                                  |
                     +----------------------------+----------------------------+
                     |                                                         |
        +------------v-------------+                             +-------------v------------+
        |   Predictive AI Services |                             | Clinical Support Services|
        +--------------------------+                             +--------------------------+
        | • OPD Queue Forecasting  |                             | • Emergency Triage Engine|
        | • Bed Capacity Markov    |                             | • Document Intelligence  |
        | • Pharmacy FEFO Velocity |                             | • Voice Note Structuring |
        | • Operational Anomalies  |                             | • AI Shift Handover      |
        +------------+-------------+                             +-------------+------------+
                     |                                                         |
                     +----------------------------+----------------------------+
                                                  |
                               +------------------v------------------+
                               | Model Transparency & Safety Layer   |
                               +-------------------------------------+
                               | • Model Badges (TRAINED / STAT / ..)|
                               | • Zero Fabricated Confidence Metric |
                               | • Structured "Why?" Factors         |
                               | • Recommended Protocol Actions      |
                               | • AIFeedback & Traceable Audit Trail|
                               +-------------------------------------+
```

---

## 2. Model Governance & Transparency Standards

Every AI prediction and recommendation rendered in CAREX strictly complies with the following principles:

1. **Explicit Model Provider Attribution**:
   - `TRAINED_ML`: Supervised machine learning or neural statistical models calibrated on real operational historical dataset distributions.
   - `STATISTICAL_MODEL`: Time-series moving averages, Markov transitions, Z-Score standard deviation thresholds.
   - `RULE_BASED`: Deterministic Emergency Severity Index (ESI) & Manchester Triage physiological protocols.
   - `FALLBACK_SIMULATION`: Operational estimations used when insufficient historical records exist.
2. **Zero Fabricated Confidence**: If sample size is insufficient, the system explicitly displays:
   > *"Using operational estimate — insufficient historical data for trained ML prediction."*
3. **Structured Explanation Format**:
   - **Prediction Value**: Quantitative forecast (e.g. estimated wait time, 24h occupancy percentage, stockout date).
   - **Risk Level**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
   - **Why?**: Multi-factor clinical or operational reasons (e.g. recent consult duration elongation, triage acuity mix).
   - **Recommended Action**: Actionable hospital SOP protocol.
4. **Clinical Safety Disclaimers**:
   - All diagnostic, triage, and voice note modules display mandatory disclaimers emphasizing that AI outputs are for decision support only and require qualified healthcare professional review and sign-off.

---

## 3. Implemented AI Domains

### 3.1 OPD Queue Prediction
- **Module**: `backend/app/ai/queue_prediction/`
- **Route**: `/admin/ai/queue`
- **Capabilities**:
  - Calculates real-time estimated wait times based on queue size and consultation duration velocity.
  - Compares against historical baseline SLA to compute delay risks.
  - Computes doctor capacity utilization and generates 6-hour hourly throughput projections.

### 3.2 Bed Occupancy & Capacity Forecasting
- **Module**: `backend/app/ai/bed_prediction/`
- **Route**: `/admin/ai/bed-forecast`
- **Capabilities**:
  - Multi-horizon forecasting (6-hour, 12-hour, and 24-hour occupancy percentages).
  - Risk thresholds: `LOW <70%`, `MEDIUM 70-85%`, `HIGH 85-95%`, `CRITICAL >95%`.
  - Ward-by-ward breakdown highlighting ICU, CCU, and emergency capacity saturation.

### 3.3 Pharmacy Stock Depletion & Inventory Intelligence
- **Module**: `backend/app/ai/pharmacy_prediction/`
- **Route**: `/admin/ai/pharmacy`
- **Capabilities**:
  - Daily dispensing velocity analysis across 30-day transactional windows.
  - Days-of-supply countdown and exact predicted depletion dates.
  - Automated purchase replenishment suggestions to maintain safety buffers.
  - Expiry alert integration prioritizing FEFO (First-Expired, First-Out) dispensing.

### 3.4 Emergency Triage Decision Support
- **Module**: `backend/app/ai/triage/`
- **API**: `POST /api/v1/ai/triage/assess`
- **Capabilities**:
  - Physiological vital sign evaluation (SpO2, Systolic BP, Heart Rate, Respiratory Rate, Temperature, Consciousness).
  - ESI category priority recommendation (`RED`, `ORANGE`, `YELLOW`, `GREEN`).
  - Highlights critical vital flags and specifies target physician evaluation windows.

### 3.5 Medical Document Intelligence
- **Module**: `backend/app/ai/document_ai/`
- **Route**: `/ai/documents`
- **Capabilities**:
  - Extracts parameters, numeric values, units, and reference ranges from diagnostic reports.
  - Identifies out-of-range observations (`LOW`, `HIGH`, `CRITICAL`).
  - Summarizes diagnostic findings and supports clinician verification and sign-off.

### 3.6 Voice-to-Clinical-Note Dictation
- **Module**: `backend/app/ai/voice/`
- **Component**: `VoiceNoteAssistantModal.tsx` (Embedded in `/doctors`)
- **Capabilities**:
  - Real-time speech-to-text dictation processor with NLP structuring into SOAP fields: Chief Complaint, Duration, Vitals, Exam Findings, Assessment & Plan.
  - Full clinician editing and explicit sign-off workflow.

### 3.7 AI Nursing Shift Handover
- **Module**: `backend/app/ai/handover/`
- **Route**: `/ai/handover`
- **Capabilities**:
  - Aggregates active admitted ward inpatients, latest telemetry vitals, and pending lab orders.
  - Compiles next-shift task checklists and handover notes.
  - Supports nurse review, observation editing, and approval sign-off.

### 3.8 Operational Anomaly Detection
- **Module**: `backend/app/ai/anomaly_detection/`
- **Route**: `/admin/ai/anomalies`
- **Capabilities**:
  - Statistical deviation model tracking OPD queue surges, ER trauma clusters, bed spikes, lab backlogs, and stockout outliers.
  - Automatically posts active alerts into the unified hospital alert stream.

---

## 4. Controlled Simulation Scenarios

CAREX provides 4 non-destructive demo scenarios to demonstrate operational intelligence without corrupting underlying clinical data:

| Scenario Key | Trigger Name | Simulated Event |
|---|---|---|
| `OPD_DELAY` | Cardiology Queue Delay | Elongated consultation duration (+65% over baseline) with 14 waiting patients. |
| `ICU_CAPACITY` | Critical ICU Saturation | 96% 24h occupancy forecast with 1 ventilator bed remaining. |
| `PHARMACY_DEPLETION` | Critical Stockout | Azithromycin 500mg down to 1.4 days supply; triggers PO-PHARM-2026-088. |
| `EMERGENCY_SURGE` | Code Yellow Trauma Cluster | Mass transit incident resulting in 8 arrivals in 30 mins with 3 RED triage cases. |

Triggers can be executed from the AI Dashboard (`/admin/ai`) or via `POST /api/v1/ai/simulation/trigger`.

---

## 5. API Reference Summary

| Endpoint | Method | Role Permissions | Description |
|---|---|---|---|
| `/api/v1/ai/insights` | GET | All staff roles | Aggregated hospital AI telemetry and active alerts stream |
| `/api/v1/ai/queue/predict` | POST | Admin, Reception, Doctor, Nurse | OPD queue wait-time and delay prediction |
| `/api/v1/ai/beds/predict` | POST | Admin, Doctor, Nurse, Reception | 6h/12h/24h ward and ICU capacity forecasting |
| `/api/v1/ai/pharmacy/predict` | POST | Admin, Pharmacist, Doctor | Pharmacy stock depletion and reorder velocity |
| `/api/v1/ai/triage/assess` | POST | Admin, Reception, Doctor, Nurse | Emergency triage physiological decision support |
| `/api/v1/ai/documents/analyze` | POST | Admin, Doctor, Lab Tech | Medical laboratory document entity extraction |
| `/api/v1/ai/documents/{id}/verify`| POST | Doctor, Lab Tech, Admin | Clinician sign-off for analyzed document |
| `/api/v1/ai/voice/transcribe` | POST | Doctor, Admin | Voice-to-clinical note structuring |
| `/api/v1/ai/handover/generate` | POST | Nurse, Admin, Doctor | Nursing shift handover generation |
| `/api/v1/ai/handover/{id}/approve`| POST | Nurse, Admin | Nursing shift handover approval |
| `/api/v1/ai/anomalies/detect` | POST | Admin, Doctor, Nurse | Operational anomaly detection |
| `/api/v1/ai/alerts` | GET | All staff roles | List active and acknowledged operational alerts |
| `/api/v1/ai/alerts/{id}/acknowledge`| POST| All staff roles | Acknowledge active alert |
| `/api/v1/ai/alerts/{id}/resolve` | POST | All staff roles | Resolve operational alert |
| `/api/v1/ai/predictions` | GET | All staff roles | Full audit trail of historical AI predictions |
| `/api/v1/ai/feedback` | POST | All staff roles | Submit user feedback rating on AI outputs |
| `/api/v1/ai/simulation/trigger` | POST | Admin | Trigger controlled live demo scenario |

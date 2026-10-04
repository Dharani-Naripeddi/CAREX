# CAREX Hospital Brain — Architecture & Operational Intelligence Documentation

## 1. System Overview

The **CAREX Hospital Brain** is the centralized operational intelligence and cross-department decision-support engine of the CAREX Healthcare Information System. Building on the underlying clinical datasets (Phases 1–4) and the 8 dedicated predictive services (Phase 5), the Hospital Brain synthesizes cross-department telemetry into a unified operational command center.

It is designed to proactively answer the six fundamental operational questions of healthcare management:
1. **What is happening in the hospital?** (Live state across emergency, outpatient queues, inpatient capacity, pharmacy, and diagnostic laboratory)
2. **What is likely to happen next?** (Predictive horizons for queue bottlenecks, bed saturation, and stock depletions)
3. **Why is it happening?** (Transparent signal breakdown explaining contributing telemetry)
4. **How serious is it?** (Explainable 0–100 Operational Priority Score)
5. **Which departments or resources are affected?** (Cross-module dependency mapping)
6. **What should hospital administrators and coordinators consider doing?** (Actionable, protocol-driven operational playbooks)

---

## 2. Mandatory Clinical & Operational Safety Boundaries

> [!IMPORTANT]
> **Safety Notice:** The CAREX Hospital Brain is strictly an **operational decision-support system** designed for bed flow, queue coordination, inventory management, and resource allocation.
> - It is **NOT** a clinical diagnostic system.
> - It does **NOT** autonomously dispense medications or make clinical treatment decisions.
> - All recommendations are non-prescriptive reviews (e.g., *"Operational risk detected. Review recommended."*).
> - Final clinical judgment and patient disposition decisions remain exclusively with licensed healthcare professionals.

---

## 3. Hospital Brain Architecture & Data Ingestion

```mermaid
flowchart TD
    subgraph Core HMS Telemetry (Phases 1-4)
        T_OPD[OPD Tokens & Appointments]
        T_ER[Emergency Arrivals & Triage Cases]
        T_BED[Beds, Wards & Transfers]
        T_LAB[Lab Orders & Diagnostic TAT]
        T_PHARM[Pharmacy Stocks & Dispensings]
    end

    subgraph Phase 5 AI Intelligence Engine
        AI_Q[OPD Queue Predictor]
        AI_B[Bed Capacity Forecaster]
        AI_P[Pharmacy Depletion Forecaster]
        AI_A[Anomaly Detection Engine]
        AI_H[Handover & Document AI]
    end

    subgraph Central Hospital Brain Core (Phase 6)
        INGEST[Real-Time Telemetry Ingestion Layer]
        SCORER[Operational Priority Scorer (0-100)]
        CORR[Cross-Module Correlator Engine]
        SIM[What-If Scenario Simulator]
        AUDIT[Audit Trail & Lifecycle Tracker]
    end

    subgraph Flagship Command Center & Clients
        CC[Flagship Hospital Brain Command Center]
        WHY[Explainability 'Why?' Inspector]
        MATRIX[Department Status Matrix]
        ACTIONS[Action Playbook Center]
    end

    T_OPD & T_ER & T_BED & T_LAB & T_PHARM --> INGEST
    AI_Q & AI_B & AI_P & AI_A & AI_H --> INGEST
    INGEST --> CORR
    INGEST --> SCORER
    CORR --> SCORER
    CORR --> AUDIT
    SCORER --> CC
    CORR --> CC
    SIM --> CC
    CC --> WHY
    CC --> MATRIX
    CC --> ACTIONS
```

---

## 4. Operational Priority Scoring Algorithm (0–100)

Every operational alert and correlated composite crisis is scored using a transparent, multi-dimensional algorithm:

$$\text{Priority Score} = \sum (\text{Dimension Weight} \times \text{Dimension Score})$$

### Scoring Dimensions:

| Dimension | Weight | Description | Factor Contributing Logic |
| :--- | :---: | :--- | :--- |
| **Alert Severity** | **30%** | Baseline severity rating | Critical = 100, High = 75, Warning = 50, Info = 25 |
| **Operational Impact** | **25%** | Departmental & resource breadth | Score rises if critical resources (ICU, Emergency, Oxygen) are affected |
| **Correlation Multiplier** | **25%** | Cross-department corroboration | Score escalates when 2 or more distinct modules confirm risk |
| **Signal Persistence** | **20%** | Duration of unmitigated pressure | Increases by 10 points per hour active without resolution |

### Score Ratings:
- **0 – 39**: `LOW`
- **40 – 64**: `MODERATE`
- **65 – 79**: `HIGH`
- **80 – 100**: `CRITICAL` (Triggers urgent administrative alert)

---

## 5. Multi-Signal Cross-Module Correlation Rules

The Correlator analyzes concurrent signals across siloed departments to detect composite hospital-wide crises:

1. **`HOSPITAL_CAPACITY_RISK` (SIH Signature Workflow)**:
   - **Triggers when**: High Emergency Inflow / Surge + High Inpatient Bed Occupancy ($\ge 85\%$) + OPD Queue Delay ($\ge 30\text{ mins}$).
   - **Explanation**: Upstream emergency intake combined with delayed bed turnover and OPD backlog creates institutional gridlock.
   - **Recommended Playbook**: Expedite medically stable IPD discharges, activate on-call clinical staff, and open overflow consultation rooms.

2. **`BED_CAPACITY_RISK` (Critical Inpatient / ICU Bottleneck)**:
   - **Triggers when**: ICU Occupancy $\ge 85\%$ or Total Bed Occupancy $\ge 90\%$, alongside active acute emergency cases.
   - **Explanation**: Acute admissions risk boarding in ER hallways due to lack of monitored beds.
   - **Recommended Playbook**: Review step-down ICU candidates and prepare transit bed capacity.

3. **`LAB_BACKLOG` (Diagnostic Bottleneck Delaying Inpatient Triage)**:
   - **Triggers when**: $\ge 15$ pending lab orders or $\ge 3$ pending STAT orders.
   - **Explanation**: Diagnostic turnaround delay is holding up emergency triage and ward admission decisions.
   - **Recommended Playbook**: Reallocate lab technician shifts and expedite STAT test processing.

---

## 6. What-If Capacity Scenario Simulation Engine

The Brain includes an interactive sandbox allowing hospital leadership to stress-test capacity and test contingency policies:

### Adjustable Parameters:
- $\Delta\%$ Emergency Patient Arrival Volume ($-30\%$ to $+100\%$)
- $\Delta\%$ ICU Occupancy Shift ($-20\%$ to $+50\%$)
- $\Delta\%$ Outpatient OPD Demand ($-30\%$ to $+100\%$)
- $\Delta\%$ Inpatient Discharge Velocity ($-50\%$ to $+50\%$)

### Simulation Projection Outputs:
- Projected Bed Occupancy (%)
- Projected ICU Occupancy (%)
- Projected OPD Wait Times (minutes)
- Emerging Operational Bottlenecks
- Recommended Preemptive Action Playbook

> [!NOTE]
> All simulation results clearly display the non-realtime disclaimer banner: `SIMULATION: Scenario-based estimate. Not a real-time forecast.`

---

## 7. Hospital Brain REST API Contracts

All endpoints are mounted under `/api/v1/hospital-brain`:

| Endpoint | Method | Role Access | Description |
| :--- | :---: | :--- | :--- |
| `/overview` | `GET` | All Staff | Complete operational overview, top KPIs, active events, and department matrix |
| `/events` | `GET` | All Staff | List all operational intelligence events with priority scores and filters |
| `/events/active` | `GET` | All Staff | List active events sorted by Operational Priority Score |
| `/events/{id}` | `GET` | All Staff | Granular explainability ("Why?") view with factor contributions |
| `/events/{id}/acknowledge` | `POST` | Admin, Doctor, Nurse | Acknowledge event and record user action in Audit Log |
| `/events/{id}/resolve` | `POST` | Admin, Doctor, Nurse | Mark event as resolved with audit timestamp and user attribution |
| `/departments` | `GET` | All Staff | Department Operational Intelligence Matrix across 6 clinical units |
| `/capacity` | `GET` | All Staff | Hospital-wide bed, ward, and ICU capacity matrix |
| `/actions` | `GET` | All Staff | List active operational playbooks and action items |
| `/simulation` | `POST` | Admin, Doctor | Execute What-If simulation and log execution in Audit Log |

---

## 8. Verification & Test Suite Summary

- **Automated Pytest Suite**: `backend/tests/test_hospital_brain.py`
  - Total automated tests: **48 / 48 passing (100% pass rate)**
  - Tests verify priority scoring, cross-module correlation, What-If engine, overview API, event lifecycle transitions, audit logging, and RBAC enforcement.
- **Frontend TypeScript Build**: `npm run build`
  - Zero TypeScript compilation errors.
  - Full type safety matching backend schemas via `frontend/src/types/hospital_brain.ts`.

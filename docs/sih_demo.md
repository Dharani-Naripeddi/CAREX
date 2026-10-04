# CAREX — SIH Flagship Demonstration & Architecture Guide

## Smart India Hackathon (SIH 2026) Technical Documentation

---

### Executive Overview

**CAREX** is an AI-powered Hospital Management and Intelligent Patient Coordination Platform designed to eliminate clinical communication silos, optimize hospital bed and queue capacity, and deliver real-time operational decision support.

Unlike fragmented Hospital Information Systems (HIS) or disconnected AI prototypes, CAREX integrates an autonomous **Hospital Brain** that acts as a central neural network across 8 major hospital domains: Outpatient Clinics (OPD), Inpatient Wards (IPD), Emergency & Trauma, Intensive Care Units (ICU), Diagnostic Laboratories, Central Pharmacy, Staff Coordination, and Billing.

```
+---------------------------------------------------------------------------------------------------+
|                                  CAREX HOSPITAL BRAIN ARCHITECTURE                                |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [Emergency / Trauma]   [OPD Token Queue]   [Inpatient / ICU]   [Labs & Radiology]   [Pharmacy]   |
|            |                    |                   |                   |                 |       |
|            +--------------------+-------------------+-------------------+-----------------+       |
|                                                     |                                             |
|                                       v                           v                               |
|                           [Autonomous AI Services]      [Audit Logs & Security]                   |
|                           - XGBoost Wait Forecasting    - RBAC Authorization                      |
|                           - Bed Turnover Projections    - Real-Time Traceability                  |
|                           - Stock Depletion Velocity                                              |
|                           - CDSS Triage Classifiers                                               |
|                                                     |                                             |
|                                                     v                                             |
|                                  [Central Hospital Brain Engine]                                  |
|                                  - 0-100 Priority Scoring Engine                                  |
|                                  - Cross-Module Correlation Matrix                                |
|                                  - Multi-Signal Crisis Detection                                  |
|                                  - What-If Capacity Simulation                                    |
|                                                     |                                             |
|                                                     v                                             |
|                             +-----------------------------------------------+                     |
|                             |          CAREX COMMAND DASHBOARDS             |                     |
|                             |  - Flagship Hospital Brain & Explainability   |                     |
|                             |  - 10-Touchpoint Unified Patient Journey      |                     |
|                             |  - SIH Deterministic Demo Control Center      |                     |
|                             |  - Clinical & Administrative Workspaces       |                     |
|                             +-----------------------------------------------+                     |
+---------------------------------------------------------------------------------------------------+
```

---

## 1. The 7 Deterministic SIH Demo Scenarios

CAREX provides an isolated **SIH Demo Control Center** (`/admin/demo`) that simulates hospital stress conditions without altering real clinical databases.

| # | Scenario Code | Scenario Name | Category | Primary Telemetry & Impact | Expected AI Response |
|---|---|---|---|---|---|
| **1** | `STABLE_HOSPITAL` | Baseline Stable Operations | Baseline | 68% Bed Occ, 18 min OPD Wait, 1 ICU Available | Normal operations, proactive telemetry |
| **2** | `OPD_OVERLOAD` | Outpatient Clinic Surge | Clinical Load | 52 min OPD Wait, 45% Reg Influx | Overflow consultation room recommendation |
| **3** | `EMERGENCY_SURGE` | Mass Casualty & Trauma Surge | Emergency | 3 simultaneous Code Red/Orange trauma cases | Code Yellow activation, triage bay priority |
| **4** | `ICU_CAPACITY_PRESSURE` | Critical Care Saturation | Capacity | 92% ICU Occ, 1 monitored bed remaining | Step-down candidate audit trigger |
| **5** | `PHARMACY_DEPLETION` | Critical Drug Stockout | Supply Chain | Antibiotic supply < 3 days buffer | Automated emergency purchase order PO |
| **6** | `LAB_BACKLOG` | Diagnostic Lab TAT Bottleneck | Diagnostics | 28 pending orders with 5 STAT trauma orders | STAT bench re-allocation alert |
| **7** | `HOSPITAL_CAPACITY_CRISIS` | **Flagship Multi-Signal Crisis** | **Compound** | 89% Beds, 94% ICU, 58m OPD, 3 Trauma Cases | **6-Stage Intelligence Pipeline Triggered** |

---

## 2. The 6-Stage Hospital Brain Intelligence Pipeline

When the flagship **Hospital Capacity Crisis** scenario is activated, CAREX executes a 6-stage autonomous orchestration workflow:

1. **Stage 1 — Emergency Telemetry Ingestion**: Captures incoming ambulance vitals (BP, SpO2, HR, GCS) and classifies acuity via supervised ML.
2. **Stage 2 — Bed Capacity & ICU Projection**: Forecasts ICU saturation within 4 hours using length-of-stay survival models.
3. **Stage 3 — OPD Queue Pacing Assessment**: Identifies outpatient delays and predicts doctor consultation bottlenecks.
4. **Stage 4 — Cross-Module Signal Correlation**: The Brain Correlator connects the Emergency surge + Bed saturation + OPD delay into a single compound strain index.
5. **Stage 5 — Hospital Capacity Risk Generation**: Triggers an alert with an Explainable Priority Score (e.g., 94/100) and multi-factor breakdown.
6. **Stage 6 — Closed-Loop Action Protocol**: Dispatches actionable tasks to Hospital Admins, Charge Nurses, and Pharmacy Leads with full audit tracking.

---

## 3. End-to-End Longitudinal Patient Care Journey

CAREX tracks the complete, chronological care trajectory across 10 hospital touchpoints:

1. **Master Patient Index Registration**: Unique Medical Record Number (MRN) generation and demographic verification.
2. **Consultation Scheduling**: Doctor roster matching with time-slot optimization.
3. **OPD Token Queue**: Real-time queue ticketing with ML wait-time forecasting.
4. **Emergency Triage Intake**: Vital signs capture and CDSS severity scoring.
5. **Doctor Clinical Examination**: SOAP consultation notes with automated ICD-10 suggestions.
6. **Diagnostic Laboratory Orders**: Specimen tracking from sample collection to pathologist verification.
7. **Electronic Prescriptions**: Automated drug-interaction and formulary validation.
8. **Pharmacy Dispensing**: Real-time batch-level inventory deduction.
9. **Inpatient Ward & Bed Allocation**: Intelligent bed turnover prediction.
10. **Billing & Settlement**: Multi-source invoice itemization and payment reconciliation.

---

## 4. Technical Specifications & Architecture

### Backend Stack
- **Framework**: FastAPI (Python 3.13)
- **Database ORM**: SQLAlchemy 2.0 with SQLite / PostgreSQL compatibility
- **Security**: JWT OAuth2 authentication with 8 granular Role-Based Access Control (RBAC) tiers
- **Automated Test Suite**: 54 comprehensive Pytest tests covering Auth, Clinical Workflows, Support Services, AI Engines, Hospital Brain, and Demo Scenarios (100% Pass Rate).

### Frontend Stack
- **Framework**: React 19 + TypeScript + Vite
- **Styling**: Modern CSS3 Design System with dark mode glassmorphism and Lucide icons
- **State & Data**: TanStack React Query + Axios with interceptors
- **Build Quality**: Verified zero-error production build (`tsc && vite build`).

---

## 5. Clinical Safety & Regulatory Disclosures

- **Non-Diagnostic Policy**: CAREX is an operational intelligence and clinical decision support system (CDSS). It does not autonomously prescribe, diagnose, or replace certified clinical practitioners.
- **Explainability (XAI)**: Every operational prediction discloses contributing factors, model provider types (Trained ML, Statistical Model, Rule-Based), confidence metrics, and human-in-the-loop safety disclaimers.
- **Audit Logging**: All scenario activations, clinical overrides, triage assessments, and alert resolutions are immutably logged with timestamp, user ID, IP address, and role.

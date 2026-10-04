# CAREX — AI-Powered Hospital Information & Intelligent Coordination Platform

![CAREX Status](https://img.shields.io/badge/System_Status-100%25_Complete_(Phases_1--7)-10b981?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React_19-TypeScript-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-54%2F54_Passed-success?style=for-the-badge&logo=pytest&logoColor=white)

**CAREX** is an enterprise-grade Hospital Operating System and Clinical Information Platform. It combines core hospital operations with an autonomous **Hospital Brain** intelligence layer, cross-module clinical correlation, AI-assisted decision support (CDSS), dynamic what-if capacity simulations, and a 10-touchpoint longitudinal patient care journey.

> 📖 **Comprehensive Documentation**: For full architecture diagrams, sequence flowcharts, database schemas, and AI algorithm details, see the **[CAREX Master System Documentation & Flow Guide](file:///c:/Users/Dharani%20N/OneDrive/Desktop/f8/CAREX/docs/CAREX_MASTER_DOCUMENTATION.md)**.

---

## 🏥 Complete System Capabilities (Phases 1–7)

### 🧠 Flagship Hospital Brain & Central Intelligence (Phases 5 & 6)
- **Central Intelligence Command Center** (`/hospital-brain`): Real-time priority assessment, active clinical correlations, multi-signal strain alerts, and closed-loop action center.
- **Cross-Module Correlation Engine**: Synthesizes simultaneous strain across OPD, Emergency, Inpatient Wards, Diagnostics, and Pharmacy into actionable high-level events (e.g., `HOSPITAL_CAPACITY_RISK`).
- **0–100 Operational Priority Scoring**: Auditable weighted scoring formula combining Severity (30%), Resource Impact (25%), Correlation Density (25%), and Persistence (20%).
- **Transparent Explainability ("Why?" Modal)**: Inspect contributing factors, baseline vs. strained telemetry, affected clinical units, and recommended protocols.
- **What-If Capacity Simulation Engine**: In-memory modeling of emergency inflow surges (+20%), ICU occupancy stress (+10%), OPD surges (+30%), and discharge acceleration without mutating database state.
- **8 AI Clinical Decision Support Modules**:
  1. ⏱️ **OPD Queue Wait-Time Forecast** (Gradient Boosted ML / 95% CI)
  2. 🛏️ **Bed Capacity Horizon & LOS Risk** (Statistical Survival Model)
  3. 💊 **Pharmacy Stockout & Depletion Engine** (Moving Average Velocity)
  4. 🚨 **Emergency Triage CDSS** (Supervised ESI Classifier with Feature Weights)
  5. 📄 **Medical Document OCR / BioBERT NER** (Structured Extraction)
  6. 🎙️ **Voice-to-Note EHR / Whisper ASR** (SOAP Consultation Note Generation)
  7. 📋 **Nursing Shift Handover SBAR** (Rule-Based Deterministic Engine)
  8. 🔍 **Operational Flow Anomaly Detector** (Isolation Forest Engine)

---

### 🏥 Core Clinical & Operational Modules (Phases 1–4)
- **Master Patient Index & Records** (`/patients`): Demographic intake, MRN generation, blood type, allergies, and complete medical histories.
- **10-Touchpoint Patient Journey** (`/patients/:id/journey`): Longitudinal timeline tracing patient progression from registration, appointment, OPD token, ER triage, consultation note, lab order, prescription, dispensing, bed allocation, to itemized billing.
- **OPD Queue & Token Engine** (`/opd-queue`, `/appointments`): Real-time token issuance, department queuing, calling system, and appointment scheduling.
- **Emergency & Trauma Center** (`/emergency`): Level 1–5 triage intake, real-time vitals monitoring, STAT admission triggers, and CDSS scoring.
- **Inpatient Care & Bed Census** (`/ipd`, `/beds`): Ward/room/bed allocation, occupancy heatmap, bed transfers, admission tracking, and discharge summaries.
- **Diagnostic Pathology Laboratory** (`/lab`): STAT/Routine test ordering, specimen accessioning, reference ranges, critical value flagging, and lab report verification.
- **Pharmacy & Inventory Management** (`/pharmacy`, `/prescriptions`): e-Prescription validation, stock alerts, batch expiry tracking, and dispensing audit log.
- **Billing & Revenue Settlement** (`/billing`): Itemized invoices, automated service charging, payment tracking, and receipt generation.

---

### 🎯 SIH 2026 Interactive Demonstration Center (Phase 7)
- **Deterministic Scenario Simulator** (`/admin/demo`): 7 preset operational states (Stable Baseline, OPD Surge, Acute Trauma Inflow, ICU Saturation, Antibiotic Stockout, Lab Backlog, and Flagship Multi-Signal Capacity Crisis).
- **Zero-Side-Effect Demo Reset**: Instantly clears injected simulation alerts (`8801–8899`) while preserving genuine hospital database records.
- **Innovation & Technical Claim Matrix** (`/admin/innovation`): Clear model provider categorization (*Trained ML*, *Statistical Model*, *Rule-Based Engine*, *Simulation Fallback*) with clinical CDSS safety disclaimers.

---

## 🔑 Demo User Credentials

All demo accounts use the standard password: `Carex#2026`

| Persona / Role | Email | Password | Primary Workspace View |
|---|---|---|---|
| 👑 **Super Admin** | `superadmin@carex.health` | `Carex#2026` | Full System Governance & Command Center |
| 🏢 **Hospital Admin** | `admin@carex.health` | `Carex#2026` | Hospital Command Center & Operations |
| 🩺 **Doctor / Attending** | `dr.sharma@carex.health` | `Carex#2026` | Inpatient Care, OPD Queue & e-Rx |
| 💉 **Registered Nurse** | `nurse.sarah@carex.health` | `Carex#2026` | Ward 4B Station, Vitals & MAR |
| 🎫 **Receptionist** | `reception@carex.health` | `Carex#2026` | Front Desk, Token Queue & Intake |
| 💊 **Pharmacist** | `pharmacy@carex.health` | `Carex#2026` | Pharmacy Dispensing & Stock Alerts |
| 🔬 **Lab Technician** | `lab@carex.health` | `Carex#2026` | Pathology Analyzers & STAT Orders |
| 🧑‍⚕️ **Patient** | `patient.john@carex.health` | `Carex#2026` | Personal Health Records Portal |

---

## 🚀 Quick Start Guide

### Option 1: Run with Docker Compose (Recommended)

```bash
docker-compose up --build
```

- **Frontend App**: [http://localhost:3000](http://localhost:3000) or [http://localhost](http://localhost)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

### Option 2: Run Locally

#### 1. Start the Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
# source venv/bin/activate    # On Linux/macOS

pip install -r requirements.txt
alembic upgrade head
python -m app.utils.seed

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*Backend Swagger Docs will be available at [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)*

#### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```
*Frontend will open at [http://localhost:5173](http://localhost:5173)*

---

## 🧪 Testing & Verification

### Run Backend Unit & Integration Tests

```bash
cd backend
.\venv\Scripts\pytest tests/ -v
```

**Result: 54 / 54 tests passing (100% pass rate)** covering authentication, RBAC, clinical flows, acute care, support services, AI intelligence, Hospital Brain, and demo scenario lifecycles.

### Run Frontend Build & Type Check

```bash
cd frontend
npm run build
```

**Result: 0 build errors, 0 TypeScript errors.**

---

## 📂 Project Architecture

```
CAREX/
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── ai/               # AI models (Queue, Bed, Pharmacy, Triage, Brain, Correlator, Scorer, Sim)
│   │   ├── api/v1/endpoints/ # 22 REST endpoint routers
│   │   ├── core/             # Auth, JWT, RBAC guards, logging, config
│   │   ├── db/               # SQLAlchemy ORM session & declarative Base
│   │   ├── demo/             # SIH Demo scenarios & patient journey service
│   │   ├── models/           # 20 SQLAlchemy database models
│   │   ├── schemas/          # Pydantic validation & response schemas
│   │   ├── services/         # Business logic services
│   │   └── utils/seed.py     # Master database seeder
│   ├── tests/                # 54 Pytest unit & integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # UI library, layout, brain modals, dashboard widgets
│   │   ├── context/          # AuthContext, ToastContext
│   │   ├── hooks/            # Custom React hooks
│   │   ├── pages/            # 30 Clinical, Administrative, and AI pages
│   │   ├── routes/           # AppRoutes with RBAC ProtectedRoute wrapper
│   │   ├── services/api.ts   # Axios client with JWT interceptor
│   │   └── types/            # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docs/                     # Comprehensive architecture, AI, database, & audit reports
├── docker-compose.yml        # Multi-container production stack
└── README.md
```

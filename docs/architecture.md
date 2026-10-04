# CAREX — System Architecture (Phase 1: Foundation)

This document provides a comprehensive technical overview of the **CAREX Healthcare Information System** architecture established during Phase 1.

---

## 1. System Overview & Principles

CAREX is designed as a high-reliability, modular healthcare operating system built with:
- **Clean Architecture & Decoupled Layers**: Separation between API presentation, domain services, database models, and future AI subsystems.
- **Enterprise Role-Based Access Control (RBAC)**: Fine-grained permissions for 8 clinical and administrative roles.
- **HIPAA-Compliant Audit Trails**: Structured audit logs capturing all clinical authentication, modification, and access events.
- **Modern Clinical Aesthetics**: High-contrast, dark/glassmorphic interface tailored for low fatigue in clinical stations and command centers.

```
┌─────────────────────────────────────────────────────────────┐
│                    CAREX UI (React + Vite)                  │
│  - Hospital Command Center   - Clinical Station Workspaces  │
│  - Recharts KPI Telemetry    - 1-Click Role Simulator       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / JSON (JWT Bearer)
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Service                  │
│  - CORS & Timing Middleware  - Pydantic v2 Request Guards   │
│  - OAuth2/JWT Security       - Role Dependency Injectors    │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐┌──────────────▼───────────────┐
│     SQLAlchemy ORM Layer    ││  AI Intelligence Subsystems  │
│ - users, roles, departments ││ (CDS, Triage, Transcription) │
│ - audit_logs (HIPAA Trail)  ││       [Future Phase 2]       │
└──────────────┬──────────────┘└──────────────────────────────┘
               │
┌──────────────▼──────────────┐
│    PostgreSQL / SQLite      │
│  - Foreign Key Constraints  │
│  - Indexed Query Paths      │
└─────────────────────────────┘
```

---

## 2. Backend Layer Breakdown

### 2.1 Core Subsystems (`app/core/`)
- `config.py`: Central `Settings` class powered by `pydantic-settings`. Loads environment variables from `.env` or system environment.
- `security.py`: Direct `bcrypt` password hashing with auto-generated salts and `python-jose` HS256 JWT generation and validation.
- `deps.py`: Dependency injection providers for:
  - `get_db`: Yields transaction-isolated SQLAlchemy sessions.
  - `get_current_user`: Decodes Bearer tokens and loads active user identity.
  - `require_roles(*roles)`: Higher-order dependency enforcing RBAC policies.
- `logging.py`: Structured console logging for access times, audit trails, and errors.

### 2.2 Domain Services (`app/services/`)
- `auth_service.py`: User credential verification, JWT token issuance, and login audit logging.
- `user_service.py`: User CRUD, role assignments, password encryption.
- `dashboard_service.py`: Aggregates the 8 core command center KPIs, weekly admission trend analysis, department bed census, and role workspace datasets.
- `audit_service.py`: Writes structured compliance audit entries (`action`, `entity`, `entity_id`, `details`, `ip_address`).

### 2.3 API Endpoints (`app/api/v1/`)
- `/api/v1/auth/login` (POST): JWT authentication.
- `/api/v1/auth/me` (GET): Authenticated user profile and permissions.
- `/api/v1/auth/logout` (POST): Session termination & audit log.
- `/api/v1/users/` (GET, POST, PUT): Staff user management (Admin only).
- `/api/v1/roles/` (GET): System role definitions and permission sets.
- `/api/v1/departments/` (GET, POST): Clinical departments.
- `/api/v1/dashboard/admin` (GET): Real-time Command Center telemetry (Admins only).
- `/api/v1/dashboard/role/{role_name}` (GET): Role-tailored workspace data.
- `/api/v1/health/` (GET): System uptime & database connection health.

---

## 3. RBAC Permission Matrix

| Role | Scope & Description | Permissions |
|---|---|---|
| `SUPER_ADMIN` | Global IT & Multi-Tenant Authority | `["*"]` (Global bypass) |
| `HOSPITAL_ADMIN` | Hospital Operations, Bed & Staff Census | `hospital:read`, `hospital:write`, `users:read`, `users:write`, `departments:read`, `departments:write`, `dashboard:admin`, `audit:read` |
| `DOCTOR` | Attending Physician & Inpatient Care | `patients:read`, `patients:write`, `encounters:read`, `encounters:write`, `prescriptions:write`, `labs:order`, `vitals:read`, `dashboard:doctor` |
| `NURSE` | Inpatient Vitals, e-MAR, Shift Handover | `patients:read`, `vitals:write`, `medications:administer`, `triage:read`, `triage:write`, `dashboard:nurse` |
| `RECEPTIONIST` | Patient Intake, OPD Tokens, Booking | `patients:register`, `appointments:read`, `appointments:write`, `queue:manage`, `dashboard:receptionist` |
| `PHARMACIST` | Drug Dispensing & Inventory Alerts | `prescriptions:dispense`, `inventory:read`, `inventory:write`, `dashboard:pharmacist` |
| `LAB_TECHNICIAN` | Diagnostic Testing & Result Entry | `labs:accession`, `labs:report`, `labs:validate`, `dashboard:lab_technician` |
| `PATIENT` | Personal Health Records & Portals | `patient_portal:read`, `appointments:book`, `prescriptions:view`, `reports:view`, `dashboard:patient` |

---

## 4. Frontend Design System & Architecture

- **Theme & Color Strategy**: Dark slate slate-950 foundation with glowing cyan (`#0ea5e9`), clinical teal (`#0d9488`), emerald (`#10b981`), amber (`#f59e0b`), and rose emergency alerts (`#f43f5e`).
- **State Management**:
  - `AuthContext`: Holds active JWT token, user profile, and permission checkers.
  - `ToastContext`: Global reactive toast notifications with auto-dismiss.
  - `TanStack Query`: Server state caching, auto-polling (every 30s for Command Center), and stale-time management.
- **Routing & Guards**:
  - `ProtectedRoute`: Verifies authentication and role eligibility before rendering components. Redirects unauthenticated requests to `/login` and unauthorized roles to `/unauthorized`.

---

## 5. Extensibility for Future Phases

- **Phase 2 (Clinical Care & OPD/IPD)**: The `departments` and `users` models directly link into future `patients`, `encounters`, `beds`, `prescriptions`, and `lab_orders` tables without restructuring.
- **Phase 3 (AI Intelligence & Clinical Copilot)**: The `app/ai/` module provides clean entry points to plug in LLM-based clinical decision support, triage risk scoring, and clinical documentation transcription.

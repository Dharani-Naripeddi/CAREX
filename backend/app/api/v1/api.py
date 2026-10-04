from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    roles,
    departments,
    patients,
    doctors,
    nurses,
    appointments,
    tokens,
    emergency,
    ipd,
    beds,
    resources,
    lab,
    pharmacy,
    billing,
    notifications,
    ai,
    hospital_brain,
    demo,
    dashboard,
    health,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles & RBAC"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patient Management"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctor Management"])
api_router.include_router(nurses.router, prefix="/nurses", tags=["Nurse Management"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointment Management"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["OPD Token Queue System"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["Emergency & Triage"])
api_router.include_router(ipd.router, prefix="/ipd", tags=["Inpatient (IPD) Admissions"])
api_router.include_router(beds.router, prefix="/beds", tags=["Bed & Ward Management"])
api_router.include_router(resources.router, prefix="/resources", tags=["Resource Coordination"])
api_router.include_router(lab.router, prefix="/lab", tags=["Laboratory Management"])
api_router.include_router(pharmacy.router, prefix="/pharmacy", tags=["Pharmacy & Therapeutics"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing & Revenue Management"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications System"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Intelligence Layer"])
api_router.include_router(hospital_brain.router, prefix="/hospital-brain", tags=["Hospital Brain Core"])
api_router.include_router(demo.router, prefix="/demo", tags=["SIH Demo Center"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard & Command Center"])
api_router.include_router(health.router, prefix="/health", tags=["System Health"])

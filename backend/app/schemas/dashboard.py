from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class KPIItem(BaseModel):
    id: str
    title: str
    value: str
    numeric_value: float
    change_percentage: float
    is_positive: bool
    status: str  # "normal", "warning", "critical", "info"
    subtext: str
    icon_name: str


class TrendPoint(BaseModel):
    time: str
    opd_admissions: int
    emergency_cases: int
    discharges: int


class DepartmentOccupancy(BaseModel):
    department: str
    occupied_beds: int
    total_beds: int
    occupancy_rate: float
    status: str


class TriagePatient(BaseModel):
    id: str
    patient_name: str
    age: int
    gender: str
    chief_complaint: str
    priority: str  # "P1_CRITICAL", "P2_URGENT", "P3_NON_URGENT"
    wait_time_minutes: int
    assigned_doctor: Optional[str] = None
    department: str


class RecentActivity(BaseModel):
    id: int
    timestamp: str
    user_name: str
    role: str
    action: str
    details: str
    category: str  # "ADMISSION", "PRESCRIPTION", "LAB", "DISCHARGE", "SYSTEM"


class AdminDashboardStats(BaseModel):
    hospital_name: str
    last_updated: str
    kpis: List[KPIItem]
    weekly_trends: List[TrendPoint]
    department_occupancy: List[DepartmentOccupancy]
    triage_queue: List[TriagePatient]
    recent_activities: List[RecentActivity]


class RoleDashboardData(BaseModel):
    role: str
    title: str
    description: str
    stats: List[KPIItem]
    quick_actions: List[Dict[str, Any]]
    recent_records: List[Dict[str, Any]]

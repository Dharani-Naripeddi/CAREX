import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.role import RoleEnum
from app.models.ai import AIAlert, AIAlertSeverity, AIAlertStatus
from app.models.bed import Bed, BedStatus
from app.models.ward import Ward
from app.models.emergency_case import EmergencyCase, EmergencyCaseStatus, TriageLevel
from app.models.opd_token import OpdToken, TokenStatus
from app.models.lab import LabOrder, LabOrderStatus, LabOrderPriority
from app.models.audit_log import AuditLog
from app.ai.brain.priority_scorer import OperationalPriorityScorer
from app.ai.brain.correlator import HospitalBrainCorrelator
from app.ai.brain.schemas import AIRiskLevel, WhatIfSimulationRequest
from app.ai.brain.simulation import HospitalBrainSimulationEngine


def get_token_for(client: TestClient, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_priority_scorer_calculation():
    """Test transparent 0-100 Operational Priority Scoring and factor contributions."""
    priority = OperationalPriorityScorer.calculate_score(
        severity=AIAlertSeverity.CRITICAL,
        risk_level=AIRiskLevel.CRITICAL,
        correlated_sources_count=3,
        is_composite=True,
        is_critical_resource=True,
        hours_active=2.0,
    )

    assert priority.score >= 80
    assert priority.rating == "CRITICAL"
    assert len(priority.factors) == 4
    assert any(f.name == "Alert Severity" for f in priority.factors)
    assert any(f.name == "Cross-Module Correlation" for f in priority.factors)


def test_cross_module_correlation_engine():
    """Test correlation engine triggers composite HOSPITAL_CAPACITY_RISK on simultaneous signals."""
    opd_data = {"estimated_wait_minutes": 55, "predicted_delay_minutes": 35, "waiting_count": 12}
    bed_data = {"occupancy_percent": 88.0, "icu_occupancy_percent": 92.0, "available_beds": 5}
    emergency_data = {"active_count": 6, "red_cases_count": 2, "orange_cases_count": 3, "is_surge": True}
    pharmacy_data = {"critical_count": 2, "high_count": 4}
    lab_data = {"pending_count": 18, "stat_pending_count": 4}

    composite_events = HospitalBrainCorrelator.evaluate_correlations(
        opd_data=opd_data,
        bed_data=bed_data,
        emergency_data=emergency_data,
        pharmacy_data=pharmacy_data,
        lab_data=lab_data,
    )

    assert len(composite_events) >= 2
    event_types = [e.event_type.value for e in composite_events]
    assert "HOSPITAL_CAPACITY_RISK" in event_types
    assert "BED_CAPACITY_RISK" in event_types

    cap_event = next(e for e in composite_events if e.event_type.value == "HOSPITAL_CAPACITY_RISK")
    assert cap_event.is_composite_correlation is True
    assert "Emergency" in cap_event.explanation.affected_departments
    assert "Inpatient Wards" in cap_event.explanation.affected_departments
    assert cap_event.priority.score >= 80


def test_what_if_simulation_engine():
    """Test What-If simulation projections for capacity and queue surge."""
    baseline = {
        "bed_occupancy_percent": 75.0,
        "icu_occupancy_percent": 70.0,
        "opd_wait_minutes": 25.0,
        "active_emergency_count": 4.0,
    }
    req = WhatIfSimulationRequest(
        emergency_arrival_delta_pct=30.0,
        icu_occupancy_delta_pct=15.0,
        opd_demand_delta_pct=40.0,
        ward_discharge_rate_delta_pct=-20.0,
    )

    sim = HospitalBrainSimulationEngine.execute_simulation(req, baseline)

    assert sim.simulation_label.startswith("SIMULATION")
    assert "hospital_bed_occupancy" in sim.impacts
    assert "icu_occupancy" in sim.impacts
    assert "opd_wait_time" in sim.impacts
    assert sim.impacts["hospital_bed_occupancy"].simulated_value > baseline["bed_occupancy_percent"]
    assert sim.impacts["opd_wait_time"].simulated_value > baseline["opd_wait_minutes"]
    assert len(sim.recommended_preemptive_actions) > 0


def test_hospital_brain_overview_api(client: TestClient, db: Session):
    """Test GET /api/v1/hospital-brain/overview returns complete KPIs and live events."""
    admin_token = get_token_for(client, "admin@carex.health")
    response = client.get(
        "/api/v1/hospital-brain/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "hospital_status" in data
    assert "kpis" in data
    assert "active_events" in data
    assert "department_matrix" in data
    assert "top_recommended_actions" in data

    kpis = data["kpis"]
    assert "hospital_capacity_percent" in kpis
    assert "opd_predicted_wait_minutes" in kpis
    assert "available_beds_count" in kpis


def test_hospital_brain_events_and_details_api(client: TestClient, db: Session):
    """Test listing events and fetching detailed explainability view."""
    admin_token = get_token_for(client, "admin@carex.health")

    # Seed an alert
    alert = AIAlert(
        id=7701,
        alert_type="OPD_DELAY",
        severity=AIAlertSeverity.HIGH,
        title="Cardiology OPD Queue Delay",
        description="Consultation delay exceeds 40 mins",
        reason=["Elongated consultation time"],
        recommended_action="Open overflow consultation room",
        related_entity="OPD",
        status=AIAlertStatus.ACTIVE,
    )
    db.merge(alert)
    db.commit()

    # List events
    response = client.get(
        "/api/v1/hospital-brain/events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) > 0

    # Get details
    event_id = events[0]["id"]
    det_resp = client.get(
        f"/api/v1/hospital-brain/events/{event_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert det_resp.status_code == 200
    event_det = det_resp.json()
    assert "explanation" in event_det
    assert "what_is_happening" in event_det["explanation"]
    assert "why_flagged" in event_det["explanation"]
    assert "recommended_operational_review" in event_det["explanation"]


def test_hospital_brain_acknowledge_and_resolve_lifecycle(client: TestClient, db: Session):
    """Test acknowledging and resolving events with automatic audit trail recording."""
    admin_token = get_token_for(client, "admin@carex.health")

    alert = AIAlert(
        id=7702,
        alert_type="PHARMACY_DEPLETION",
        severity=AIAlertSeverity.WARNING,
        title="Antibiotic Safety Stock Warning",
        description="Azithromycin 500mg down to 3 days supply",
        reason=["High inpatient consumption"],
        recommended_action="Issue PO-PHARM-2026-099",
        related_entity="PHARMACY",
        status=AIAlertStatus.ACTIVE,
    )
    db.merge(alert)
    db.commit()

    # 1. Acknowledge
    ack_resp = client.post(
        f"/api/v1/hospital-brain/events/{alert.id}/acknowledge",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "ACKNOWLEDGED"

    # Verify audit log
    audit_ack = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "HOSPITAL_BRAIN_ACKNOWLEDGE",
            AuditLog.entity_id == str(alert.id),
        )
        .first()
    )
    assert audit_ack is not None

    # 2. Resolve
    res_resp = client.post(
        f"/api/v1/hospital-brain/events/{alert.id}/resolve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"

    # Verify audit log
    audit_res = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "HOSPITAL_BRAIN_RESOLVE",
            AuditLog.entity_id == str(alert.id),
        )
        .first()
    )
    assert audit_res is not None


def test_hospital_brain_departments_and_capacity_api(client: TestClient, db: Session):
    """Test department operational matrix and capacity matrix APIs."""
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    # Departments
    dept_resp = client.get(
        "/api/v1/hospital-brain/departments",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert dept_resp.status_code == 200
    depts = dept_resp.json()
    assert len(depts) >= 5
    dept_names = [d["department_name"] for d in depts]
    assert any("Emergency" in name for name in dept_names)
    assert any("ICU" in name for name in dept_names)

    # Capacity
    cap_resp = client.get(
        "/api/v1/hospital-brain/capacity",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert cap_resp.status_code == 200
    cap = cap_resp.json()
    assert "total_beds" in cap
    assert "icu_occupancy_percent" in cap
    assert "wards" in cap


def test_hospital_brain_simulation_api(client: TestClient, db: Session):
    """Test What-If simulation execution endpoint and audit logging."""
    admin_token = get_token_for(client, "admin@carex.health")

    payload = {
        "emergency_arrival_delta_pct": 25.0,
        "icu_occupancy_delta_pct": 10.0,
        "opd_demand_delta_pct": 30.0,
        "ward_discharge_rate_delta_pct": 0.0,
    }
    response = client.post(
        "/api/v1/hospital-brain/simulation",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    sim_data = response.json()

    assert "SIMULATION" in sim_data["simulation_label"]
    assert "impacts" in sim_data
    assert "recommended_preemptive_actions" in sim_data

    # Verify simulation audit log entry
    sim_audit = (
        db.query(AuditLog)
        .filter(AuditLog.action == "HOSPITAL_BRAIN_SIMULATION")
        .order_by(desc(AuditLog.id))
        .first()
    )
    assert sim_audit is not None
    assert sim_audit.entity == "WHAT_IF_SCENARIO"

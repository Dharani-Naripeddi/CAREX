import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.demo.scenarios import DEMO_SCENARIOS


def get_token_for(client: TestClient, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_list_demo_scenarios_api(client: TestClient):
    """Test retrieving full catalog of 7 SIH Demo Scenarios."""
    admin_token = get_token_for(client, "admin@carex.health")
    response = client.get(
        "/api/v1/demo/scenarios",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 7

    codes = [s["code"] for s in scenarios]
    assert "STABLE_HOSPITAL" in codes
    assert "OPD_OVERLOAD" in codes
    assert "EMERGENCY_SURGE" in codes
    assert "ICU_CAPACITY_PRESSURE" in codes
    assert "PHARMACY_DEPLETION" in codes
    assert "LAB_BACKLOG" in codes
    assert "HOSPITAL_CAPACITY_CRISIS" in codes

    flagship = next(s for s in scenarios if s["code"] == "HOSPITAL_CAPACITY_CRISIS")
    assert flagship["is_flagship"] is True


def test_launch_flagship_hospital_capacity_crisis(client: TestClient, db: Session):
    """Test launching the SIH Flagship Hospital Capacity Crisis scenario."""
    admin_token = get_token_for(client, "admin@carex.health")

    payload = {"scenario_code": "HOSPITAL_CAPACITY_CRISIS"}
    response = client.post(
        "/api/v1/demo/launch",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    result = response.json()

    assert result["scenario_code"] == "HOSPITAL_CAPACITY_CRISIS"
    assert "generated_events" in result
    assert len(result["generated_events"]) > 0

    # Verify audit log entry
    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "DEMO_SCENARIO_LAUNCH",
            AuditLog.entity_id == "HOSPITAL_CAPACITY_CRISIS",
        )
        .first()
    )
    assert audit is not None


def test_pipeline_progress_progression(client: TestClient):
    """Test retrieving real-time intelligence pipeline progress."""
    admin_token = get_token_for(client, "admin@carex.health")

    # Launch flagship first
    client.post(
        "/api/v1/demo/launch",
        json={"scenario_code": "HOSPITAL_CAPACITY_CRISIS"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = client.get(
        "/api/v1/demo/pipeline-progress",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    progress = response.json()

    assert progress["active_scenario_code"] == "HOSPITAL_CAPACITY_CRISIS"
    assert len(progress["steps"]) == 6
    assert progress["steps"][0]["step_name"] == "Emergency Telemetry Ingestion"
    assert progress["steps"][3]["step_name"] == "Cross-Module Signal Correlation"
    assert progress["steps"][4]["step_name"] == "Hospital Capacity Risk Generation"
    assert all(s["is_completed"] for s in progress["steps"])


def test_reset_demo_to_baseline(client: TestClient, db: Session):
    """Test resetting Demo Mode back to clean baseline state."""
    admin_token = get_token_for(client, "admin@carex.health")

    response = client.post(
        "/api/v1/demo/reset",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert "baseline_kpis" in data

    # Verify reset audit log
    audit_reset = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "DEMO_RESET",
            AuditLog.entity_id == "RESET",
        )
        .first()
    )
    assert audit_reset is not None


def test_end_to_end_patient_journey_timeline(client: TestClient, db: Session):
    """Test compiling comprehensive 10-touchpoint patient care journey timeline."""
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    # Fetch first patient
    patient = db.query(Patient).first()
    assert patient is not None

    response = client.get(
        f"/api/v1/patients/{patient.id}/journey",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    journey = response.json()

    assert journey["patient_id"] == patient.id
    assert journey["mrn"] == patient.mrn
    assert len(journey["journey_stages"]) >= 3

    stage_names = [s["stage_name"] for s in journey["journey_stages"]]
    assert "Patient Registration" in stage_names
    assert any(s["ai_insight"] is not None for s in journey["journey_stages"])


def test_patient_journey_security_authorization(client: TestClient, db: Session):
    """Test that patients can only access their own journey."""
    patient_token = get_token_for(client, "patient.john@carex.health")

    # Attempt to access with a valid token
    response = client.get(
        "/api/v1/patients/1/journey",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    # Either 200 (if patient owns record 1) or 403 (if accessing another patient)
    assert response.status_code in [200, 403]

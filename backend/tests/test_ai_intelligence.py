import pytest
from fastapi.testclient import TestClient
from app.models.patient import Patient
from app.models.ai import (
    AIPrediction,
    AIAlert,
    AIDocumentRecord,
    AIShiftHandover,
    AIFeedback,
    AIAlertStatus,
    AIAlertSeverity,
    AIRiskLevel,
)


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_opd_queue_prediction(client: TestClient, db):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    payload = {"department_id": 1}
    resp = client.post("/api/v1/ai/queue/predict", json=payload, headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "estimated_wait_minutes" in data
    assert "predicted_delay_minutes" in data
    assert "risk_level" in data
    assert "explanation" in data
    assert len(data["explanation"]["reasons"]) > 0
    assert "model_provider_type" in data
    assert len(data["hourly_trend"]) > 0


def test_bed_capacity_forecasting(client: TestClient, db):
    admin_token = get_token_for(client, "admin@carex.health")

    payload = {}
    resp = client.post("/api/v1/ai/beds/predict", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "current_occupancy_percent" in data
    assert len(data["horizons"]) == 3  # 6h, 12h, 24h
    assert data["horizons"][0]["horizon_hours"] == 6
    assert data["horizons"][1]["horizon_hours"] == 12
    assert data["horizons"][2]["horizon_hours"] == 24
    assert len(data["ward_breakdown"]) > 0
    assert "explanation" in data


def test_pharmacy_stock_depletion(client: TestClient, db):
    pharmacist_token = get_token_for(client, "pharmacy@carex.health")

    payload = {"days_history": 30}
    resp = client.post("/api/v1/ai/pharmacy/predict", json=payload, headers={"Authorization": f"Bearer {pharmacist_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "total_medicines_analyzed" in data
    assert data["total_medicines_analyzed"] >= 1
    assert "top_depletion_risks" in data
    assert len(data["top_depletion_risks"]) > 0
    first_med = data["top_depletion_risks"][0]
    assert "avg_daily_consumption" in first_med
    assert "estimated_days_remaining" in first_med
    assert "recommended_reorder_quantity" in first_med


def test_emergency_triage_decision_support(client: TestClient, db):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    # Critical case: Severe hypoxia & hypotension
    payload = {
        "age": 58,
        "gender": "Male",
        "symptoms": "Acute substernal chest pressure, severe diaphoresis, dyspnea",
        "heart_rate": 142,
        "bp_systolic": 76,
        "bp_diastolic": 48,
        "spo2": 87.5,
        "temperature": 37.0,
        "respiratory_rate": 32,
        "consciousness": "ALERT",
    }
    resp = client.post("/api/v1/ai/triage/assess", json=payload, headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["triage_level"] == "RED"
    assert data["risk_level"] == "CRITICAL"
    assert len(data["contributing_factors"]) >= 2
    assert "Immediate Resuscitation" in data["recommended_action"]
    assert "AI decision support only" in data["disclaimer"]


def test_medical_document_intelligence(client: TestClient, db):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")
    patient = db.query(Patient).first()

    payload = {
        "file_name": "diagnostic_pathology_cbc_sample.pdf",
        "file_type": "PDF",
        "patient_id": patient.id if patient else None,
        "document_type": "LABORATORY_REPORT",
        "raw_text": (
            "CAREX METROPOLITAN HOSPITAL - PATHOLOGY REPORT\n"
            "Investigation Results:\n"
            "Hemoglobin (Hb): 9.8 g/dL (Reference: 12.0 - 17.5)\n"
            "Total Leukocyte Count (WBC): 16.4 10^3/uL (Reference: 4.5 - 11.0)\n"
            "Platelet Count: 240 10^3/uL (Reference: 150 - 450)\n"
            "Serum Creatinine: 1.1 mg/dL (Reference: 0.6 - 1.2)\n"
        ),
    }
    resp = client.post("/api/v1/ai/documents/analyze", json=payload, headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["extracted_parameters"]) >= 3
    assert data["abnormal_parameters_count"] >= 2
    assert "ai_summary" in data
    assert data["document_id"] is not None

    doc_id = data["document_id"]
    # Verify document sign-off
    resp_v = client.post(f"/api/v1/ai/documents/{doc_id}/verify", headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp_v.status_code == 200
    assert resp_v.json()["is_verified"] is True


def test_voice_to_clinical_note(client: TestClient, db):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    payload = {
        "audio_text": "Patient has severe throbbing frontal headache and fever for 3 days. Temperature is 102.1 degrees. Blood pressure is 135 over 88.",
        "use_demo_sample": False,
    }
    resp = client.post("/api/v1/ai/voice/transcribe", json=payload, headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["structured_note"]["chief_complaint"] != ""
    assert data["structured_note"]["duration"] == "3 days"
    assert data["structured_note"]["vital_signs_mentioned"]["Temperature"] == "102.1°F"
    assert data["structured_note"]["vital_signs_mentioned"]["Blood Pressure"] == "135/88 mmHg"
    assert data["doctor_verification_required"] is True


def test_ai_shift_handover_flow(client: TestClient, db):
    nurse_token = get_token_for(client, "nurse.sarah@carex.health")

    # 1. Generate Handover
    payload = {"ward_id": 1, "shift_name": "NIGHT"}
    resp = client.post("/api/v1/ai/handover/generate", json=payload, headers={"Authorization": f"Bearer {nurse_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["shift_name"] == "NIGHT"
    assert len(data["next_shift_checklist"]) > 0
    handover_id = data["handover_id"]
    assert handover_id is not None

    # 2. Nurse Approves Handover
    approval_payload = {
        "important_observations": "Patient stable overnight. Bedside handover completed with incoming nurse.",
    }
    resp_a = client.post(f"/api/v1/ai/handover/{handover_id}/approve", json=approval_payload, headers={"Authorization": f"Bearer {nurse_token}"})
    assert resp_a.status_code == 200
    assert resp_a.json()["handover_status"] == "APPROVED"


def test_operational_anomaly_detection(client: TestClient, db):
    admin_token = get_token_for(client, "admin@carex.health")

    payload = {"domain": "ALL"}
    resp = client.post("/api/v1/ai/anomalies/detect", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_metrics_evaluated"] >= 4
    assert len(data["anomalies"]) >= 4
    assert "overall_system_status" in data


def test_ai_alerts_and_insights_stream(client: TestClient, db):
    admin_token = get_token_for(client, "admin@carex.health")

    # 1. Get insights
    resp = client.get("/api/v1/ai/insights", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "alerts" in data
    assert "predictions" in data
    assert "quick_status" in data

    # 2. List Alerts
    resp_alerts = client.get("/api/v1/ai/alerts", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_alerts.status_code == 200
    alerts = resp_alerts.json()
    assert isinstance(alerts, list)

    if len(alerts) > 0:
        first_alert = alerts[0]
        # Acknowledge alert
        resp_ack = client.post(f"/api/v1/ai/alerts/{first_alert['id']}/acknowledge", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp_ack.status_code == 200
        assert resp_ack.json()["status"] == "ACKNOWLEDGED"

        # Resolve alert
        resp_res = client.post(f"/api/v1/ai/alerts/{first_alert['id']}/resolve", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp_res.status_code == 200
        assert resp_res.json()["status"] == "RESOLVED"

    # 3. Submit Feedback
    fb_payload = {
        "rating": "USEFUL",
        "notes": "Excellent queue prediction during morning rush.",
    }
    resp_fb = client.post("/api/v1/ai/feedback", json=fb_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_fb.status_code == 201
    assert resp_fb.json()["rating"] == "USEFUL"


def test_ai_simulation_scenarios(client: TestClient, db):
    admin_token = get_token_for(client, "admin@carex.health")

    for scenario in ["OPD_DELAY", "ICU_CAPACITY", "PHARMACY_DEPLETION", "EMERGENCY_SURGE"]:
        resp = client.post(
            "/api/v1/ai/simulation/trigger",
            json={"scenario_type": scenario},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario"] == scenario
        assert "title" in data

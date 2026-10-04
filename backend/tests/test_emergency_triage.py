from fastapi import status


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_emergency_registration_critical_red_triage(client):
    receptionist_token = get_token_for(client, "reception@carex.health")

    # Severe case: SpO2 88%, HR 146 bpm, Systolic BP 78 mmHg
    case_payload = {
        "patient_name": "Marcus Vance",
        "age": 62,
        "gender": "Male",
        "symptoms": "Severe crushing substernal chest pain, diaphoresis, cyanotic lips",
        "injury_type": "Suspected Acute STEMI / Cardiogenic Shock",
        "heart_rate": 146,
        "bp_systolic": 78,
        "bp_diastolic": 48,
        "spo2": 88.0,
        "temperature": 37.1,
        "respiratory_rate": 34,
        "consciousness": "ALERT",
    }

    res = client.post(
        "/api/v1/emergency/",
        json=case_payload,
        headers={"Authorization": f"Bearer {receptionist_token}"},
    )

    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["case_number"].startswith("EMR-")
    assert data["triage_level"] == "RED"
    assert len(data["contributing_factors"]) >= 2
    assert "AI decision support only" in data["disclaimer"]
    assert "Resuscitation Bay" in data["recommended_action"] or "Trauma" in data["recommended_action"]


def test_emergency_registration_non_urgent_green_triage(client):
    receptionist_token = get_token_for(client, "reception@carex.health")

    # Stable case: SpO2 99%, HR 74 bpm, BP 120/80
    case_payload = {
        "patient_name": "Sarah Miller",
        "age": 28,
        "gender": "Female",
        "symptoms": "Mild wrist sprain after slipping on pavement, minimal swelling",
        "injury_type": "Minor Wrist Sprain",
        "heart_rate": 74,
        "bp_systolic": 120,
        "bp_diastolic": 80,
        "spo2": 99.0,
        "temperature": 36.8,
        "respiratory_rate": 16,
        "consciousness": "ALERT",
    }

    res = client.post(
        "/api/v1/emergency/",
        json=case_payload,
        headers={"Authorization": f"Bearer {receptionist_token}"},
    )

    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["triage_level"] == "GREEN"
    assert "FastTrack" in data["recommended_action"] or "Outpatient" in data["recommended_action"]


def test_emergency_vitals_update_recalculates_triage(client):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    # List cases
    cases_res = client.get("/api/v1/emergency/", headers={"Authorization": f"Bearer {doctor_token}"})
    assert len(cases_res.json()) > 0
    case_id = cases_res.json()[0]["id"]

    # Deteriorate vitals: SpO2 drops to 87%
    update_res = client.put(
        f"/api/v1/emergency/{case_id}",
        json={
            "spo2": 87.0,
            "heart_rate": 150,
            "consciousness": "VOICE",
            "triage_notes": "Patient condition acutely deteriorated, oxygen desaturation.",
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )

    assert update_res.status_code == status.HTTP_200_OK
    updated = update_res.json()
    assert updated["triage_level"] == "RED"
    assert any("SpO2" in f for f in updated["contributing_factors"])

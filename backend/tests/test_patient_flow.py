import datetime
from fastapi import status


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_receptionist_can_register_patient(client):
    receptionist_token = get_token_for(client, "reception@carex.health")

    patient_payload = {
        "first_name": "Eleanor",
        "last_name": "Vance",
        "email": "eleanor.vance@example.com",
        "phone": "+1-555-9011",
        "date_of_birth": "1994-06-18",
        "gender": "Female",
        "blood_group": "A+",
        "address": "404 Northridge Drive, Boston, MA",
        "emergency_contact_name": "Thomas Vance",
        "emergency_contact_phone": "+1-555-9012",
        "emergency_contact_relation": "Father",
        "allergies": ["Penicillin", "Sulfa"],
        "current_medications": ["Cetirizine 10mg OD"],
        "medical_history": ["Seasonal Allergic Rhinitis"],
    }

    response = client.post(
        "/api/v1/patients/",
        json=patient_payload,
        headers={"Authorization": f"Bearer {receptionist_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["mrn"].startswith("CRX-")
    assert data["first_name"] == "Eleanor"
    assert data["last_name"] == "Vance"
    assert "Penicillin" in data["allergies"]


def test_search_patients(client):
    admin_token = get_token_for(client, "admin@carex.health")

    # Search by seeded patient
    response = client.get(
        "/api/v1/patients/?query=Johnathan",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    patients = response.json()
    assert len(patients) >= 1
    assert any("Johnathan" in p["first_name"] for p in patients)


def test_update_patient_allergies_and_history(client):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    # Fetch patient
    search_res = client.get(
        "/api/v1/patients/?query=Johnathan",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    patient_id = search_res.json()[0]["id"]

    # Update allergies
    update_res = client.put(
        f"/api/v1/patients/{patient_id}",
        json={
            "allergies": ["Penicillin", "Sulfa Drugs", "Aspirin"],
            "current_medications": ["Atorvastatin 40mg OD", "Ticagrelor 90mg BD"],
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )

    assert update_res.status_code == status.HTTP_200_OK
    updated = update_res.json()
    assert "Aspirin" in updated["allergies"]
    assert "Ticagrelor 90mg BD" in updated["current_medications"]

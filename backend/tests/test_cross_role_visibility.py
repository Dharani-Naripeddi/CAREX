from fastapi import status


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_cross_role_patient_visibility(client):
    receptionist_token = get_token_for(client, "reception@carex.health")
    doctor_token = get_token_for(client, "dr.sharma@carex.health")
    nurse_token = get_token_for(client, "nurse.sarah@carex.health")
    admin_token = get_token_for(client, "admin@carex.health")

    # 1. Receptionist creates a new patient
    new_patient_payload = {
        "first_name": "Marcus",
        "last_name": "Aurelius",
        "phone": "+1-555-7788",
        "date_of_birth": "1975-04-26",
        "gender": "Male",
        "blood_group": "AB+",
        "allergies": ["Latex", "Codeine"],
        "current_medications": ["Amlodipine 5mg OD"],
        "medical_history": ["Mild Essential Hypertension"],
    }

    create_res = client.post(
        "/api/v1/patients/",
        json=new_patient_payload,
        headers={"Authorization": f"Bearer {receptionist_token}"},
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    created_patient = create_res.json()
    patient_id = created_patient["id"]
    mrn = created_patient["mrn"]

    # 2. Doctor looks up patient by MRN
    doc_lookup_res = client.get(
        f"/api/v1/patients/?query={mrn}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert doc_lookup_res.status_code == status.HTTP_200_OK
    doc_results = doc_lookup_res.json()
    assert len(doc_results) == 1
    assert doc_results[0]["first_name"] == "Marcus"
    assert "Codeine" in doc_results[0]["allergies"]

    # 3. Nurse views patient details
    nurse_view_res = client.get(
        f"/api/v1/patients/{patient_id}",
        headers={"Authorization": f"Bearer {nurse_token}"},
    )
    assert nurse_view_res.status_code == status.HTTP_200_OK
    nurse_pat = nurse_view_res.json()
    assert nurse_pat["blood_group"] == "AB+"
    assert nurse_pat["emergency_contact_phone"] is None or isinstance(nurse_pat["emergency_contact_phone"], (str, type(None)))

    # 4. Admin accesses full patient profile
    admin_view_res = client.get(
        f"/api/v1/patients/{patient_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_view_res.status_code == status.HTTP_200_OK
    assert admin_view_res.json()["first_name"] == "Marcus"

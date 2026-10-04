from fastapi import status


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_ipd_admission_transfer_discharge_lifecycle(client):
    admin_token = get_token_for(client, "admin@carex.health")
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    # 1. Get available bed in ICU or General Ward
    beds_res = client.get("/api/v1/beds/?status=AVAILABLE", headers={"Authorization": f"Bearer {admin_token}"})
    available_beds = beds_res.json()
    assert len(available_beds) >= 2
    bed1 = available_beds[0]
    bed2 = available_beds[1]

    # 2. Get patient and doctor
    pat_res = client.get("/api/v1/patients/", headers={"Authorization": f"Bearer {admin_token}"})
    patient_id = pat_res.json()[0]["id"]

    doc_res = client.get("/api/v1/doctors/", headers={"Authorization": f"Bearer {admin_token}"})
    doctor_user_id = doc_res.json()[0]["user_id"]

    # 3. Admit Patient to Bed 1
    adm_res = client.post(
        "/api/v1/ipd/admissions",
        json={
            "patient_id": patient_id,
            "admitting_doctor_id": doctor_user_id,
            "ward_id": bed1["ward_id"],
            "bed_id": bed1["id"],
            "admission_reason": "Acute exacerbation of chronic cardiac failure",
            "expected_stay_days": 4,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert adm_res.status_code == status.HTTP_201_CREATED
    adm_data = adm_res.json()
    adm_id = adm_data["id"]
    assert adm_data["admission_number"].startswith("ADM-")
    assert adm_data["status"] == "ADMITTED"

    # Verify Bed 1 is now OCCUPIED
    bed1_check = client.get(f"/api/v1/beds/?ward_id={bed1['ward_id']}", headers={"Authorization": f"Bearer {admin_token}"}).json()
    b1_found = next(b for b in bed1_check if b["id"] == bed1["id"])
    assert b1_found["status"] == "OCCUPIED"

    # 4. Transfer Patient from Bed 1 to Bed 2
    transfer_res = client.post(
        f"/api/v1/ipd/admissions/{adm_id}/transfer",
        json={
            "to_bed_id": bed2["id"],
            "transfer_reason": "Patient stabilized; step-down ward transfer",
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert transfer_res.status_code == status.HTTP_200_OK

    # Verify Bed 1 is now CLEANING and Bed 2 is OCCUPIED
    beds_after_trf = client.get("/api/v1/beds/", headers={"Authorization": f"Bearer {admin_token}"}).json()
    b1_after = next(b for b in beds_after_trf if b["id"] == bed1["id"])
    b2_after = next(b for b in beds_after_trf if b["id"] == bed2["id"])
    assert b1_after["status"] == "CLEANING"
    assert b2_after["status"] == "OCCUPIED"

    # 5. Discharge Patient with Comprehensive Discharge Summary
    discharge_res = client.post(
        f"/api/v1/ipd/admissions/{adm_id}/discharge",
        json={
            "discharge_diagnosis": "Compensated Congestive Heart Failure, NYHA Class II",
            "discharge_summary": "Patient responded favorably to IV diuresis. Vitals stable, ambulating well.",
            "discharge_condition": "IMPROVED",
            "discharge_medications": [
                {"name": "Furosemide 40mg", "dosage": "1 tab PO daily in AM", "duration": "30 days"},
                {"name": "Carvedilol 6.25mg", "dosage": "1 tab PO twice daily", "duration": "30 days"},
            ],
            "follow_up_instructions": "Follow up in Cardiology OPD in 2 weeks with repeat electrolyte panel.",
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert discharge_res.status_code == status.HTTP_200_OK
    dis_data = discharge_res.json()
    assert dis_data["status"] == "DISCHARGED"
    assert dis_data["discharge_condition"] == "IMPROVED"
    assert len(dis_data["discharge_medications"]) == 2

    # Verify Bed 2 is freed to CLEANING
    beds_after_dis = client.get("/api/v1/beds/", headers={"Authorization": f"Bearer {admin_token}"}).json()
    b2_freed = next(b for b in beds_after_dis if b["id"] == bed2["id"])
    assert b2_freed["status"] == "CLEANING"

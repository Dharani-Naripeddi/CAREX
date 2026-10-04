from fastapi import status


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_token_generation_and_queue_tracking(client):
    receptionist_token = get_token_for(client, "reception@carex.health")
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    # Fetch patient & department
    pat_res = client.get("/api/v1/patients/", headers={"Authorization": f"Bearer {receptionist_token}"})
    patient_id = pat_res.json()[0]["id"]

    dept_res = client.get("/api/v1/departments/", headers={"Authorization": f"Bearer {receptionist_token}"})
    dept_id = dept_res.json()[0]["id"]

    # 1. Generate OPD Token
    gen_res = client.post(
        "/api/v1/tokens/generate",
        json={
            "patient_id": patient_id,
            "department_id": dept_id,
            "priority": "NORMAL",
        },
        headers={"Authorization": f"Bearer {receptionist_token}"},
    )

    assert gen_res.status_code == status.HTTP_201_CREATED
    tok = gen_res.json()
    token_id = tok["id"]
    assert "token_code" in tok
    assert tok["status"] == "ISSUED"

    # 2. Check live department queue
    queue_res = client.get(
        f"/api/v1/tokens/queue?department_id={dept_id}",
        headers={"Authorization": f"Bearer {receptionist_token}"},
    )
    assert queue_res.status_code == status.HTTP_200_OK
    queue_data = queue_res.json()
    assert queue_data["total_in_queue"] >= 1

    # 3. Check live patient token status
    pat_status_res = client.get(
        f"/api/v1/tokens/patient/{patient_id}/status",
        headers={"Authorization": f"Bearer {receptionist_token}"},
    )
    assert pat_status_res.status_code == status.HTTP_200_OK
    pat_live = pat_status_res.json()
    assert pat_live["has_active_token"] is True
    assert pat_live["token"]["id"] == token_id

    # 4. Doctor calls token
    call_res = client.put(
        f"/api/v1/tokens/{token_id}/call",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert call_res.status_code == status.HTTP_200_OK
    assert call_res.json()["status"] == "CALLED"

    # 5. Complete token
    complete_res = client.put(
        f"/api/v1/tokens/{token_id}/complete",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert complete_res.status_code == status.HTTP_200_OK
    assert complete_res.json()["status"] == "SERVICED"

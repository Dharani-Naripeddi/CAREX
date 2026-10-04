import datetime
from fastapi import status


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_appointment_booking_and_lifecycle(client):
    receptionist_token = get_token_for(client, "reception@carex.health")
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    # 1. Get Doctor & Department IDs
    doc_res = client.get("/api/v1/doctors/", headers={"Authorization": f"Bearer {receptionist_token}"})
    assert len(doc_res.json()) > 0
    doctor_user_id = doc_res.json()[0]["user_id"]
    dept_id = doc_res.json()[0]["department_id"]

    # 2. Get Patient ID
    pat_res = client.get("/api/v1/patients/", headers={"Authorization": f"Bearer {receptionist_token}"})
    patient_id = pat_res.json()[0]["id"]

    # 3. Create Appointment
    today_str = str(datetime.date.today())
    create_res = client.post(
        "/api/v1/appointments/",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_user_id,
            "department_id": dept_id,
            "appointment_date": today_str,
            "appointment_time": "14:30",
            "type": "OPD",
            "chief_complaint": "Acute retrosternal chest discomfort on climbing stairs",
        },
        headers={"Authorization": f"Bearer {receptionist_token}"},
    )

    assert create_res.status_code == status.HTTP_201_CREATED
    appt = create_res.json()
    appt_id = appt["id"]
    assert appt["appointment_number"].startswith("APT-")
    assert appt["status"] == "SCHEDULED"

    # 4. Receptionist checks in patient
    checkin_res = client.put(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "CHECKED_IN"},
        headers={"Authorization": f"Bearer {receptionist_token}"},
    )
    assert checkin_res.status_code == status.HTTP_200_OK
    assert checkin_res.json()["status"] == "CHECKED_IN"

    # 5. Doctor starts consultation
    start_res = client.put(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "IN_CONSULTATION", "notes": "ECG shows normal sinus rhythm, order Troponin I test."},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert start_res.status_code == status.HTTP_200_OK
    assert start_res.json()["status"] == "IN_CONSULTATION"

    # 6. Complete consultation
    complete_res = client.put(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "COMPLETED", "notes": "Prescribed Aspirin 81mg, follow up in 2 weeks."},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert complete_res.status_code == status.HTTP_200_OK
    assert complete_res.json()["status"] == "COMPLETED"


def test_appointment_rescheduling(client):
    receptionist_token = get_token_for(client, "reception@carex.health")

    # Get an active appointment
    appts = client.get("/api/v1/appointments/?status=SCHEDULED", headers={"Authorization": f"Bearer {receptionist_token}"}).json()
    if appts:
        appt_id = appts[0]["id"]
        tomorrow_str = str(datetime.date.today() + datetime.timedelta(days=1))
        resched_res = client.put(
            f"/api/v1/appointments/{appt_id}/reschedule",
            json={
                "appointment_date": tomorrow_str,
                "appointment_time": "15:00",
                "notes": "Patient requested afternoon slot.",
            },
            headers={"Authorization": f"Bearer {receptionist_token}"},
        )
        assert resched_res.status_code == status.HTTP_200_OK
        assert resched_res.json()["appointment_time"] == "15:00"

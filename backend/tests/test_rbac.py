from fastapi import status


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_admin_can_access_command_center(client):
    admin_token = get_token_for(client, "admin@carex.health")
    response = client.get(
        "/api/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "kpis" in data
    assert len(data["kpis"]) == 8


def test_super_admin_can_access_command_center(client):
    super_admin_token = get_token_for(client, "superadmin@carex.health")
    response = client.get(
        "/api/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK


def test_doctor_cannot_access_admin_command_center(client):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")
    response = client.get(
        "/api/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_patient_cannot_access_users_list(client):
    patient_token = get_token_for(client, "patient.john@carex.health")
    response = client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_access_users_list(client):
    admin_token = get_token_for(client, "admin@carex.health")
    response = client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) >= 8


def test_role_dashboard_endpoints(client):
    roles_to_test = ["DOCTOR", "NURSE", "RECEPTIONIST", "PHARMACIST", "LAB_TECHNICIAN", "PATIENT"]
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    for r in roles_to_test:
        response = client.get(
            f"/api/v1/dashboard/role/{r}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == r
        assert len(data["stats"]) > 0

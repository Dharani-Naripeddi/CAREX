from fastapi import status


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_admin_dashboard_reflects_live_database_metrics(client):
    admin_token = get_token_for(client, "admin@carex.health")

    res = client.get("/api/v1/dashboard/admin", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()

    # Verify 8 KPI items are returned with numeric values
    assert len(data["kpis"]) >= 8
    total_pat_kpi = next(k for k in data["kpis"] if k["id"] == "total_patients")
    assert total_pat_kpi["numeric_value"] >= 1

    admissions_kpi = next(k for k in data["kpis"] if k["id"] == "current_admissions")
    assert admissions_kpi["numeric_value"] >= 0

    available_beds_kpi = next(k for k in data["kpis"] if k["id"] == "available_beds")
    assert "/" in available_beds_kpi["value"]

    # Verify Triage Queue is populated with active emergency cases
    assert len(data["triage_queue"]) >= 1
    first_er = data["triage_queue"][0]
    assert first_er["id"].startswith("EMR-")

    # Verify Department Occupancy has real wards
    assert len(data["department_occupancy"]) >= 3

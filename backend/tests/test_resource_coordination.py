from fastapi import status


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_resource_coordination_telemetry(client):
    admin_token = get_token_for(client, "admin@carex.health")

    res = client.get("/api/v1/resources/coordination", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()

    assert "overall_status" in data
    assert len(data["resources"]) >= 5
    assert any(r["resource_type"] == "ICU_BEDS" for r in data["resources"])
    assert any(r["resource_type"] == "DOCTORS" for r in data["resources"])
    assert any(r["resource_type"] == "OXYGEN_SUPPORT" for r in data["resources"])
    assert len(data["operational_recommendations"]) >= 1
    assert "AI decision support only" in data["disclaimer"]

from fastapi import status


def test_health_endpoint(client):
    response = client.get("/api/v1/health/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"


def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@carex.health", "password": "Carex#2026"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "superadmin@carex.health"
    assert data["user"]["role"] == "SUPER_ADMIN"


def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@carex.health", "password": "WrongPassword123"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@carex.health", "password": "Carex#2026"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_authenticated(client):
    # First login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "dr.sharma@carex.health", "password": "Carex#2026"},
    )
    token = login_res.json()["access_token"]

    # Request /auth/me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    user = response.json()
    assert user["email"] == "dr.sharma@carex.health"
    assert user["role"] == "DOCTOR"
    assert "Dr. Rajesh Sharma" in user["full_name"]


def test_get_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_403_FORBIDDEN or response.status_code == status.HTTP_401_UNAUTHORIZED

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "ada@example.com") -> dict:
    response = client.post(
        "/api/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "secret123"},
    )
    return response.json()


def _login(
    client: TestClient, email: str = "ada@example.com", password: str = "secret123"
):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_register_returns_201_without_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert "password" not in body


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    _register(client)

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Grace Hopper",
            "email": "ada@example.com",
            "password": "other-pass",
        },
    )

    assert response.status_code == 409


def test_login_with_correct_credentials_returns_token(client: TestClient) -> None:
    _register(client)

    response = _login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_returns_401(client: TestClient) -> None:
    _register(client)

    response = _login(client, password="wrong-password")

    assert response.status_code == 401


def test_login_with_unknown_email_returns_401(client: TestClient) -> None:
    response = _login(client, email="missing@example.com", password="whatever")

    assert response.status_code == 401


def test_me_with_valid_token_returns_current_teacher(client: TestClient) -> None:
    _register(client)
    token = _login(client).json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "ada@example.com"


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_with_garbage_token_returns_401(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer garbage-token"}
    )

    assert response.status_code == 401

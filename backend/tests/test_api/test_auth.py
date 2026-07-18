from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401 - registers all mapped models on Base.metadata
from database.connection import get_db
from main import app
from models.base import Base


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)
        engine.dispose()


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

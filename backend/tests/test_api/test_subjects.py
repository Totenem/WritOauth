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


def _register_and_login(client: TestClient, email: str, name: str) -> dict:
    client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": "secret123"},
    )
    token = client.post(
        "/api/auth/login",
        json={"email": email, "password": "secret123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _auth_headers(client: TestClient) -> dict:
    return _register_and_login(client, "ada@example.com", "Ada Lovelace")


def test_full_subject_lifecycle(client: TestClient) -> None:
    headers = _auth_headers(client)

    create_response = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers
    )
    assert create_response.status_code == 201
    subject_id = create_response.json()["id"]
    assert create_response.json()["name"] == "Algebra"

    list_response = client.get("/api/subjects", headers=headers)
    assert list_response.status_code == 200
    assert any(s["id"] == subject_id for s in list_response.json())

    get_response = client.get(f"/api/subjects/{subject_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Algebra"

    update_response = client.put(
        f"/api/subjects/{subject_id}",
        json={"name": "Advanced Algebra"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Advanced Algebra"

    get_after_update = client.get(f"/api/subjects/{subject_id}", headers=headers)
    assert get_after_update.json()["name"] == "Advanced Algebra"

    delete_response = client.delete(f"/api/subjects/{subject_id}", headers=headers)
    assert delete_response.status_code == 204

    get_after_delete = client.get(f"/api/subjects/{subject_id}", headers=headers)
    assert get_after_delete.status_code == 404


def test_get_unknown_subject_returns_404(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.get("/api/subjects/999", headers=headers)

    assert response.status_code == 404


def test_update_unknown_subject_returns_404(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.put("/api/subjects/999", json={"name": "Nobody"}, headers=headers)

    assert response.status_code == 404


def test_delete_unknown_subject_returns_404(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.delete("/api/subjects/999", headers=headers)

    assert response.status_code == 404


def test_list_subjects_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/subjects")

    assert response.status_code == 401


def test_create_subject_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/api/subjects", json={"name": "Algebra"})

    assert response.status_code == 401


def test_get_subject_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/subjects/1")

    assert response.status_code == 401


def test_update_subject_without_token_returns_401(client: TestClient) -> None:
    response = client.put("/api/subjects/1", json={"name": "Algebra"})

    assert response.status_code == 401


def test_delete_subject_without_token_returns_401(client: TestClient) -> None:
    response = client.delete("/api/subjects/1")

    assert response.status_code == 401


def test_list_subjects_never_returns_another_teachers_subjects(
    client: TestClient,
) -> None:
    headers_a = _register_and_login(client, "a@example.com", "Teacher A")
    headers_b = _register_and_login(client, "b@example.com", "Teacher B")
    client.post("/api/subjects", json={"name": "Algebra"}, headers=headers_a)
    client.post("/api/subjects", json={"name": "Geometry"}, headers=headers_b)

    response_a = client.get("/api/subjects", headers=headers_a)

    assert response_a.status_code == 200
    assert [s["name"] for s in response_a.json()] == ["Algebra"]


def test_get_another_teachers_subject_returns_404(client: TestClient) -> None:
    headers_a = _register_and_login(client, "a@example.com", "Teacher A")
    headers_b = _register_and_login(client, "b@example.com", "Teacher B")
    subject_id = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers_a
    ).json()["id"]

    response = client.get(f"/api/subjects/{subject_id}", headers=headers_b)

    assert response.status_code == 404


def test_update_another_teachers_subject_returns_404(client: TestClient) -> None:
    headers_a = _register_and_login(client, "a@example.com", "Teacher A")
    headers_b = _register_and_login(client, "b@example.com", "Teacher B")
    subject_id = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers_a
    ).json()["id"]

    response = client.put(
        f"/api/subjects/{subject_id}", json={"name": "Hacked"}, headers=headers_b
    )

    assert response.status_code == 404
    unchanged = client.get(f"/api/subjects/{subject_id}", headers=headers_a)
    assert unchanged.json()["name"] == "Algebra"


def test_delete_another_teachers_subject_returns_404(client: TestClient) -> None:
    headers_a = _register_and_login(client, "a@example.com", "Teacher A")
    headers_b = _register_and_login(client, "b@example.com", "Teacher B")
    subject_id = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers_a
    ).json()["id"]

    response = client.delete(f"/api/subjects/{subject_id}", headers=headers_b)

    assert response.status_code == 404
    still_there = client.get(f"/api/subjects/{subject_id}", headers=headers_a)
    assert still_there.status_code == 200

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
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

    # SQLite ignores FK constraints unless a connection opts in; MySQL
    # (used in production) enforces them by default.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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


def _auth_headers(client: TestClient) -> dict:
    client.post(
        "/api/auth/register",
        json={
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "secret123",
        },
    )
    token = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "secret123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_student_and_subject(client: TestClient, headers: dict) -> tuple[int, int]:
    student_id = client.post(
        "/api/students", json={"name": "Grace Hopper"}, headers=headers
    ).json()["id"]
    subject_id = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers
    ).json()["id"]
    return student_id, subject_id


def test_upload_baseline_then_get_returns_baseline_type(client: TestClient) -> None:
    headers = _auth_headers(client)
    student_id, subject_id = _make_student_and_subject(client, headers)

    upload_response = client.post(
        "/api/papers/baseline",
        json={"student_id": student_id, "subject_id": subject_id, "content": "essay"},
        headers=headers,
    )
    assert upload_response.status_code == 201
    paper_id = upload_response.json()["id"]

    get_response = client.get(f"/api/papers/{paper_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["type"] == "baseline"


def test_upload_submission_then_get_returns_submission_type(client: TestClient) -> None:
    headers = _auth_headers(client)
    student_id, subject_id = _make_student_and_subject(client, headers)

    upload_response = client.post(
        "/api/papers/analyze",
        json={"student_id": student_id, "subject_id": subject_id, "content": "essay"},
        headers=headers,
    )
    assert upload_response.status_code == 201
    paper_id = upload_response.json()["id"]

    get_response = client.get(f"/api/papers/{paper_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["type"] == "submission"


def test_upload_baseline_with_unknown_student_returns_4xx(client: TestClient) -> None:
    headers = _auth_headers(client)
    _, subject_id = _make_student_and_subject(client, headers)

    response = client.post(
        "/api/papers/baseline",
        json={"student_id": 999, "subject_id": subject_id, "content": "essay"},
        headers=headers,
    )

    assert 400 <= response.status_code < 500


def test_upload_submission_with_unknown_subject_returns_4xx(client: TestClient) -> None:
    headers = _auth_headers(client)
    student_id, _ = _make_student_and_subject(client, headers)

    response = client.post(
        "/api/papers/analyze",
        json={"student_id": student_id, "subject_id": 999, "content": "essay"},
        headers=headers,
    )

    assert 400 <= response.status_code < 500


def test_get_unknown_paper_returns_404(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.get("/api/papers/999", headers=headers)

    assert response.status_code == 404


def test_upload_baseline_without_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/papers/baseline",
        json={"student_id": 1, "subject_id": 1, "content": "essay"},
    )

    assert response.status_code == 401


def test_upload_analysis_without_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/papers/analyze",
        json={"student_id": 1, "subject_id": 1, "content": "essay"},
    )

    assert response.status_code == 401


def test_get_paper_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/papers/1")

    assert response.status_code == 401

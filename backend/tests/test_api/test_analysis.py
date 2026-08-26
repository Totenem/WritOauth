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

    # SQLite ignores FK constraints unless a connection opts in; prod
    # (Postgres) enforces them by default.
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


def _create_analysis(client: TestClient, headers: dict) -> int:
    student_id, subject_id = _make_student_and_subject(client, headers)
    client.post(
        "/api/papers/baseline",
        json={
            "student_id": student_id,
            "subject_id": subject_id,
            "content": "The cat sat calmly on the warm mat.",
        },
        headers=headers,
    )
    submission = client.post(
        "/api/papers/analyze",
        json={
            "student_id": student_id,
            "subject_id": subject_id,
            "content": "The cat sat calmly on the warm mat.",
        },
        headers=headers,
    )
    analysis_id = submission.json()["analysis_id"]
    assert analysis_id is not None
    return analysis_id


def test_upload_for_analysis_without_baseline_has_null_analysis_id(
    client: TestClient,
) -> None:
    headers = _auth_headers(client)
    student_id, subject_id = _make_student_and_subject(client, headers)

    response = client.post(
        "/api/papers/analyze",
        json={"student_id": student_id, "subject_id": subject_id, "content": "essay"},
        headers=headers,
    )

    assert response.json()["analysis_id"] is None


def test_get_analysis_returns_score_breakdown_and_explanation(
    client: TestClient,
) -> None:
    headers = _auth_headers(client)
    analysis_id = _create_analysis(client, headers)

    response = client.get(f"/api/analysis/{analysis_id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == analysis_id
    assert 0 <= body["consistency_score"] <= 100
    assert set(body["breakdown"].keys()) == {
        "vocabulary",
        "sentence_structure",
        "grammar",
        "readability",
        "style",
    }
    assert isinstance(body["explanation"], str) and body["explanation"]


def test_get_unknown_analysis_returns_404(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.get("/api/analysis/999", headers=headers)

    assert response.status_code == 404


def test_get_analysis_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/analysis/1")

    assert response.status_code == 401


def test_submit_feedback_creates_feedback(client: TestClient) -> None:
    headers = _auth_headers(client)
    analysis_id = _create_analysis(client, headers)

    response = client.post(
        f"/api/analysis/{analysis_id}/feedback",
        json={"decision": "genuine", "remarks": "looks fine"},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["decision"] == "genuine"
    assert body["remarks"] == "looks fine"


def test_submit_feedback_twice_overwrites_previous_decision(
    client: TestClient,
) -> None:
    headers = _auth_headers(client)
    analysis_id = _create_analysis(client, headers)
    client.post(
        f"/api/analysis/{analysis_id}/feedback",
        json={"decision": "genuine"},
        headers=headers,
    )

    response = client.post(
        f"/api/analysis/{analysis_id}/feedback",
        json={"decision": "flagged", "remarks": "reconsidered"},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["decision"] == "flagged"


def test_submit_feedback_for_unknown_analysis_returns_404(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.post(
        "/api/analysis/999/feedback", json={"decision": "genuine"}, headers=headers
    )

    assert response.status_code == 404


def test_submit_feedback_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/api/analysis/1/feedback", json={"decision": "genuine"})

    assert response.status_code == 401

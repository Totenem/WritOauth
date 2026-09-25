from fastapi.testclient import TestClient

from tests.helpers import api_student, api_subject


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
    subject_id = api_subject(client, headers, "Algebra")
    student_id = api_student(client, headers, "Grace Hopper", subject_id)
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
    assert set(body["breakdown"]["profiles"]) == {
        "lexical",
        "syntactic",
        "grammatical",
        "mechanical",
        "stylistic",
        "discourse",
    }
    # The verdict is computed server-side, so the client never has to infer
    # one by comparing a score against a threshold itself.
    assert isinstance(body["flagged"], bool)
    assert body["breakdown"]["flagged"] == body["flagged"]
    assert body["breakdown"]["reliability"]["n_baseline_papers"] >= 1
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

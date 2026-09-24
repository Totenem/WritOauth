from fastapi.testclient import TestClient


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

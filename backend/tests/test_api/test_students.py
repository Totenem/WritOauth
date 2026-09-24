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


def test_full_student_lifecycle(client: TestClient) -> None:
    headers = _auth_headers(client)

    create_response = client.post(
        "/api/students", json={"name": "Grace Hopper"}, headers=headers
    )
    assert create_response.status_code == 201
    student_id = create_response.json()["id"]
    assert create_response.json()["name"] == "Grace Hopper"

    list_response = client.get("/api/students", headers=headers)
    assert list_response.status_code == 200
    assert any(s["id"] == student_id for s in list_response.json())

    get_response = client.get(f"/api/students/{student_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Grace Hopper"

    update_response = client.put(
        f"/api/students/{student_id}",
        json={"name": "Grace B. Hopper"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Grace B. Hopper"

    get_after_update = client.get(f"/api/students/{student_id}", headers=headers)
    assert get_after_update.json()["name"] == "Grace B. Hopper"

    delete_response = client.delete(f"/api/students/{student_id}", headers=headers)
    assert delete_response.status_code == 204

    get_after_delete = client.get(f"/api/students/{student_id}", headers=headers)
    assert get_after_delete.status_code == 404


def test_get_unknown_student_returns_404(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.get("/api/students/999", headers=headers)

    assert response.status_code == 404


def test_update_unknown_student_returns_404(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.put("/api/students/999", json={"name": "Nobody"}, headers=headers)

    assert response.status_code == 404


def test_delete_unknown_student_returns_404(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.delete("/api/students/999", headers=headers)

    assert response.status_code == 404


def test_list_students_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/students")

    assert response.status_code == 401


def test_create_student_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/api/students", json={"name": "Grace Hopper"})

    assert response.status_code == 401


def test_get_student_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/students/1")

    assert response.status_code == 401


def test_update_student_without_token_returns_401(client: TestClient) -> None:
    response = client.put("/api/students/1", json={"name": "Grace Hopper"})

    assert response.status_code == 401


def test_delete_student_without_token_returns_401(client: TestClient) -> None:
    response = client.delete("/api/students/1")

    assert response.status_code == 401

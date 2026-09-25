from fastapi.testclient import TestClient


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


def _template(code: str, *rows: str) -> bytes:
    header = "Subject Code,Last Name,First Name,Email,Status"
    return "\n".join([header, *(f"{code},{row}" for row in rows)]).encode()


def test_created_subject_has_a_course_code_and_empty_roster(client: TestClient) -> None:
    headers = _auth_headers(client)

    body = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers
    ).json()

    assert body["course_code"].startswith("ALGEBR-")
    assert body["student_count"] == 0
    roster = client.get(f"/api/subjects/{body['id']}/roster", headers=headers)
    assert roster.status_code == 200
    assert roster.json()["students"] == []


def test_batch_upload_enrolls_students_and_reports_skips(client: TestClient) -> None:
    headers = _auth_headers(client)
    subject = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers
    ).json()

    response = client.post(
        f"/api/subjects/{subject['id']}/students/batch",
        files={
            "file": (
                "roster.csv",
                _template(
                    subject["course_code"],
                    "Hopper,Grace,g@x.org,active",
                    ",Ada,,active",
                ),
                "text/csv",
            )
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["created_count"] == 1
    assert response.json()["skipped"][0]["row"] == 3

    listed = client.get("/api/subjects", headers=headers).json()[0]
    assert listed["student_count"] == 1
    students = client.get("/api/students", headers=headers).json()
    assert [(s["name"], s["subjects"][0]["id"]) for s in students] == [
        ("Grace Hopper", subject["id"])
    ]


def test_batch_upload_rejects_non_csv_files(client: TestClient) -> None:
    headers = _auth_headers(client)
    subject_id = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers
    ).json()["id"]

    response = client.post(
        f"/api/subjects/{subject_id}/students/batch",
        files={"file": ("roster.xlsx", b"not a csv", "application/octet-stream")},
        headers=headers,
    )

    assert response.status_code == 400


def test_batch_upload_rejects_a_file_missing_template_columns(
    client: TestClient,
) -> None:
    headers = _auth_headers(client)
    subject_id = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers
    ).json()["id"]

    response = client.post(
        f"/api/subjects/{subject_id}/students/batch",
        files={"file": ("roster.csv", b"name\nGrace Hopper\n", "text/csv")},
        headers=headers,
    )

    assert response.status_code == 400
    assert "Missing column" in response.json()["detail"]


def test_roster_and_batch_upload_are_404_for_another_teacher(
    client: TestClient,
) -> None:
    owner = _auth_headers(client)
    intruder = _register_and_login(client, "bob@example.com", "Bob Barker")
    subject = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=owner
    ).json()

    roster = client.get(f"/api/subjects/{subject['id']}/roster", headers=intruder)
    upload = client.post(
        f"/api/subjects/{subject['id']}/students/batch",
        files={
            "file": (
                "r.csv",
                _template(subject["course_code"], "Hopper,Grace,,active"),
                "text/csv",
            )
        },
        headers=intruder,
    )

    assert roster.status_code == 404
    assert upload.status_code == 404
    assert (
        client.get(f"/api/subjects/{subject['id']}/roster", headers=owner).json()[
            "students"
        ]
        == []
    )

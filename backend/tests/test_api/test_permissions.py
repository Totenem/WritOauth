"""Cross-tenant authorization tests.

Every test here registers two unrelated teachers and asserts that one cannot
reach the other's data. They mirror the idiom already used in
`test_subjects.py`, which was the only resource with ownership enforcement.

Cross-owner access is expected to return 404 rather than 403, matching the
convention in `api/subjects.py`: a teacher must not be able to learn that
another teacher's record even exists.
"""

from collections.abc import Callable

from fastapi.testclient import TestClient


def _make_student_and_subject(
    client: TestClient, headers: dict, name: str = "Grace Hopper"
) -> tuple[int, int]:
    student_id = client.post(
        "/api/students", json={"name": name}, headers=headers
    ).json()["id"]
    subject_id = client.post(
        "/api/subjects", json={"name": "Algebra"}, headers=headers
    ).json()["id"]
    return student_id, subject_id


def _analysis_id_with_baseline(
    client: TestClient, headers: dict, student_id: int, subject_id: int
) -> int:
    """Upload a baseline then a submission, returning the analysis id.

    A submission only produces an analysis when the student already has a
    baseline profile - `AIOrchestrator.analyze_submission` returns None
    otherwise.
    """
    client.post(
        "/api/papers/baseline",
        json={
            "student_id": student_id,
            "subject_id": subject_id,
            "content": "The quick brown fox jumps over the lazy dog. A fine day.",
        },
        headers=headers,
    )
    response = client.post(
        "/api/papers/analyze",
        json={
            "student_id": student_id,
            "subject_id": subject_id,
            "content": "A wholly different sentence, written later in the term.",
        },
        headers=headers,
    )
    analysis_id = response.json()["analysis_id"]
    assert analysis_id is not None, "expected an analysis once a baseline exists"
    return int(analysis_id)


# --------------------------------------------------------------------------
# Students
# --------------------------------------------------------------------------


def test_list_students_excludes_another_teachers_students(
    client: TestClient, auth_headers: dict, other_headers: dict
) -> None:
    client.post("/api/students", json={"name": "Grace Hopper"}, headers=auth_headers)

    response = client.get("/api/students", headers=other_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_get_another_teachers_student_returns_404(
    client: TestClient, auth_headers: dict, other_headers: dict
) -> None:
    student_id = client.post(
        "/api/students", json={"name": "Grace Hopper"}, headers=auth_headers
    ).json()["id"]

    assert (
        client.get(f"/api/students/{student_id}", headers=other_headers).status_code
        == 404
    )
    # ...and the real owner is unaffected.
    assert (
        client.get(f"/api/students/{student_id}", headers=auth_headers).status_code
        == 200
    )


def test_update_another_teachers_student_returns_404(
    client: TestClient, auth_headers: dict, other_headers: dict
) -> None:
    student_id = client.post(
        "/api/students", json={"name": "Grace Hopper"}, headers=auth_headers
    ).json()["id"]

    response = client.put(
        f"/api/students/{student_id}", json={"name": "Hacked"}, headers=other_headers
    )

    assert response.status_code == 404
    owner_view = client.get(f"/api/students/{student_id}", headers=auth_headers)
    assert owner_view.json()["name"] == "Grace Hopper"


def test_delete_another_teachers_student_returns_404(
    client: TestClient, auth_headers: dict, other_headers: dict
) -> None:
    """The highest-severity leak: papers.student_id is ON DELETE CASCADE, so a
    cross-tenant delete would destroy the owner's papers and analyses too."""
    student_id, subject_id = _make_student_and_subject(client, auth_headers)
    client.post(
        "/api/papers/baseline",
        json={"student_id": student_id, "subject_id": subject_id, "content": "essay"},
        headers=auth_headers,
    )

    response = client.delete(f"/api/students/{student_id}", headers=other_headers)

    assert response.status_code == 404
    assert (
        client.get(f"/api/students/{student_id}", headers=auth_headers).status_code
        == 200
    )


# --------------------------------------------------------------------------
# Papers
# --------------------------------------------------------------------------


def test_upload_baseline_into_another_teachers_subject_is_rejected(
    client: TestClient,
    auth_headers: dict,
    other_headers: dict,
) -> None:
    _, owner_subject_id = _make_student_and_subject(client, auth_headers)
    intruder_student_id = client.post(
        "/api/students", json={"name": "Intruder Student"}, headers=other_headers
    ).json()["id"]

    response = client.post(
        "/api/papers/baseline",
        json={
            "student_id": intruder_student_id,
            "subject_id": owner_subject_id,
            "content": "essay",
        },
        headers=other_headers,
    )

    assert response.status_code == 404


def test_upload_baseline_for_another_teachers_student_is_rejected(
    client: TestClient, auth_headers: dict, other_headers: dict
) -> None:
    owner_student_id, _ = _make_student_and_subject(client, auth_headers)
    intruder_subject_id = client.post(
        "/api/subjects", json={"name": "Physics"}, headers=other_headers
    ).json()["id"]

    response = client.post(
        "/api/papers/baseline",
        json={
            "student_id": owner_student_id,
            "subject_id": intruder_subject_id,
            "content": "essay",
        },
        headers=other_headers,
    )

    assert response.status_code == 404


def test_upload_for_analysis_into_another_teachers_subject_is_rejected(
    client: TestClient, auth_headers: dict, other_headers: dict
) -> None:
    _, owner_subject_id = _make_student_and_subject(client, auth_headers)
    intruder_student_id = client.post(
        "/api/students", json={"name": "Intruder Student"}, headers=other_headers
    ).json()["id"]

    response = client.post(
        "/api/papers/analyze",
        json={
            "student_id": intruder_student_id,
            "subject_id": owner_subject_id,
            "content": "essay",
        },
        headers=other_headers,
    )

    assert response.status_code == 404


def test_get_another_teachers_paper_returns_404(
    client: TestClient, auth_headers: dict, other_headers: dict
) -> None:
    student_id, subject_id = _make_student_and_subject(client, auth_headers)
    paper_id = client.post(
        "/api/papers/baseline",
        json={"student_id": student_id, "subject_id": subject_id, "content": "essay"},
        headers=auth_headers,
    ).json()["id"]

    assert (
        client.get(f"/api/papers/{paper_id}", headers=other_headers).status_code == 404
    )
    assert (
        client.get(f"/api/papers/{paper_id}", headers=auth_headers).status_code == 200
    )


# --------------------------------------------------------------------------
# Analysis + feedback
# --------------------------------------------------------------------------


def test_get_another_teachers_analysis_returns_404(
    client: TestClient, auth_headers: dict, other_headers: dict
) -> None:
    """The most sensitive payload in the system: scores, breakdown and the
    natural-language explanation about another teacher's student."""
    student_id, subject_id = _make_student_and_subject(client, auth_headers)
    analysis_id = _analysis_id_with_baseline(
        client, auth_headers, student_id, subject_id
    )

    assert (
        client.get(f"/api/analysis/{analysis_id}", headers=other_headers).status_code
        == 404
    )
    assert (
        client.get(f"/api/analysis/{analysis_id}", headers=auth_headers).status_code
        == 200
    )


def test_feedback_on_another_teachers_analysis_returns_404_and_preserves_decision(
    client: TestClient, auth_headers: dict, other_headers: dict
) -> None:
    """`save_feedback` is an upsert, so an unguarded write silently overwrites
    the real teacher's recorded decision."""
    student_id, subject_id = _make_student_and_subject(client, auth_headers)
    analysis_id = _analysis_id_with_baseline(
        client, auth_headers, student_id, subject_id
    )
    client.post(
        f"/api/analysis/{analysis_id}/feedback",
        json={"decision": "genuine", "remarks": "Consistent with her earlier work."},
        headers=auth_headers,
    )

    response = client.post(
        f"/api/analysis/{analysis_id}/feedback",
        json={"decision": "flagged", "remarks": "Overwritten by an intruder."},
        headers=other_headers,
    )

    assert response.status_code == 404
    # The owner's decision must survive untouched.
    owner_feedback = client.post(
        f"/api/analysis/{analysis_id}/feedback",
        json={"decision": "genuine", "remarks": "Consistent with her earlier work."},
        headers=auth_headers,
    )
    assert owner_feedback.json()["decision"] == "genuine"
    assert owner_feedback.json()["remarks"] == "Consistent with her earlier work."


def test_unknown_ids_still_return_404_for_the_owner(
    client: TestClient, auth_headers: dict
) -> None:
    """Ownership checks must not turn a genuine not-found into a 500."""
    assert client.get("/api/students/999", headers=auth_headers).status_code == 404
    assert client.get("/api/papers/999", headers=auth_headers).status_code == 404
    assert client.get("/api/analysis/999", headers=auth_headers).status_code == 404


def test_second_teacher_sees_their_own_students(
    client: TestClient,
    register_and_login: Callable[..., dict],
) -> None:
    """Scoping must filter, not simply return nothing."""
    headers_a = register_and_login(email="a@example.com", name="Teacher A")
    headers_b = register_and_login(email="b@example.com", name="Teacher B")
    client.post("/api/students", json={"name": "Student A"}, headers=headers_a)
    client.post("/api/students", json={"name": "Student B"}, headers=headers_b)

    names_b = [s["name"] for s in client.get("/api/students", headers=headers_b).json()]
    names_a = [s["name"] for s in client.get("/api/students", headers=headers_a).json()]

    assert names_b == ["Student B"]
    assert names_a == ["Student A"]

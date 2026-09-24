"""Dashboard statistics.

Two things are being checked here beyond "the numbers add up": that every
aggregate is scoped to the signed-in teacher, and that a submission which
never produced an analysis is not counted as one.
"""

from collections.abc import Callable

from fastapi.testclient import TestClient

_ESSAY = (
    "Although the committee deliberated at length regarding the proposal, "
    "several members expressed reservations. However, it is clear that one "
    "of the most significant obstacles remains unresolved. Consequently the "
    "chair recommended a further review before any decision could be taken."
)
_DIFFERENT = (
    "I don't get it. It's weird. They keep changing stuff and nobody says "
    "why. That's annoying. My mate reckons it's about cash. Maybe he's right."
)


def _roster(client: TestClient, headers: dict, name: str = "Grace Hopper"):
    student_id = client.post(
        "/api/students", json={"name": name}, headers=headers
    ).json()["id"]
    subject_id = client.post(
        "/api/subjects", json={"name": "English"}, headers=headers
    ).json()["id"]
    return student_id, subject_id


def _upload(
    client: TestClient, headers: dict, path: str, sid: int, subid: int, text: str
):
    return client.post(
        path,
        json={"student_id": sid, "subject_id": subid, "content": text},
        headers=headers,
    ).json()


def _stats(client: TestClient, headers: dict) -> dict:
    response = client.get("/api/dashboard/stats", headers=headers)
    assert response.status_code == 200
    return response.json()


def test_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/dashboard/stats").status_code == 401


def test_new_teacher_gets_a_valid_empty_payload(
    client: TestClient, auth_headers: dict
) -> None:
    """This is the page a teacher lands on immediately after signing up, so
    the all-zero case is the first thing a real user ever sees."""
    body = _stats(client, auth_headers)

    assert body["counts"] == {
        "students": 0,
        "subjects": 0,
        "baseline_papers": 0,
        "submissions": 0,
        "analyses": 0,
    }
    assert body["students_needing_attention"] == []
    assert body["recent_activity"] == []
    assert sum(bucket["count"] for bucket in body["score_distribution"]) == 0


def test_counts_reflect_the_roster(client: TestClient, auth_headers: dict) -> None:
    sid, subid = _roster(client, auth_headers)
    _upload(client, auth_headers, "/api/papers/baseline", sid, subid, _ESSAY)
    _upload(client, auth_headers, "/api/papers/analyze", sid, subid, _ESSAY)

    counts = _stats(client, auth_headers)["counts"]

    assert counts["students"] == 1
    assert counts["subjects"] == 1
    assert counts["baseline_papers"] == 1
    assert counts["submissions"] == 1


def test_submission_without_a_baseline_is_not_counted_as_analysed(
    client: TestClient, auth_headers: dict
) -> None:
    """Papers of type `submission` and analysis rows are not 1:1 - counting
    papers would silently overstate how much has been checked."""
    sid, subid = _roster(client, auth_headers)
    _upload(client, auth_headers, "/api/papers/analyze", sid, subid, _ESSAY)

    counts = _stats(client, auth_headers)["counts"]

    assert counts["submissions"] == 1
    assert counts["analyses"] == 0


def test_baseline_readiness_separates_the_three_states(
    client: TestClient, auth_headers: dict
) -> None:
    ready_id, subid = _roster(client, auth_headers, name="Ready")
    partial_id = client.post(
        "/api/students", json={"name": "Partial"}, headers=auth_headers
    ).json()["id"]
    client.post("/api/students", json={"name": "None yet"}, headers=auth_headers)

    for _ in range(3):
        _upload(client, auth_headers, "/api/papers/baseline", ready_id, subid, _ESSAY)
    _upload(client, auth_headers, "/api/papers/baseline", partial_id, subid, _ESSAY)

    readiness = _stats(client, auth_headers)["baseline_readiness"]

    assert readiness == {"ready": 1, "no_baseline": 1, "needs_more_samples": 1}


def test_verdicts_keep_ai_and_teacher_judgements_separate(
    client: TestClient, auth_headers: dict
) -> None:
    """They answer different questions and must not be merged into one
    'flagged' number."""
    sid, subid = _roster(client, auth_headers)
    _upload(client, auth_headers, "/api/papers/baseline", sid, subid, _ESSAY)
    analysis_id = _upload(
        client, auth_headers, "/api/papers/analyze", sid, subid, _DIFFERENT
    )["analysis_id"]

    before = _stats(client, auth_headers)["verdicts"]
    assert before["awaiting_review"] == 1
    assert before["teacher_flagged"] == 0

    client.post(
        f"/api/analysis/{analysis_id}/feedback",
        json={"decision": "genuine", "remarks": "Checked, it's hers."},
        headers=auth_headers,
    )

    after = _stats(client, auth_headers)["verdicts"]
    assert after["teacher_genuine"] == 1
    assert after["awaiting_review"] == 0
    # The AI verdict is unchanged by the teacher disagreeing with it.
    assert after["ai_flagged"] == before["ai_flagged"]


def test_recent_activity_names_the_student_and_subject(
    client: TestClient, auth_headers: dict
) -> None:
    sid, subid = _roster(client, auth_headers)
    _upload(client, auth_headers, "/api/papers/baseline", sid, subid, _ESSAY)
    _upload(client, auth_headers, "/api/papers/analyze", sid, subid, _ESSAY)

    activity = _stats(client, auth_headers)["recent_activity"]

    assert len(activity) == 1
    assert activity[0]["student_name"] == "Grace Hopper"
    assert activity[0]["subject_name"] == "English"
    assert activity[0]["teacher_decision"] is None
    assert isinstance(activity[0]["flagged"], bool)


def test_score_distribution_totals_the_analyses(
    client: TestClient, auth_headers: dict
) -> None:
    sid, subid = _roster(client, auth_headers)
    _upload(client, auth_headers, "/api/papers/baseline", sid, subid, _ESSAY)
    _upload(client, auth_headers, "/api/papers/analyze", sid, subid, _ESSAY)
    _upload(client, auth_headers, "/api/papers/analyze", sid, subid, _DIFFERENT)

    body = _stats(client, auth_headers)

    total = sum(bucket["count"] for bucket in body["score_distribution"])
    assert total == body["counts"]["analyses"] == 2


def test_every_number_is_scoped_to_the_signed_in_teacher(
    client: TestClient, register_and_login: Callable[..., dict]
) -> None:
    headers_a = register_and_login(email="a@example.com", name="Teacher A")
    headers_b = register_and_login(email="b@example.com", name="Teacher B")

    sid_a, subid_a = _roster(client, headers_a, name="A's student")
    _upload(client, headers_a, "/api/papers/baseline", sid_a, subid_a, _ESSAY)
    _upload(client, headers_a, "/api/papers/analyze", sid_a, subid_a, _ESSAY)

    stats_b = _stats(client, headers_b)

    assert stats_b["counts"] == {
        "students": 0,
        "subjects": 0,
        "baseline_papers": 0,
        "submissions": 0,
        "analyses": 0,
    }
    assert stats_b["recent_activity"] == []
    assert stats_b["subjects"] == []

    stats_a = _stats(client, headers_a)
    assert stats_a["counts"]["students"] == 1
    assert stats_a["counts"]["analyses"] == 1


def test_leaderboards_only_list_the_teachers_own_students(
    client: TestClient, register_and_login: Callable[..., dict]
) -> None:
    headers_a = register_and_login(email="a@example.com", name="Teacher A")
    headers_b = register_and_login(email="b@example.com", name="Teacher B")

    sid_a, subid_a = _roster(client, headers_a, name="A's student")
    _upload(client, headers_a, "/api/papers/baseline", sid_a, subid_a, _ESSAY)
    _upload(client, headers_a, "/api/papers/analyze", sid_a, subid_a, _DIFFERENT)

    names_b = [
        row["name"] for row in _stats(client, headers_b)["students_needing_attention"]
    ]
    assert names_b == []

    stats_a = _stats(client, headers_a)
    listed = [row["name"] for row in stats_a["students_needing_attention"]]
    assert listed == ["A's student"]

"""API surface for document extraction.

The endpoint is deliberately separate from the upload endpoints: the
teacher reviews and can correct the extracted text before it becomes a
paper, so a bad extraction never silently becomes a baseline profile.
"""

from fastapi.testclient import TestClient

from tests.helpers import api_student, api_subject


def _txt(content: bytes = b"The committee met on Tuesday to discuss the matter."):
    return {"file": ("essay.txt", content, "text/plain")}


def test_extract_returns_text_and_word_count(
    client: TestClient, auth_headers: dict
) -> None:
    response = client.post("/api/papers/extract", files=_txt(), headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["text"].startswith("The committee")
    assert body["word_count"] == 9
    assert body["source_format"] == "txt"


def test_extract_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/papers/extract", files=_txt())

    assert response.status_code == 401


def test_unsupported_file_type_returns_400(
    client: TestClient, auth_headers: dict
) -> None:
    response = client.post(
        "/api/papers/extract",
        files={"file": ("photo.jpg", b"\xff\xd8\xff binary", "image/jpeg")},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "supported" in response.json()["detail"].lower()


def test_empty_file_returns_400(client: TestClient, auth_headers: dict) -> None:
    response = client.post(
        "/api/papers/extract", files=_txt(content=b""), headers=auth_headers
    )

    assert response.status_code == 400


def test_extracted_text_can_be_uploaded_as_a_baseline(
    client: TestClient, auth_headers: dict
) -> None:
    """The whole point of the two-step flow: extract, review, then submit
    through the unchanged JSON endpoint."""
    subject_id = api_subject(client, auth_headers, "English")
    student_id = api_student(client, auth_headers, "Grace Hopper", subject_id)

    extracted = client.post(
        "/api/papers/extract", files=_txt(), headers=auth_headers
    ).json()

    response = client.post(
        "/api/papers/baseline",
        json={
            "student_id": student_id,
            "subject_id": subject_id,
            "content": extracted["text"],
            "source_format": extracted["source_format"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["source_format"] == "txt"


def test_source_format_defaults_to_paste(
    client: TestClient, auth_headers: dict
) -> None:
    """Papers submitted without a format are pastes, which keeps every
    existing client working unchanged."""
    subject_id = api_subject(client, auth_headers, "English")
    student_id = api_student(client, auth_headers, "Grace Hopper", subject_id)

    response = client.post(
        "/api/papers/baseline",
        json={
            "student_id": student_id,
            "subject_id": subject_id,
            "content": "Pasted straight into the box.",
        },
        headers=auth_headers,
    )

    assert response.json()["source_format"] == "paste"

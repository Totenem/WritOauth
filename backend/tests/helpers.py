"""Small builders shared across the test suite.

Students need at least one subject to be created through the API or the
service layer, and subjects need a course code. These keep every test from
re-deriving those rules.
"""

import itertools

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.student import Student
from models.subject import Subject


def student_payload(name: str, subject_id: int, email: str | None = None) -> dict:
    """API body for POST /api/students from a single display name."""
    first, _, last = name.partition(" ")
    return {
        "first_name": first,
        "last_name": last,
        "email": email,
        "subject_ids": [subject_id],
    }


def api_subject(client: TestClient, headers: dict, name: str = "Algebra") -> int:
    return client.post("/api/subjects", json={"name": name}, headers=headers).json()[
        "id"
    ]


def api_student(
    client: TestClient,
    headers: dict,
    name: str = "Grace Hopper",
    subject_id: int | None = None,
) -> int:
    if subject_id is None:
        subject_id = api_subject(client, headers)
    return client.post(
        "/api/students", json=student_payload(name, subject_id), headers=headers
    ).json()["id"]


_codes = itertools.count(1)


def db_subject(
    db: Session, teacher_id: int, name: str = "Algebra", code: str | None = None
) -> Subject:
    subject = Subject(
        teacher_id=teacher_id, name=name, course_code=code or f"TEST-{next(_codes):04d}"
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def db_student(db: Session, teacher_id: int, name: str = "Grace Hopper") -> Student:
    """A bare student row with no enrollments - for tests that only need a
    student to hang papers off."""
    first, _, last = name.partition(" ")
    student = Student(first_name=first, last_name=last, teacher_id=teacher_id)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

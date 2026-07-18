import pytest
from sqlalchemy.orm import Session

from application.repositories.teacher_repository import (
    TeacherEmailAlreadyExistsError,
    TeacherRepository,
)
from schemas.teacher import TeacherCreate


def test_get_by_email_returns_none_when_not_found(db_session: Session) -> None:
    repo = TeacherRepository(db_session)

    assert repo.get_by_email("missing@example.com") is None


def test_get_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repo = TeacherRepository(db_session)

    assert repo.get_by_id(999) is None


def test_create_persists_teacher_with_hashed_password(db_session: Session) -> None:
    repo = TeacherRepository(db_session)

    teacher = repo.create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )

    assert teacher.id is not None
    assert teacher.password != "secret123"
    assert teacher.password.startswith("$2b$")


def test_get_by_email_returns_created_teacher(db_session: Session) -> None:
    repo = TeacherRepository(db_session)
    repo.create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )

    found = repo.get_by_email("ada@example.com")

    assert found is not None
    assert found.name == "Ada Lovelace"


def test_get_by_id_returns_created_teacher(db_session: Session) -> None:
    repo = TeacherRepository(db_session)
    created = repo.create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )

    found = repo.get_by_id(created.id)

    assert found is not None
    assert found.email == "ada@example.com"


def test_create_duplicate_email_raises_domain_error(db_session: Session) -> None:
    repo = TeacherRepository(db_session)
    repo.create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )

    with pytest.raises(TeacherEmailAlreadyExistsError):
        repo.create(
            TeacherCreate(
                name="Grace Hopper", email="ada@example.com", password="other-pass"
            )
        )

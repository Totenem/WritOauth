import pytest
from sqlalchemy.orm import Session

from application.repositories.teacher_repository import TeacherRepository
from application.services.subject_service import (
    SubjectForbiddenError,
    SubjectNotFoundError,
    SubjectService,
)
from schemas.subject import SubjectCreate, SubjectUpdate
from schemas.teacher import TeacherCreate


def _make_teacher(db_session: Session, email: str = "ada@example.com") -> int:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(name="Ada Lovelace", email=email, password="secret123")
    )
    return teacher.id


def _create(service: SubjectService, teacher_id: int, name: str = "Algebra"):
    return service.create_subject(teacher_id, SubjectCreate(name=name))


def test_create_subject_returns_response(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    service = SubjectService(db_session)

    response = _create(service, teacher_id)

    assert response.id is not None
    assert response.name == "Algebra"
    assert response.teacher_id == teacher_id


def test_list_subjects_only_returns_own_subjects(db_session: Session) -> None:
    teacher_a = _make_teacher(db_session, email="a@example.com")
    teacher_b = _make_teacher(db_session, email="b@example.com")
    service = SubjectService(db_session)
    _create(service, teacher_a, name="Algebra")
    _create(service, teacher_b, name="Geometry")

    subjects = service.list_subjects(teacher_a)

    assert {s.name for s in subjects} == {"Algebra"}


def test_get_subject_returns_created_subject(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    service = SubjectService(db_session)
    created = _create(service, teacher_id)

    found = service.get_subject(created.id, teacher_id)

    assert found.name == "Algebra"


def test_get_subject_raises_when_not_found(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    service = SubjectService(db_session)

    with pytest.raises(SubjectNotFoundError):
        service.get_subject(999, teacher_id)


def test_get_subject_raises_forbidden_for_other_teacher(db_session: Session) -> None:
    teacher_a = _make_teacher(db_session, email="a@example.com")
    teacher_b = _make_teacher(db_session, email="b@example.com")
    service = SubjectService(db_session)
    created = _create(service, teacher_a)

    with pytest.raises(SubjectForbiddenError):
        service.get_subject(created.id, teacher_b)


def test_update_subject_modifies_and_returns_response(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    service = SubjectService(db_session)
    created = _create(service, teacher_id)

    updated = service.update_subject(
        created.id, teacher_id, SubjectUpdate(name="Advanced Algebra")
    )

    assert updated.name == "Advanced Algebra"


def test_update_subject_raises_when_not_found(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    service = SubjectService(db_session)

    with pytest.raises(SubjectNotFoundError):
        service.update_subject(999, teacher_id, SubjectUpdate(name="Advanced Algebra"))


def test_update_subject_raises_forbidden_for_other_teacher(db_session: Session) -> None:
    teacher_a = _make_teacher(db_session, email="a@example.com")
    teacher_b = _make_teacher(db_session, email="b@example.com")
    service = SubjectService(db_session)
    created = _create(service, teacher_a)

    with pytest.raises(SubjectForbiddenError):
        service.update_subject(created.id, teacher_b, SubjectUpdate(name="Geometry"))


def test_delete_subject_removes_subject(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    service = SubjectService(db_session)
    created = _create(service, teacher_id)

    service.delete_subject(created.id, teacher_id)

    with pytest.raises(SubjectNotFoundError):
        service.get_subject(created.id, teacher_id)


def test_delete_subject_raises_when_not_found(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    service = SubjectService(db_session)

    with pytest.raises(SubjectNotFoundError):
        service.delete_subject(999, teacher_id)


def test_delete_subject_raises_forbidden_for_other_teacher(db_session: Session) -> None:
    teacher_a = _make_teacher(db_session, email="a@example.com")
    teacher_b = _make_teacher(db_session, email="b@example.com")
    service = SubjectService(db_session)
    created = _create(service, teacher_a)

    with pytest.raises(SubjectForbiddenError):
        service.delete_subject(created.id, teacher_b)

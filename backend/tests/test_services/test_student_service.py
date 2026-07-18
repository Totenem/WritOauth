import pytest
from sqlalchemy.orm import Session

from application.services.student_service import StudentNotFoundError, StudentService
from schemas.student import StudentCreate, StudentUpdate


def _create(service: StudentService, name: str = "Ada Lovelace"):
    return service.create_student(StudentCreate(name=name))


def test_create_student_returns_response(db_session: Session) -> None:
    service = StudentService(db_session)

    response = _create(service)

    assert response.id is not None
    assert response.name == "Ada Lovelace"


def test_list_students_returns_created_students(db_session: Session) -> None:
    service = StudentService(db_session)
    _create(service, name="Ada Lovelace")
    _create(service, name="Grace Hopper")

    students = service.list_students()

    assert {s.name for s in students} == {"Ada Lovelace", "Grace Hopper"}


def test_get_student_returns_created_student(db_session: Session) -> None:
    service = StudentService(db_session)
    created = _create(service)

    found = service.get_student(created.id)

    assert found.name == "Ada Lovelace"


def test_get_student_raises_when_not_found(db_session: Session) -> None:
    service = StudentService(db_session)

    with pytest.raises(StudentNotFoundError):
        service.get_student(999)


def test_update_student_modifies_and_returns_response(db_session: Session) -> None:
    service = StudentService(db_session)
    created = _create(service)

    updated = service.update_student(created.id, StudentUpdate(name="Ada Byron"))

    assert updated.name == "Ada Byron"


def test_update_student_raises_when_not_found(db_session: Session) -> None:
    service = StudentService(db_session)

    with pytest.raises(StudentNotFoundError):
        service.update_student(999, StudentUpdate(name="Ada Byron"))


def test_delete_student_removes_student(db_session: Session) -> None:
    service = StudentService(db_session)
    created = _create(service)

    service.delete_student(created.id)

    with pytest.raises(StudentNotFoundError):
        service.get_student(created.id)


def test_delete_student_raises_when_not_found(db_session: Session) -> None:
    service = StudentService(db_session)

    with pytest.raises(StudentNotFoundError):
        service.delete_student(999)

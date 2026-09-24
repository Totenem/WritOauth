import pytest
from sqlalchemy.orm import Session

from application.services.student_service import (
    StudentForbiddenError,
    StudentNotFoundError,
    StudentService,
)
from models.teacher import Teacher
from schemas.student import StudentCreate, StudentResponse, StudentUpdate


def _create(
    service: StudentService, teacher_id: int, name: str = "Ada Lovelace"
) -> StudentResponse:
    return service.create_student(teacher_id, StudentCreate(name=name))


def test_create_student_returns_response(db_session: Session, teacher: Teacher) -> None:
    service = StudentService(db_session)

    response = _create(service, teacher.id)

    assert response.id is not None
    assert response.name == "Ada Lovelace"


def test_list_students_returns_created_students(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)
    _create(service, teacher.id, name="Ada Lovelace")
    _create(service, teacher.id, name="Grace Hopper")

    students = service.list_students(teacher.id)

    assert {s.name for s in students} == {"Ada Lovelace", "Grace Hopper"}


def test_list_students_excludes_other_teachers_students(
    db_session: Session, teacher: Teacher, other_teacher: Teacher
) -> None:
    service = StudentService(db_session)
    _create(service, teacher.id, name="Ada Lovelace")
    _create(service, other_teacher.id, name="Grace Hopper")

    assert [s.name for s in service.list_students(teacher.id)] == ["Ada Lovelace"]


def test_get_student_returns_created_student(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)
    created = _create(service, teacher.id)

    found = service.get_student(created.id, teacher.id)

    assert found.name == "Ada Lovelace"


def test_get_student_raises_when_not_found(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)

    with pytest.raises(StudentNotFoundError):
        service.get_student(999, teacher.id)


def test_get_another_teachers_student_raises_forbidden(
    db_session: Session, teacher: Teacher, other_teacher: Teacher
) -> None:
    service = StudentService(db_session)
    created = _create(service, teacher.id)

    with pytest.raises(StudentForbiddenError):
        service.get_student(created.id, other_teacher.id)


def test_update_student_modifies_and_returns_response(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)
    created = _create(service, teacher.id)

    updated = service.update_student(
        created.id, teacher.id, StudentUpdate(name="Ada Byron")
    )

    assert updated.name == "Ada Byron"


def test_update_student_raises_when_not_found(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)

    with pytest.raises(StudentNotFoundError):
        service.update_student(999, teacher.id, StudentUpdate(name="Ada Byron"))


def test_update_another_teachers_student_raises_forbidden(
    db_session: Session, teacher: Teacher, other_teacher: Teacher
) -> None:
    service = StudentService(db_session)
    created = _create(service, teacher.id)

    with pytest.raises(StudentForbiddenError):
        service.update_student(
            created.id, other_teacher.id, StudentUpdate(name="Hacked")
        )


def test_delete_student_removes_student(db_session: Session, teacher: Teacher) -> None:
    service = StudentService(db_session)
    created = _create(service, teacher.id)

    service.delete_student(created.id, teacher.id)

    with pytest.raises(StudentNotFoundError):
        service.get_student(created.id, teacher.id)


def test_delete_student_raises_when_not_found(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)

    with pytest.raises(StudentNotFoundError):
        service.delete_student(999, teacher.id)


def test_delete_another_teachers_student_raises_forbidden(
    db_session: Session, teacher: Teacher, other_teacher: Teacher
) -> None:
    service = StudentService(db_session)
    created = _create(service, teacher.id)

    with pytest.raises(StudentForbiddenError):
        service.delete_student(created.id, other_teacher.id)

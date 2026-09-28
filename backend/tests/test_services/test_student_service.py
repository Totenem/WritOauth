import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from application.services.student_service import (
    StudentForbiddenError,
    StudentNotFoundError,
    StudentService,
    SubjectNotEnrollableError,
)
from models.teacher import Teacher
from schemas.student import StudentCreate, StudentResponse, StudentUpdate
from tests.helpers import db_subject


def _create(
    service: StudentService,
    db_session: Session,
    teacher_id: int,
    name: str = "Ada Lovelace",
) -> StudentResponse:
    subject = db_subject(db_session, teacher_id)
    first, _, last = name.partition(" ")
    return service.create_student(
        teacher_id,
        StudentCreate(first_name=first, last_name=last, subject_ids=[subject.id]),
    )


def test_create_student_returns_response(db_session: Session, teacher: Teacher) -> None:
    service = StudentService(db_session)

    response = _create(service, db_session, teacher.id)

    assert response.id is not None
    assert response.name == "Ada Lovelace"
    assert (response.first_name, response.last_name) == ("Ada", "Lovelace")
    assert len(response.subjects) == 1


def test_create_student_requires_at_least_one_subject() -> None:
    """A brand-new account has no subjects, so it has nothing valid to send."""
    with pytest.raises(ValidationError):
        StudentCreate(first_name="Ada", last_name="Lovelace", subject_ids=[])


def test_create_student_rejects_another_teachers_subject(
    db_session: Session, teacher: Teacher, other_teacher: Teacher
) -> None:
    service = StudentService(db_session)
    theirs = db_subject(db_session, other_teacher.id)

    with pytest.raises(SubjectNotEnrollableError):
        service.create_student(
            teacher.id,
            StudentCreate(
                first_name="Ada", last_name="Lovelace", subject_ids=[theirs.id]
            ),
        )
    assert service.list_students(teacher.id) == []


def test_create_student_rejects_unknown_subject(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)

    with pytest.raises(SubjectNotEnrollableError):
        service.create_student(
            teacher.id,
            StudentCreate(first_name="Ada", last_name="Lovelace", subject_ids=[999]),
        )


def test_list_students_returns_created_students(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)
    _create(service, db_session, teacher.id, name="Ada Lovelace")
    _create(service, db_session, teacher.id, name="Grace Hopper")

    students = service.list_students(teacher.id)

    assert {s.name for s in students} == {"Ada Lovelace", "Grace Hopper"}


def test_list_students_excludes_other_teachers_students(
    db_session: Session, teacher: Teacher, other_teacher: Teacher
) -> None:
    service = StudentService(db_session)
    _create(service, db_session, teacher.id, name="Ada Lovelace")
    _create(service, db_session, other_teacher.id, name="Grace Hopper")

    assert [s.name for s in service.list_students(teacher.id)] == ["Ada Lovelace"]


def test_get_student_returns_created_student(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)
    created = _create(service, db_session, teacher.id)

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
    created = _create(service, db_session, teacher.id)

    with pytest.raises(StudentForbiddenError):
        service.get_student(created.id, other_teacher.id)


def test_update_student_modifies_and_returns_response(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)
    created = _create(service, db_session, teacher.id)

    updated = service.update_student(
        created.id, teacher.id, StudentUpdate(first_name="Ada", last_name="Byron")
    )

    assert updated.name == "Ada Byron"


def test_update_student_raises_when_not_found(
    db_session: Session, teacher: Teacher
) -> None:
    service = StudentService(db_session)

    with pytest.raises(StudentNotFoundError):
        service.update_student(
            999, teacher.id, StudentUpdate(first_name="Ada", last_name="Byron")
        )


def test_update_another_teachers_student_raises_forbidden(
    db_session: Session, teacher: Teacher, other_teacher: Teacher
) -> None:
    service = StudentService(db_session)
    created = _create(service, db_session, teacher.id)

    with pytest.raises(StudentForbiddenError):
        service.update_student(
            created.id,
            other_teacher.id,
            StudentUpdate(first_name="Hacked", last_name=""),
        )


def test_delete_student_removes_student(db_session: Session, teacher: Teacher) -> None:
    service = StudentService(db_session)
    created = _create(service, db_session, teacher.id)

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
    created = _create(service, db_session, teacher.id)

    with pytest.raises(StudentForbiddenError):
        service.delete_student(created.id, other_teacher.id)

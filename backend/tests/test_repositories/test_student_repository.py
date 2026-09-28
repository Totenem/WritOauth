from sqlalchemy.orm import Session

from application.repositories.student_repository import StudentRepository
from models.teacher import Teacher
from schemas.student import StudentCreate, StudentUpdate
from tests.helpers import db_subject


def _payload(name: str, subject_id: int, email: str | None = None) -> StudentCreate:
    first, _, last = name.partition(" ")
    return StudentCreate(
        first_name=first, last_name=last, email=email, subject_ids=[subject_id]
    )


def test_get_all_returns_empty_list_when_no_students(
    db_session: Session, teacher: Teacher
) -> None:
    repo = StudentRepository(db_session)

    assert repo.get_all(teacher.id) == []


def test_get_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repo = StudentRepository(db_session)

    assert repo.get_by_id(999) is None


def test_create_persists_student_and_enrolls_them(
    db_session: Session, teacher: Teacher
) -> None:
    repo = StudentRepository(db_session)
    subject = db_subject(db_session, teacher.id)

    student = repo.create(
        teacher.id, _payload("Ada Lovelace", subject.id, "ada@school.edu")
    )

    assert student.id is not None
    assert (student.first_name, student.last_name) == ("Ada", "Lovelace")
    assert student.name == "Ada Lovelace"
    assert student.email == "ada@school.edu"
    assert student.teacher_id == teacher.id
    assert [s.id for s in student.subjects] == [subject.id]


def test_get_all_returns_created_students(
    db_session: Session, teacher: Teacher
) -> None:
    repo = StudentRepository(db_session)
    subject = db_subject(db_session, teacher.id)
    repo.create(teacher.id, _payload("Ada Lovelace", subject.id))
    repo.create(teacher.id, _payload("Grace Hopper", subject.id))

    students = repo.get_all(teacher.id)

    assert {s.name for s in students} == {"Ada Lovelace", "Grace Hopper"}


def test_get_all_excludes_other_teachers_students(
    db_session: Session, teacher: Teacher, other_teacher: Teacher
) -> None:
    repo = StudentRepository(db_session)
    mine = db_subject(db_session, teacher.id)
    theirs = db_subject(db_session, other_teacher.id)
    repo.create(teacher.id, _payload("Ada Lovelace", mine.id))
    repo.create(other_teacher.id, _payload("Grace Hopper", theirs.id))

    assert [s.name for s in repo.get_all(teacher.id)] == ["Ada Lovelace"]
    assert [s.name for s in repo.get_all(other_teacher.id)] == ["Grace Hopper"]


def test_get_by_id_returns_created_student(
    db_session: Session, teacher: Teacher
) -> None:
    repo = StudentRepository(db_session)
    subject = db_subject(db_session, teacher.id)
    created = repo.create(teacher.id, _payload("Ada Lovelace", subject.id))

    found = repo.get_by_id(created.id)

    assert found is not None
    assert found.name == "Ada Lovelace"


def test_update_modifies_and_returns_student(
    db_session: Session, teacher: Teacher
) -> None:
    repo = StudentRepository(db_session)
    subject = db_subject(db_session, teacher.id)
    created = repo.create(teacher.id, _payload("Ada Lovelace", subject.id))

    updated = repo.update(
        created.id, StudentUpdate(first_name="Ada", last_name="Byron", email="ab@x.org")
    )

    assert updated is not None
    assert updated.name == "Ada Byron"
    refetched = repo.get_by_id(created.id)
    assert refetched is not None
    assert refetched.name == "Ada Byron"
    assert refetched.email == "ab@x.org"


def test_update_returns_none_when_not_found(db_session: Session) -> None:
    repo = StudentRepository(db_session)

    assert repo.update(999, StudentUpdate(first_name="Ada", last_name="Byron")) is None


def test_delete_removes_student_and_returns_true(
    db_session: Session, teacher: Teacher
) -> None:
    repo = StudentRepository(db_session)
    subject = db_subject(db_session, teacher.id)
    created = repo.create(teacher.id, _payload("Ada Lovelace", subject.id))

    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None


def test_delete_returns_false_when_not_found(db_session: Session) -> None:
    repo = StudentRepository(db_session)

    assert repo.delete(999) is False

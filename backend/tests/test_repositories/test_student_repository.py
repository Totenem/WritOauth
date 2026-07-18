from sqlalchemy.orm import Session

from application.repositories.student_repository import StudentRepository
from schemas.student import StudentCreate, StudentUpdate


def test_get_all_returns_empty_list_when_no_students(db_session: Session) -> None:
    repo = StudentRepository(db_session)

    assert repo.get_all() == []


def test_get_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repo = StudentRepository(db_session)

    assert repo.get_by_id(999) is None


def test_create_persists_student(db_session: Session) -> None:
    repo = StudentRepository(db_session)

    student = repo.create(StudentCreate(name="Ada Lovelace"))

    assert student.id is not None
    assert student.name == "Ada Lovelace"


def test_get_all_returns_created_students(db_session: Session) -> None:
    repo = StudentRepository(db_session)
    repo.create(StudentCreate(name="Ada Lovelace"))
    repo.create(StudentCreate(name="Grace Hopper"))

    students = repo.get_all()

    assert {s.name for s in students} == {"Ada Lovelace", "Grace Hopper"}


def test_get_by_id_returns_created_student(db_session: Session) -> None:
    repo = StudentRepository(db_session)
    created = repo.create(StudentCreate(name="Ada Lovelace"))

    found = repo.get_by_id(created.id)

    assert found is not None
    assert found.name == "Ada Lovelace"


def test_update_modifies_and_returns_student(db_session: Session) -> None:
    repo = StudentRepository(db_session)
    created = repo.create(StudentCreate(name="Ada Lovelace"))

    updated = repo.update(created.id, StudentUpdate(name="Ada Byron"))

    assert updated is not None
    assert updated.name == "Ada Byron"
    refetched = repo.get_by_id(created.id)
    assert refetched is not None
    assert refetched.name == "Ada Byron"


def test_update_returns_none_when_not_found(db_session: Session) -> None:
    repo = StudentRepository(db_session)

    assert repo.update(999, StudentUpdate(name="Ada Byron")) is None


def test_delete_removes_student_and_returns_true(db_session: Session) -> None:
    repo = StudentRepository(db_session)
    created = repo.create(StudentCreate(name="Ada Lovelace"))

    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None


def test_delete_returns_false_when_not_found(db_session: Session) -> None:
    repo = StudentRepository(db_session)

    assert repo.delete(999) is False

from sqlalchemy.orm import Session

from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from schemas.subject import SubjectCreate, SubjectUpdate
from schemas.teacher import TeacherCreate


def _make_teacher(db_session: Session, email: str = "ada@example.com") -> int:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(name="Ada Lovelace", email=email, password="secret123")
    )
    return teacher.id


def test_get_all_returns_empty_list_when_no_subjects(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    repo = SubjectRepository(db_session)

    assert repo.get_all(teacher_id) == []


def test_get_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repo = SubjectRepository(db_session)

    assert repo.get_by_id(999) is None


def test_create_persists_subject(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    repo = SubjectRepository(db_session)

    subject = repo.create(teacher_id, SubjectCreate(name="Algebra"))

    assert subject.id is not None
    assert subject.name == "Algebra"
    assert subject.teacher_id == teacher_id


def test_get_all_only_returns_subjects_for_that_teacher(db_session: Session) -> None:
    teacher_a = _make_teacher(db_session, email="a@example.com")
    teacher_b = _make_teacher(db_session, email="b@example.com")
    repo = SubjectRepository(db_session)
    repo.create(teacher_a, SubjectCreate(name="Algebra"))
    repo.create(teacher_b, SubjectCreate(name="Geometry"))

    subjects = repo.get_all(teacher_a)

    assert {s.name for s in subjects} == {"Algebra"}


def test_get_by_id_returns_created_subject(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    repo = SubjectRepository(db_session)
    created = repo.create(teacher_id, SubjectCreate(name="Algebra"))

    found = repo.get_by_id(created.id)

    assert found is not None
    assert found.name == "Algebra"


def test_update_modifies_and_returns_subject(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    repo = SubjectRepository(db_session)
    created = repo.create(teacher_id, SubjectCreate(name="Algebra"))

    updated = repo.update(created.id, SubjectUpdate(name="Advanced Algebra"))

    assert updated is not None
    assert updated.name == "Advanced Algebra"
    refetched = repo.get_by_id(created.id)
    assert refetched is not None
    assert refetched.name == "Advanced Algebra"


def test_update_returns_none_when_not_found(db_session: Session) -> None:
    repo = SubjectRepository(db_session)

    assert repo.update(999, SubjectUpdate(name="Advanced Algebra")) is None


def test_delete_removes_subject_and_returns_true(db_session: Session) -> None:
    teacher_id = _make_teacher(db_session)
    repo = SubjectRepository(db_session)
    created = repo.create(teacher_id, SubjectCreate(name="Algebra"))

    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None


def test_delete_returns_false_when_not_found(db_session: Session) -> None:
    repo = SubjectRepository(db_session)

    assert repo.delete(999) is False

import pytest
from sqlalchemy.orm import Session

from application.repositories.paper_repository import (
    PaperReferenceIntegrityError,
    PaperRepository,
)
from application.repositories.student_repository import StudentRepository
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate
from schemas.student import StudentCreate
from schemas.subject import SubjectCreate
from schemas.teacher import TeacherCreate


def _make_student_and_subject(db_session: Session) -> tuple[int, int]:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )
    student = StudentRepository(db_session).create(StudentCreate(name="Grace Hopper"))
    subject = SubjectRepository(db_session).create(
        teacher.id, SubjectCreate(name="Algebra")
    )
    return student.id, subject.id


def test_create_baseline_sets_type(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    repo = PaperRepository(db_session)

    paper = repo.create_baseline(
        BaselinePaperCreate(student_id=student_id, subject_id=subject_id, content="x")
    )

    assert paper.type == "baseline"


def test_create_submission_sets_type(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    repo = PaperRepository(db_session)

    paper = repo.create_submission(
        AnalysisPaperCreate(student_id=student_id, subject_id=subject_id, content="x")
    )

    assert paper.type == "submission"


def test_create_baseline_with_unknown_student_raises_domain_error(
    db_session: Session,
) -> None:
    _, subject_id = _make_student_and_subject(db_session)
    repo = PaperRepository(db_session)

    with pytest.raises(PaperReferenceIntegrityError):
        repo.create_baseline(
            BaselinePaperCreate(student_id=999, subject_id=subject_id, content="x")
        )


def test_create_baseline_with_unknown_subject_raises_domain_error(
    db_session: Session,
) -> None:
    student_id, _ = _make_student_and_subject(db_session)
    repo = PaperRepository(db_session)

    with pytest.raises(PaperReferenceIntegrityError):
        repo.create_baseline(
            BaselinePaperCreate(student_id=student_id, subject_id=999, content="x")
        )


def test_get_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repo = PaperRepository(db_session)

    assert repo.get_by_id(999) is None


def test_get_by_id_returns_created_paper(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    repo = PaperRepository(db_session)
    created = repo.create_baseline(
        BaselinePaperCreate(student_id=student_id, subject_id=subject_id, content="x")
    )

    found = repo.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id


def test_get_baselines_for_student_only_returns_baselines(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    repo = PaperRepository(db_session)
    repo.create_baseline(
        BaselinePaperCreate(student_id=student_id, subject_id=subject_id, content="b")
    )
    repo.create_submission(
        AnalysisPaperCreate(student_id=student_id, subject_id=subject_id, content="s")
    )

    baselines = repo.get_baselines_for_student(student_id)

    assert len(baselines) == 1
    assert baselines[0].type == "baseline"

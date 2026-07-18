import pytest
from sqlalchemy.orm import Session

from application.repositories.student_repository import StudentRepository
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from application.services.paper_service import (
    PaperInvalidReferenceError,
    PaperNotFoundError,
    PaperService,
)
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


def test_upload_baseline_returns_response_with_type(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    service = PaperService(db_session)

    response = service.upload_baseline(
        BaselinePaperCreate(student_id=student_id, subject_id=subject_id, content="x")
    )

    assert response.type == "baseline"
    assert response.student_id == student_id
    assert response.subject_id == subject_id


def test_upload_for_analysis_returns_response_with_type(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    service = PaperService(db_session)

    response = service.upload_for_analysis(
        AnalysisPaperCreate(student_id=student_id, subject_id=subject_id, content="x")
    )

    assert response.type == "submission"


def test_upload_baseline_with_unknown_student_raises(db_session: Session) -> None:
    _, subject_id = _make_student_and_subject(db_session)
    service = PaperService(db_session)

    with pytest.raises(PaperInvalidReferenceError):
        service.upload_baseline(
            BaselinePaperCreate(student_id=999, subject_id=subject_id, content="x")
        )


def test_upload_for_analysis_with_unknown_subject_raises(db_session: Session) -> None:
    student_id, _ = _make_student_and_subject(db_session)
    service = PaperService(db_session)

    with pytest.raises(PaperInvalidReferenceError):
        service.upload_for_analysis(
            AnalysisPaperCreate(student_id=student_id, subject_id=999, content="x")
        )


def test_get_paper_returns_created_paper(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    service = PaperService(db_session)
    created = service.upload_baseline(
        BaselinePaperCreate(student_id=student_id, subject_id=subject_id, content="x")
    )

    found = service.get_paper(created.id)

    assert found.id == created.id


def test_get_paper_raises_when_not_found(db_session: Session) -> None:
    service = PaperService(db_session)

    with pytest.raises(PaperNotFoundError):
        service.get_paper(999)

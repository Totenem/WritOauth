import pytest
from sqlalchemy.orm import Session

from application.repositories.analysis_repository import AnalysisRepository
from application.repositories.paper_repository import PaperRepository
from application.repositories.student_repository import StudentRepository
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from application.services.analysis_service import (
    AnalysisNotFoundError,
    AnalysisService,
    StaleAnalysisError,
)
from schemas.analysis import FeedbackCreate
from schemas.paper import AnalysisPaperCreate
from schemas.student import StudentCreate
from schemas.subject import SubjectCreate
from schemas.teacher import TeacherCreate


def _make_paper_id(db_session: Session) -> tuple[int, int]:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )
    student = StudentRepository(db_session).create(
        teacher.id, StudentCreate(name="Grace Hopper")
    )
    subject = SubjectRepository(db_session).create(
        teacher.id, SubjectCreate(name="Algebra")
    )
    paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(student_id=student.id, subject_id=subject.id, content="x")
    )
    return paper.id, teacher.id


def test_get_analysis_returns_response_with_breakdown_and_explanation(
    db_session: Session, analysis_breakdown_v2: dict
) -> None:
    paper_id, teacher_id = _make_paper_id(db_session)
    analysis = AnalysisRepository(db_session).save(
        paper_id,
        {
            "consistency_score": 92.0,
            "confidence_level": 1.0,
            "breakdown": analysis_breakdown_v2,
        },
    )
    service = AnalysisService(db_session)

    response = service.get_analysis(analysis.id, teacher_id)

    assert response.id == analysis.id
    assert response.paper_id == paper_id
    assert response.consistency_score == 92.0
    assert response.breakdown.overall.score == 92.0
    assert response.explanation.startswith("This submission scores 92%")
    assert response.flagged is False


def test_get_analysis_raises_when_not_found(db_session: Session, teacher) -> None:
    service = AnalysisService(db_session)

    with pytest.raises(AnalysisNotFoundError):
        service.get_analysis(999, teacher.id)


def test_submit_feedback_creates_feedback_for_analysis_paper(
    db_session: Session, analysis_breakdown_v2: dict
) -> None:
    paper_id, teacher_id = _make_paper_id(db_session)
    analysis = AnalysisRepository(db_session).save(
        paper_id,
        {
            "consistency_score": 92.0,
            "confidence_level": 1.0,
            "breakdown": analysis_breakdown_v2,
        },
    )
    service = AnalysisService(db_session)

    response = service.submit_feedback(
        analysis.id,
        teacher_id,
        FeedbackCreate(decision="genuine", remarks="checks out"),
    )

    assert response.paper_id == paper_id
    assert response.decision == "genuine"
    assert response.remarks == "checks out"


def test_submit_feedback_raises_when_analysis_not_found(
    db_session: Session, teacher
) -> None:
    service = AnalysisService(db_session)

    with pytest.raises(AnalysisNotFoundError):
        service.submit_feedback(999, teacher.id, FeedbackCreate(decision="genuine"))


def test_analysis_from_an_older_engine_version_is_reported_as_stale(
    db_session: Session,
) -> None:
    """A v1 breakdown holds five ad-hoc scores with no v2 equivalent.
    Coercing it into the current models would misreport the result, so the
    service refuses and the router turns this into a 409."""
    paper_id, teacher_id = _make_paper_id(db_session)
    legacy = {"vocabulary": 90.0, "style": 92.0, "explanation": "old"}
    analysis = AnalysisRepository(db_session).save(
        paper_id,
        {"consistency_score": 92.0, "confidence_level": 1.0, "breakdown": legacy},
    )
    service = AnalysisService(db_session)

    with pytest.raises(StaleAnalysisError):
        service.get_analysis(analysis.id, teacher_id)

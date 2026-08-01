import pytest
from sqlalchemy.orm import Session

from application.repositories.analysis_repository import AnalysisRepository
from application.repositories.paper_repository import PaperRepository
from application.repositories.student_repository import StudentRepository
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from application.services.analysis_service import AnalysisNotFoundError, AnalysisService
from schemas.analysis import FeedbackCreate
from schemas.paper import AnalysisPaperCreate
from schemas.student import StudentCreate
from schemas.subject import SubjectCreate
from schemas.teacher import TeacherCreate

_BREAKDOWN = {
    "vocabulary": 90.0,
    "sentence_structure": 80.0,
    "grammar": 85.0,
    "readability": 88.0,
    "style": 92.0,
    "threshold": 75.0,
    "deltas": {},
    "explanation": "This submission is 92% consistent with the baseline.",
}


def _make_paper_id(db_session: Session) -> int:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )
    student = StudentRepository(db_session).create(StudentCreate(name="Grace Hopper"))
    subject = SubjectRepository(db_session).create(
        teacher.id, SubjectCreate(name="Algebra")
    )
    paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(student_id=student.id, subject_id=subject.id, content="x")
    )
    return paper.id


def test_get_analysis_returns_response_with_breakdown_and_explanation(
    db_session: Session,
) -> None:
    paper_id = _make_paper_id(db_session)
    analysis = AnalysisRepository(db_session).save(
        paper_id,
        {"consistency_score": 92.0, "confidence_level": 1.0, "breakdown": _BREAKDOWN},
    )
    service = AnalysisService(db_session)

    response = service.get_analysis(analysis.id)

    assert response.id == analysis.id
    assert response.paper_id == paper_id
    assert response.consistency_score == 92.0
    assert response.breakdown.style == 92.0
    assert (
        response.explanation == "This submission is 92% consistent with the baseline."
    )


def test_get_analysis_raises_when_not_found(db_session: Session) -> None:
    service = AnalysisService(db_session)

    with pytest.raises(AnalysisNotFoundError):
        service.get_analysis(999)


def test_submit_feedback_creates_feedback_for_analysis_paper(
    db_session: Session,
) -> None:
    paper_id = _make_paper_id(db_session)
    analysis = AnalysisRepository(db_session).save(
        paper_id,
        {"consistency_score": 92.0, "confidence_level": 1.0, "breakdown": _BREAKDOWN},
    )
    service = AnalysisService(db_session)

    response = service.submit_feedback(
        analysis.id, FeedbackCreate(decision="genuine", remarks="checks out")
    )

    assert response.paper_id == paper_id
    assert response.decision == "genuine"
    assert response.remarks == "checks out"


def test_submit_feedback_raises_when_analysis_not_found(db_session: Session) -> None:
    service = AnalysisService(db_session)

    with pytest.raises(AnalysisNotFoundError):
        service.submit_feedback(999, FeedbackCreate(decision="genuine"))

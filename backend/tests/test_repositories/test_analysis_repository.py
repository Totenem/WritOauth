from sqlalchemy.orm import Session

from application.repositories.analysis_repository import AnalysisRepository
from application.repositories.paper_repository import PaperRepository
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from schemas.analysis import FeedbackCreate
from schemas.paper import AnalysisPaperCreate
from schemas.subject import SubjectCreate
from schemas.teacher import TeacherCreate
from tests.helpers import db_student


def _make_submission_paper_id(db_session: Session) -> int:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )
    student = db_student(db_session, teacher.id)
    subject = SubjectRepository(db_session).create(
        teacher.id, SubjectCreate(name="Algebra")
    )
    paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(student_id=student.id, subject_id=subject.id, content="x")
    )
    return paper.id


def test_save_creates_analysis_result(db_session: Session) -> None:
    paper_id = _make_submission_paper_id(db_session)
    repo = AnalysisRepository(db_session)

    analysis = repo.save(
        paper_id,
        {
            "consistency_score": 88.5,
            "confidence_level": 0.67,
            "breakdown": {"style": 88.5},
        },
    )

    assert analysis.id is not None
    assert analysis.paper_id == paper_id
    assert analysis.consistency_score == 88.5


def test_save_upserts_existing_analysis_result(db_session: Session) -> None:
    paper_id = _make_submission_paper_id(db_session)
    repo = AnalysisRepository(db_session)
    first = repo.save(
        paper_id,
        {"consistency_score": 10.0, "confidence_level": 0.3, "breakdown": {}},
    )

    second = repo.save(
        paper_id,
        {"consistency_score": 90.0, "confidence_level": 0.9, "breakdown": {}},
    )

    assert second.id == first.id
    assert second.consistency_score == 90.0


def test_get_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repo = AnalysisRepository(db_session)

    assert repo.get_by_id(999) is None


def test_get_by_paper_id_returns_none_when_not_found(db_session: Session) -> None:
    paper_id = _make_submission_paper_id(db_session)
    repo = AnalysisRepository(db_session)

    assert repo.get_by_paper_id(paper_id) is None


def test_save_feedback_creates_feedback(db_session: Session) -> None:
    paper_id = _make_submission_paper_id(db_session)
    repo = AnalysisRepository(db_session)

    feedback = repo.save_feedback(
        paper_id, FeedbackCreate(decision="genuine", remarks="looks fine")
    )

    assert feedback.paper_id == paper_id
    assert feedback.decision == "genuine"
    assert feedback.remarks == "looks fine"


def test_save_feedback_upserts_existing_feedback(db_session: Session) -> None:
    paper_id = _make_submission_paper_id(db_session)
    repo = AnalysisRepository(db_session)
    first = repo.save_feedback(paper_id, FeedbackCreate(decision="genuine"))

    second = repo.save_feedback(
        paper_id, FeedbackCreate(decision="flagged", remarks="reconsidered")
    )

    assert second.id == first.id
    assert second.decision == "flagged"
    assert second.remarks == "reconsidered"

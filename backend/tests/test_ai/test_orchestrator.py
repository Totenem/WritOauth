import pytest
from sqlalchemy.orm import Session

from ai.embedding_service import EmbeddingService
from ai.explanation_service import ExplanationService
from ai.fingerprint_service import FingerprintService
from ai.orchestrator import AIOrchestrator
from ai.profile_engine import ProfileEngine
from ai.retrieval_service import RetrievalService
from ai.scoring_service import ScoringService
from application.repositories.paper_repository import PaperRepository
from application.repositories.student_repository import StudentRepository
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from models.baseline_profile import BaselineProfile
from models.feature_vector import FeatureVector
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate
from schemas.student import StudentCreate
from schemas.subject import SubjectCreate
from schemas.teacher import TeacherCreate


def _make_orchestrator(embed_fn=None) -> AIOrchestrator:
    return AIOrchestrator(
        fingerprint=FingerprintService(),
        embedding=EmbeddingService(embed_fn=embed_fn),
        retrieval=RetrievalService(),
        scoring=ScoringService(),
        explanation=ExplanationService(),
        profile=ProfileEngine(),
    )


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


def test_process_baseline_creates_feature_vector_and_profile(
    db_session: Session,
) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    paper = PaperRepository(db_session).create_baseline(
        BaselinePaperCreate(
            student_id=student_id,
            subject_id=subject_id,
            content="The cat sat. The cat ran.",
        )
    )
    orchestrator = _make_orchestrator(embed_fn=lambda text: [1.0, 2.0, 3.0])

    profile = orchestrator.process_baseline(paper, db_session)

    feature_vector = (
        db_session.query(FeatureVector)
        .filter(FeatureVector.paper_id == paper.id)
        .first()
    )
    assert feature_vector is not None
    assert feature_vector.features["embedding"] == [1.0, 2.0, 3.0]
    assert feature_vector.features["sentence_count"] == 2

    assert isinstance(profile, BaselineProfile)
    assert profile.student_id == student_id
    assert profile.version == 1


def test_analyze_submission_without_baseline_returns_none(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(
            student_id=student_id, subject_id=subject_id, content="essay"
        )
    )
    orchestrator = _make_orchestrator(embed_fn=lambda text: [1.0, 0.0])

    result = orchestrator.analyze_submission(paper, db_session)

    assert result is None
    # The feature vector is still extracted/stored even with no baseline yet.
    feature_vector = (
        db_session.query(FeatureVector)
        .filter(FeatureVector.paper_id == paper.id)
        .first()
    )
    assert feature_vector is not None


def test_analyze_submission_scores_against_baseline(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    orchestrator = _make_orchestrator(embed_fn=lambda text: [1.0, 0.0])

    baseline_paper = PaperRepository(db_session).create_baseline(
        BaselinePaperCreate(
            student_id=student_id, subject_id=subject_id, content="The cat sat calmly."
        )
    )
    orchestrator.process_baseline(baseline_paper, db_session)

    submission_paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(
            student_id=student_id, subject_id=subject_id, content="The cat sat calmly."
        )
    )
    result = orchestrator.analyze_submission(submission_paper, db_session)

    assert result is not None
    assert result.paper_id == submission_paper.id
    assert result.consistency_score == pytest.approx(100.0)
    assert result.confidence_level == pytest.approx(1 / 3)
    assert result.breakdown["style"] == pytest.approx(100.0)
    assert "explanation" in result.breakdown
    assert "deltas" in result.breakdown


def test_analyze_submission_flags_divergent_writing(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    orchestrator = _make_orchestrator(embed_fn=lambda text: [1.0, 0.0])

    baseline_paper = PaperRepository(db_session).create_baseline(
        BaselinePaperCreate(
            student_id=student_id, subject_id=subject_id, content="The cat sat calmly."
        )
    )
    orchestrator.process_baseline(baseline_paper, db_session)

    # Different embedding vector entirely -> low cosine similarity.
    divergent_orchestrator = _make_orchestrator(embed_fn=lambda text: [0.0, 1.0])
    submission_paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(
            student_id=student_id,
            subject_id=subject_id,
            content="A completely different style of writing entirely.",
        )
    )
    result = divergent_orchestrator.analyze_submission(submission_paper, db_session)

    assert result is not None
    assert result.consistency_score == pytest.approx(50.0)

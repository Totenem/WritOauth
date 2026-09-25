import pytest
from sqlalchemy.orm import Session

from ai.explanation_service import ExplanationService
from ai.fingerprint_service import FingerprintService
from ai.orchestrator import AIOrchestrator
from ai.profile_engine import ProfileEngine
from ai.retrieval_service import RetrievalService
from ai.scoring_service import ScoringService
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from application.services.paper_service import (
    PaperForbiddenError,
    PaperNotFoundError,
    PaperService,
)
from models.analysis_result import AnalysisResult
from models.baseline_profile import BaselineProfile
from models.feature_vector import FeatureVector
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate
from schemas.subject import SubjectCreate
from schemas.teacher import TeacherCreate
from tests.helpers import db_student


def _make_orchestrator() -> AIOrchestrator:
    return AIOrchestrator(
        fingerprint=FingerprintService(),
        retrieval=RetrievalService(),
        scoring=ScoringService(),
        explanation=ExplanationService(),
        profile=ProfileEngine(),
    )


def _make_student_and_subject(db_session: Session) -> tuple[int, int, int]:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )
    student = db_student(db_session, teacher.id)
    subject = SubjectRepository(db_session).create(
        teacher.id, SubjectCreate(name="Algebra")
    )
    return student.id, subject.id, teacher.id


def test_upload_baseline_returns_response_with_type(db_session: Session) -> None:
    student_id, subject_id, teacher_id = _make_student_and_subject(db_session)
    service = PaperService(db_session)

    response = service.upload_baseline(
        BaselinePaperCreate(student_id=student_id, subject_id=subject_id, content="x"),
        teacher_id,
    )

    assert response.type == "baseline"
    assert response.student_id == student_id
    assert response.subject_id == subject_id


def test_upload_for_analysis_returns_response_with_type(db_session: Session) -> None:
    student_id, subject_id, teacher_id = _make_student_and_subject(db_session)
    service = PaperService(db_session)

    response = service.upload_for_analysis(
        AnalysisPaperCreate(student_id=student_id, subject_id=subject_id, content="x"),
        teacher_id,
    )

    assert response.type == "submission"


def test_upload_baseline_with_unknown_student_raises(db_session: Session) -> None:
    _, subject_id, teacher_id = _make_student_and_subject(db_session)
    service = PaperService(db_session)

    with pytest.raises(PaperForbiddenError):
        service.upload_baseline(
            BaselinePaperCreate(student_id=999, subject_id=subject_id, content="x"),
            teacher_id,
        )


def test_upload_for_analysis_with_unknown_subject_raises(db_session: Session) -> None:
    student_id, _, teacher_id = _make_student_and_subject(db_session)
    service = PaperService(db_session)

    with pytest.raises(PaperForbiddenError):
        service.upload_for_analysis(
            AnalysisPaperCreate(student_id=student_id, subject_id=999, content="x"),
            teacher_id,
        )


def test_get_paper_returns_created_paper(db_session: Session) -> None:
    student_id, subject_id, teacher_id = _make_student_and_subject(db_session)
    service = PaperService(db_session)
    created = service.upload_baseline(
        BaselinePaperCreate(student_id=student_id, subject_id=subject_id, content="x"),
        teacher_id,
    )

    found = service.get_paper(created.id, teacher_id)

    assert found.id == created.id


def test_get_paper_raises_when_not_found(db_session: Session, teacher) -> None:
    teacher_id = teacher.id
    service = PaperService(db_session)

    with pytest.raises(PaperNotFoundError):
        service.get_paper(999, teacher_id)


def test_upload_baseline_creates_feature_vector_and_baseline_profile(
    db_session: Session,
) -> None:
    student_id, subject_id, teacher_id = _make_student_and_subject(db_session)
    service = PaperService(db_session, orchestrator=_make_orchestrator())

    response = service.upload_baseline(
        BaselinePaperCreate(
            student_id=student_id, subject_id=subject_id, content="The cat sat calmly."
        ),
        teacher_id,
    )

    feature_vector = (
        db_session.query(FeatureVector)
        .filter(FeatureVector.paper_id == response.id)
        .first()
    )
    assert feature_vector is not None

    profile = (
        db_session.query(BaselineProfile)
        .filter(BaselineProfile.student_id == student_id)
        .first()
    )
    assert profile is not None
    # One short baseline paper is a thin profile: confidence now accounts
    # for how much text was supplied, not just how many papers.
    assert 0.0 < profile.confidence_level < 0.5


def test_upload_for_analysis_without_baseline_has_no_analysis_id(
    db_session: Session,
) -> None:
    student_id, subject_id, teacher_id = _make_student_and_subject(db_session)
    service = PaperService(db_session, orchestrator=_make_orchestrator())

    response = service.upload_for_analysis(
        AnalysisPaperCreate(student_id=student_id, subject_id=subject_id, content="x"),
        teacher_id,
    )

    assert response.analysis_id is None


def test_upload_for_analysis_with_baseline_creates_analysis_result(
    db_session: Session,
) -> None:
    student_id, subject_id, teacher_id = _make_student_and_subject(db_session)
    service = PaperService(db_session, orchestrator=_make_orchestrator())
    service.upload_baseline(
        BaselinePaperCreate(
            student_id=student_id, subject_id=subject_id, content="The cat sat calmly."
        ),
        teacher_id,
    )

    response = service.upload_for_analysis(
        AnalysisPaperCreate(
            student_id=student_id, subject_id=subject_id, content="The cat sat calmly."
        ),
        teacher_id,
    )

    assert response.analysis_id is not None
    analysis = (
        db_session.query(AnalysisResult)
        .filter(AnalysisResult.id == response.analysis_id)
        .first()
    )
    assert analysis is not None
    assert analysis.paper_id == response.id
    assert analysis.consistency_score == pytest.approx(100.0)

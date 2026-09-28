import pytest
from sqlalchemy.orm import Session

from ai.explanation_service import ExplanationService
from ai.fingerprint_service import FingerprintService
from ai.orchestrator import AIOrchestrator
from ai.profile_engine import ProfileEngine
from ai.retrieval_service import RetrievalService
from ai.scoring_service import ScoringService
from application.repositories.paper_repository import PaperRepository
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
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


def _make_student_and_subject(db_session: Session) -> tuple[int, int]:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )
    student = db_student(db_session, teacher.id)
    subject = SubjectRepository(db_session).create(
        teacher.id, SubjectCreate(name="Algebra")
    )
    return student.id, subject.id


def _upload_baseline(
    db_session: Session, student_id: int, subject_id: int, content: str
):
    paper = PaperRepository(db_session).create_baseline(
        BaselinePaperCreate(
            student_id=student_id, subject_id=subject_id, content=content
        )
    )
    _make_orchestrator().process_baseline(paper, db_session)
    return paper


def _upload_submission(
    db_session: Session, student_id: int, subject_id: int, content: str
):
    paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(
            student_id=student_id, subject_id=subject_id, content=content
        )
    )
    return _make_orchestrator().analyze_submission(paper, db_session)


def test_process_baseline_creates_feature_vector_and_profile(
    db_session: Session, persona_a_baselines
) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)

    paper = _upload_baseline(db_session, student_id, subject_id, persona_a_baselines[0])

    vector = (
        db_session.query(FeatureVector)
        .filter(FeatureVector.paper_id == paper.id)
        .first()
    )
    assert vector is not None
    assert vector.features["schema_version"] == 2

    profile = (
        db_session.query(BaselineProfile)
        .filter(BaselineProfile.student_id == student_id)
        .first()
    )
    assert profile is not None
    assert profile.aggregated_features["num_baseline_papers"] == 1


def test_submission_without_a_baseline_produces_no_analysis(
    db_session: Session, persona_a_heldout
) -> None:
    """Nothing to compare against - persisting a zeroed score would look
    like a finding rather than an absence of one."""
    student_id, subject_id = _make_student_and_subject(db_session)

    result = _upload_submission(db_session, student_id, subject_id, persona_a_heldout)

    assert result is None


def test_submission_without_a_baseline_is_still_fingerprinted(
    db_session: Session, persona_a_heldout
) -> None:
    """So it can be scored the moment a baseline exists."""
    student_id, subject_id = _make_student_and_subject(db_session)
    paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(
            student_id=student_id, subject_id=subject_id, content=persona_a_heldout
        )
    )

    _make_orchestrator().analyze_submission(paper, db_session)

    assert (
        db_session.query(FeatureVector)
        .filter(FeatureVector.paper_id == paper.id)
        .first()
        is not None
    )


def test_same_author_submission_scores_high_and_is_not_flagged(
    db_session: Session, persona_a_baselines, persona_a_heldout
) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    for text in persona_a_baselines:
        _upload_baseline(db_session, student_id, subject_id, text)

    result = _upload_submission(db_session, student_id, subject_id, persona_a_heldout)

    assert result is not None
    assert result.consistency_score > 75.0
    assert result.breakdown["flagged"] is False


def test_different_author_submission_is_flagged(
    db_session: Session, persona_a_baselines, persona_b_heldout
) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    for text in persona_a_baselines:
        _upload_baseline(db_session, student_id, subject_id, text)

    result = _upload_submission(db_session, student_id, subject_id, persona_b_heldout)

    assert result is not None
    assert result.consistency_score < 50.0
    assert result.breakdown["flagged"] is True


def test_stored_breakdown_carries_the_full_v2_payload(
    db_session: Session, persona_a_baselines, persona_a_heldout
) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    for text in persona_a_baselines:
        _upload_baseline(db_session, student_id, subject_id, text)

    result = _upload_submission(db_session, student_id, subject_id, persona_a_heldout)

    assert result is not None
    breakdown = result.breakdown
    assert breakdown["schema_version"] == 2
    assert set(breakdown["profiles"]) == {
        "lexical",
        "syntactic",
        "grammatical",
        "mechanical",
        "stylistic",
        "discourse",
    }
    assert breakdown["explanation"]
    assert breakdown["reliability"]["n_baseline_papers"] == 3


def test_consistency_score_is_the_profile_aggregate_not_an_embedding(
    db_session: Session, persona_a_baselines, persona_a_heldout
) -> None:
    """The old engine set consistency_score to a semantic embedding cosine,
    so it rewarded topic overlap. The held-out text here is on a completely
    different topic from every baseline and must still score well."""
    student_id, subject_id = _make_student_and_subject(db_session)
    for text in persona_a_baselines:
        _upload_baseline(db_session, student_id, subject_id, text)

    result = _upload_submission(db_session, student_id, subject_id, persona_a_heldout)

    assert result is not None
    assert result.consistency_score == pytest.approx(
        result.breakdown["overall"]["score"]
    )


def test_reanalysis_updates_rather_than_duplicates(
    db_session: Session, persona_a_baselines, persona_a_heldout
) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    for text in persona_a_baselines:
        _upload_baseline(db_session, student_id, subject_id, text)
    paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(
            student_id=student_id, subject_id=subject_id, content=persona_a_heldout
        )
    )

    first = _make_orchestrator().analyze_submission(paper, db_session)
    second = _make_orchestrator().analyze_submission(paper, db_session)

    assert first is not None and second is not None
    assert first.id == second.id


def test_pdf_submission_against_pasted_baselines_ignores_typography(
    db_session: Session, persona_a_baselines, persona_a_heldout
) -> None:
    """Curly quotes and spacing come from the editor, not the writer. A
    student who pastes their baselines and then uploads a PDF must not be
    penalised for changing tools - PDF extraction reliably alters exactly
    those characters.
    """
    student_id, subject_id = _make_student_and_subject(db_session)
    for text in persona_a_baselines:
        _upload_baseline(db_session, student_id, subject_id, text)

    paper = PaperRepository(db_session).create_submission(
        AnalysisPaperCreate(
            student_id=student_id,
            subject_id=subject_id,
            content=persona_a_heldout,
            source_format="pdf",
        )
    )
    result = _make_orchestrator().analyze_submission(paper, db_session)

    assert result is not None
    typography = [
        feature
        for feature in result.breakdown["profiles"]["mechanical"]["features"]
        if feature["key"] in ("curly_quote_ratio", "double_space_after_period_ratio")
    ]
    assert typography, "expected typography features to be present"
    assert all(not feature["available"] for feature in typography)
    assert all("format" in feature["suppressed_reason"] for feature in typography)

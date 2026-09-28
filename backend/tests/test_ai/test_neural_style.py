"""The LUAR neural style profile.

Nothing here downloads a model: a deterministic fake embedder stands in for
LUAR, returning hand-placed unit vectors so the geometry (and so the
expected z) is known exactly. The one real-model test at the bottom is
opt-in via RUN_NEURAL_MODEL_TESTS=1.
"""

import math
import os

import pytest
from sqlalchemy.orm import Session

from ai.explanation_service import ExplanationService
from ai.features.registry import NEURAL, PROFILE_WEIGHTS
from ai.fingerprint_service import FingerprintService
from ai.neural_style_service import (
    centroid,
    cosine_distance,
    leave_one_out_distances,
    normalize,
)
from ai.orchestrator import AIOrchestrator
from ai.profile_engine import ProfileEngine, aggregate
from ai.retrieval_service import RetrievalService
from ai.scoring_service import ScoringService
from ai.statistics import weighted_rms
from application.repositories.paper_repository import PaperRepository
from models.teacher import Teacher
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate
from tests.helpers import db_student, db_subject

_MODEL = "fake/luar@000000000000"


def _unit(angle_degrees: float) -> list[float]:
    """A unit vector in the plane - distances between these are easy to
    reason about: 1 - cos(angle between them)."""
    radians = math.radians(angle_degrees)
    return [math.cos(radians), math.sin(radians), 0.0]


def _with_vector(fingerprint: dict, vector: list[float]) -> dict:
    return {**fingerprint, "neural_style": {"model": _MODEL, "vector": vector}}


class FakeEmbedder:
    """Returns a preassigned vector per text; None for unknown text, the
    same as the real service when the model is unavailable."""

    model_id = _MODEL

    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self.vectors = vectors

    def embed(self, text: str) -> list[float] | None:
        return self.vectors.get(text)


# -- vector maths -------------------------------------------------------------


def test_centroid_and_cosine_distance() -> None:
    assert centroid([_unit(0), _unit(90)]) == pytest.approx(_unit(45))
    assert cosine_distance(_unit(0), _unit(0)) == pytest.approx(0.0)
    assert cosine_distance(_unit(0), _unit(90)) == pytest.approx(1.0)
    assert normalize([3.0, 4.0]) == pytest.approx([0.6, 0.8])


def test_leave_one_out_measures_each_paper_against_the_others() -> None:
    # Papers at -10, 0, +10 degrees: each outer one sits 15 degrees from
    # the centroid of the other two; the middle one sits exactly on theirs.
    distances = leave_one_out_distances([_unit(-10), _unit(0), _unit(10)])

    assert distances[1] == pytest.approx(0.0, abs=1e-9)
    assert distances[0] == pytest.approx(1 - math.cos(math.radians(15)))
    assert distances[2] == pytest.approx(distances[0])
    assert leave_one_out_distances([_unit(0)]) == []


# -- profile aggregation ------------------------------------------------------


def _fingerprints(texts: list[str], angles: list[float]) -> list[dict]:
    fingerprint = FingerprintService()
    return [
        _with_vector(fingerprint.extract(text), _unit(angle))
        for text, angle in zip(texts, angles)
    ]


def test_baseline_stores_centroid_and_leave_one_out_spread(
    persona_a_baselines,
) -> None:
    baseline = aggregate(_fingerprints(persona_a_baselines, [-10, 0, 10]))

    neural = baseline["neural_style"]
    assert neural["model"] == _MODEL
    assert neural["n"] == 3
    assert neural["centroid"] == pytest.approx(_unit(0))
    assert len(neural["loo_distances"]) == 3
    assert neural["mean"] == pytest.approx(sum(neural["loo_distances"]) / 3)
    assert neural["stdev"] is not None


def test_a_single_baseline_has_a_centroid_but_no_spread(persona_a_baselines) -> None:
    neural = aggregate(_fingerprints(persona_a_baselines[:1], [0]))["neural_style"]

    assert neural["n"] == 1
    assert neural["mean"] is None


def test_baselines_without_embeddings_have_no_neural_block(
    persona_a_baselines,
) -> None:
    fingerprint = FingerprintService()
    baseline = aggregate([fingerprint.extract(t) for t in persona_a_baselines])

    assert "neural_style" not in baseline


# -- scoring ------------------------------------------------------------------


def _score(persona_a_baselines, persona_a_heldout, submission_angle: float | None):
    fingerprint = FingerprintService()
    baseline = aggregate(_fingerprints(persona_a_baselines, [-10, 0, 10]))
    submission = fingerprint.extract(persona_a_heldout)
    if submission_angle is not None:
        submission = _with_vector(submission, _unit(submission_angle))
    return ScoringService().score(submission, baseline)


def test_a_submission_inside_the_students_usual_spread_scores_full_marks(
    persona_a_baselines, persona_a_heldout
) -> None:
    neural = _score(persona_a_baselines, persona_a_heldout, 5)["profiles"][NEURAL]

    assert neural["available"] is True
    # Closer to the centroid than the student's own papers typically are:
    # one-sided, so that is z = 0, not negative evidence.
    assert neural["z"] == 0.0
    assert neural["score"] == pytest.approx(100.0)


def test_a_submission_far_outside_the_spread_scores_low(
    persona_a_baselines, persona_a_heldout
) -> None:
    result = _score(persona_a_baselines, persona_a_heldout, 80)
    neural = result["profiles"][NEURAL]

    assert neural["z"] > 4
    assert neural["score"] < 20
    feature = neural["features"][0]
    assert feature["submission"] == pytest.approx(1 - math.cos(math.radians(80)))


def test_without_an_embedding_the_neural_profile_is_suppressed_with_a_reason(
    persona_a_baselines, persona_a_heldout
) -> None:
    neural = _score(persona_a_baselines, persona_a_heldout, None)["profiles"][NEURAL]

    assert neural["available"] is False
    assert neural["score"] is None
    assert neural["suppressed_reason"] == (
        "The AI style model was not available for this paper"
    )


def test_without_the_model_the_overall_score_is_the_six_profile_engine(
    persona_a_baselines, persona_a_heldout
) -> None:
    """Suppressing the neural profile must reproduce the pre-LUAR engine:
    the six stylometric weights were scaled uniformly, and weighted RMS is
    scale-invariant."""
    result = _score(persona_a_baselines, persona_a_heldout, None)
    original_weights = {
        "stylistic": 0.30,
        "syntactic": 0.20,
        "lexical": 0.15,
        "mechanical": 0.15,
        "discourse": 0.12,
        "grammatical": 0.08,
    }
    expected = weighted_rms(
        [
            (original_weights[key], profile["z"])
            for key, profile in result["profiles"].items()
            if profile["available"]
        ]
    )

    assert result["overall"]["z"] == pytest.approx(expected)


def test_profile_weights_sum_to_one() -> None:
    assert sum(PROFILE_WEIGHTS.values()) == pytest.approx(1.0)
    assert PROFILE_WEIGHTS[NEURAL] == pytest.approx(0.80)


def test_vectors_from_a_different_model_revision_are_not_compared(
    persona_a_baselines, persona_a_heldout
) -> None:
    fingerprint = FingerprintService()
    baseline = aggregate(_fingerprints(persona_a_baselines, [-10, 0, 10]))
    submission = {
        **fingerprint.extract(persona_a_heldout),
        "neural_style": {"model": "fake/luar@ffffffffffff", "vector": _unit(0)},
    }

    neural = ScoringService().score(submission, baseline)["profiles"][NEURAL]

    assert neural["available"] is False
    assert "different AI model version" in neural["suppressed_reason"]


def test_explanation_names_the_ai_fingerprint_when_it_drives_the_score(
    persona_a_baselines, persona_a_heldout
) -> None:
    breakdown = _score(persona_a_baselines, persona_a_heldout, 80)

    text = ExplanationService().explain(breakdown, 75.0)

    assert "AI style model" in text


# -- end to end through the orchestrator --------------------------------------


def test_orchestrator_embeds_papers_and_scores_the_neural_profile(
    db_session: Session,
    teacher: Teacher,
    persona_a_baselines,
    persona_a_heldout,
    persona_b_heldout,
) -> None:
    vectors = dict(zip(persona_a_baselines, [_unit(-10), _unit(0), _unit(10)]))
    vectors[persona_a_heldout] = _unit(4)
    vectors[persona_b_heldout] = _unit(75)
    orchestrator = AIOrchestrator(
        fingerprint=FingerprintService(),
        retrieval=RetrievalService(),
        scoring=ScoringService(),
        explanation=ExplanationService(),
        profile=ProfileEngine(),
        neural=FakeEmbedder(vectors),
    )
    student = db_student(db_session, teacher.id)
    subject = db_subject(db_session, teacher.id)
    papers = PaperRepository(db_session)

    for text in persona_a_baselines:
        paper = papers.create_baseline(
            BaselinePaperCreate(
                student_id=student.id, subject_id=subject.id, content=text
            )
        )
        orchestrator.process_baseline(paper, db_session)

    def analyse(text: str):
        paper = papers.create_submission(
            AnalysisPaperCreate(
                student_id=student.id, subject_id=subject.id, content=text
            )
        )
        result = orchestrator.analyze_submission(paper, db_session)
        assert result is not None
        return result.breakdown["profiles"][NEURAL]

    same_author = analyse(persona_a_heldout)
    other_author = analyse(persona_b_heldout)

    assert same_author["available"] and other_author["available"]
    assert same_author["score"] > 90
    assert other_author["score"] < 20


# -- the real model (opt-in) --------------------------------------------------


@pytest.mark.skipif(
    os.environ.get("RUN_NEURAL_MODEL_TESTS") != "1",
    reason="downloads the LUAR model (~330 MB); set RUN_NEURAL_MODEL_TESTS=1",
)
def test_real_luar_model_embeds_deterministically(
    persona_a_baselines, persona_b_heldout
) -> None:
    from ai.neural_style_service import NeuralStyleService
    from config.settings import get_settings

    settings = get_settings()
    service = NeuralStyleService(
        settings.neural_style_model, settings.neural_style_revision, enabled=True
    )

    first = service.embed(persona_a_baselines[0])
    again = service.embed(persona_a_baselines[0])
    same_author = service.embed(persona_a_baselines[1])
    other_author = service.embed(persona_b_heldout)

    assert first is not None and again is not None
    assert same_author is not None and other_author is not None
    assert len(first) == 512
    assert first == pytest.approx(again, abs=1e-5)
    # A sanity check on the personas, not a benchmark: persona A's papers
    # should sit closer to each other than to persona B.
    assert cosine_distance(first, same_author) < cosine_distance(first, other_author)

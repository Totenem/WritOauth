"""Does the engine actually separate authors?

Every other test checks that a component behaves as specified. This one
checks the thing the product exists to do. It is the test that fails if the
weights, priors or kernel are wrong in a way the unit tests can't see.
"""

import pytest

from ai.fingerprint_service import FingerprintService
from ai.profile_engine import aggregate
from ai.scoring_service import ScoringService


@pytest.fixture(scope="module")
def scored(persona_a_baselines, persona_a_heldout, persona_b_heldout):
    fingerprint = FingerprintService()
    scoring = ScoringService()
    baseline = aggregate([fingerprint.extract(t) for t in persona_a_baselines])
    return {
        "same": scoring.score(fingerprint.extract(persona_a_heldout), baseline),
        "different": scoring.score(fingerprint.extract(persona_b_heldout), baseline),
        "baseline": baseline,
    }


def test_same_author_on_a_new_topic_scores_high(scored) -> None:
    """The held-out text is about museums; every baseline is about research
    methodology. A topic-driven score would fail this."""
    assert scored["same"]["overall"]["score"] > 75.0


def test_different_author_scores_low(scored) -> None:
    assert scored["different"]["overall"]["score"] < 50.0


def test_separation_is_decisive(scored) -> None:
    same = scored["same"]["overall"]["score"]
    different = scored["different"]["overall"]["score"]
    assert same - different > 40.0, f"same={same:.1f} different={different:.1f}"


def test_different_author_diverges_on_the_stylistic_profile(scored) -> None:
    """Stylistic carries the most weight, so it should carry the signal."""
    stylistic = scored["different"]["profiles"]["stylistic"]
    assert stylistic["available"]
    assert stylistic["score"] < 50.0


def test_a_paper_scored_against_its_own_baseline_is_near_perfect(
    persona_a_baselines,
) -> None:
    fingerprint = FingerprintService()
    baseline = aggregate([fingerprint.extract(t) for t in persona_a_baselines])
    result = ScoringService().score(
        fingerprint.extract(persona_a_baselines[0]), baseline
    )
    assert result["overall"]["score"] > 85.0

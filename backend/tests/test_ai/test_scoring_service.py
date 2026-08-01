import math

from ai.scoring_service import ScoringService


def test_score_identical_vectors_maps_to_100() -> None:
    service = ScoringService()

    result = service.score([1.0, 0.0], [1.0, 0.0])

    assert math.isclose(result, 100.0)


def test_score_orthogonal_vectors_maps_to_50() -> None:
    service = ScoringService()

    result = service.score([1.0, 0.0], [0.0, 1.0])

    assert math.isclose(result, 50.0)


def test_score_opposite_vectors_maps_to_0() -> None:
    service = ScoringService()

    result = service.score([1.0, 0.0], [-1.0, 0.0])

    assert math.isclose(result, 0.0)


def test_score_handles_empty_vector() -> None:
    service = ScoringService()

    assert service.score([], [1.0]) == 0.0


def test_score_handles_mismatched_dimensions() -> None:
    service = ScoringService()

    assert service.score([1.0, 0.0], [1.0, 0.0, 0.0]) == 0.0


def test_score_breakdown_returns_all_five_categories_at_100_when_identical() -> None:
    service = ScoringService()
    fingerprint = {
        "sentence_count": 5,
        "avg_sentence_length": 12.0,
        "avg_word_length": 4.5,
        "type_token_ratio": 0.6,
    }

    breakdown = service.score_breakdown(
        fingerprint, dict(fingerprint), style_score=90.0
    )

    assert breakdown == {
        "vocabulary": 100.0,
        "sentence_structure": 100.0,
        "grammar": 100.0,
        "readability": 100.0,
        "style": 90.0,
    }


def test_score_breakdown_penalizes_full_deviation() -> None:
    service = ScoringService()
    submission = {
        "avg_sentence_length": 20.0,
        "avg_word_length": 4.0,
        "type_token_ratio": 0.5,
    }
    baseline = {
        "avg_sentence_length": 10.0,
        "avg_word_length": 4.0,
        "type_token_ratio": 0.5,
    }

    breakdown = service.score_breakdown(submission, baseline, style_score=80.0)

    assert breakdown["sentence_structure"] == 0.0  # 100% relative deviation
    assert breakdown["grammar"] == 100.0
    assert breakdown["style"] == 80.0

from ai.explanation_service import ExplanationService


def test_explain_without_deltas_returns_headline_only() -> None:
    service = ExplanationService()

    result = service.explain(score=90.0, threshold=75.0, deltas={})

    assert result == (
        "This submission is 90% consistent with the student's baseline "
        "(flag threshold 75%)."
    )


def test_explain_names_most_deviated_feature() -> None:
    service = ExplanationService()
    deltas = {
        "avg_sentence_length": {"submission": 18.2, "baseline": 11.4},
        "avg_word_length": {"submission": 4.5, "baseline": 4.4},
    }

    result = service.explain(score=60.0, threshold=75.0, deltas=deltas)

    assert result.startswith("This submission is 60% consistent")
    assert (
        "Average sentence length differs most from the baseline (18.2 vs 11.4)"
        in result
    )


def test_explain_reports_at_most_two_features() -> None:
    service = ExplanationService()
    deltas = {
        "avg_sentence_length": {"submission": 20.0, "baseline": 10.0},
        "avg_word_length": {"submission": 8.0, "baseline": 4.0},
        "type_token_ratio": {"submission": 0.9, "baseline": 0.6},
    }

    result = service.explain(score=50.0, threshold=75.0, deltas=deltas)

    assert result.count("differs") == 2  # one "differs most", one "also differs"


def test_explain_ignores_features_with_no_deviation() -> None:
    service = ExplanationService()
    deltas = {"avg_sentence_length": {"submission": 10.0, "baseline": 10.0}}

    result = service.explain(score=95.0, threshold=75.0, deltas=deltas)

    assert result == (
        "This submission is 95% consistent with the student's baseline "
        "(flag threshold 75%)."
    )

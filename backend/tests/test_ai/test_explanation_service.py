from ai.explanation_service import ExplanationService


def _breakdown(score: float, features: list[dict], available: bool = True) -> dict:
    return {
        "overall": {"score": score, "z": 1.0},
        "profiles": {
            "stylistic": {
                "label": "Stylistic",
                "available": available,
                "features": features,
            }
        },
    }


def _feature(
    label: str,
    z: float,
    kind: str = "scalar",
    measurement: str = "direct",
    key: str = "some_feature",
) -> dict:
    return {
        "key": key,
        "label": label,
        "kind": kind,
        "z": z,
        "available": True,
        "measurement": measurement,
    }


def test_headline_states_score_and_threshold() -> None:
    text = ExplanationService().explain(_breakdown(88.0, []), 75.0)

    assert "88%" in text
    assert "75%" in text
    assert "is consistent with" in text


def test_score_below_threshold_reads_as_divergent() -> None:
    text = ExplanationService().explain(_breakdown(40.0, []), 75.0)

    assert "diverges from" in text


def test_names_the_largest_driver_first() -> None:
    text = ExplanationService().explain(
        _breakdown(
            50.0,
            [
                _feature("Contraction preference", 3.2),
                _feature("Commas per sentence", 1.4),
            ],
        ),
        75.0,
    )

    assert text.index("contraction preference") < text.index("commas per sentence")


def test_reports_at_most_three_drivers() -> None:
    features = [_feature(f"Feature {i}", 4.0 - i * 0.1) for i in range(8)]

    text = ExplanationService().explain(_breakdown(30.0, features), 75.0)

    assert text.count("feature ") == 3


def test_ignores_features_within_normal_variation() -> None:
    text = ExplanationService().explain(
        _breakdown(95.0, [_feature("Commas per sentence", 0.2)]), 75.0
    )

    assert "No individual writing feature diverged" in text


def test_states_direction_for_scalars() -> None:
    higher = ExplanationService().explain(
        _breakdown(50.0, [_feature("Pronoun rate", 2.5)]), 75.0
    )
    lower = ExplanationService().explain(
        _breakdown(50.0, [_feature("Pronoun rate", -2.5)]), 75.0
    )

    assert "higher than usual" in higher
    assert "lower than usual" in lower


def test_a_mild_deviation_is_not_worded_like_a_dramatic_one() -> None:
    """z=1.2 scores ~83% (100*exp(-0.5*(1.2/2)^2)) - a mild wobble just past
    the noteworthy cutoff, not the same thing as z=4 (~13.5%). Regression
    for a report that said "higher than usual" identically for both."""
    mild = ExplanationService().explain(
        _breakdown(83.0, [_feature("Pronoun rate", 1.2)]), 75.0
    )
    dramatic = ExplanationService().explain(
        _breakdown(13.0, [_feature("Pronoun rate", 4.0)]), 75.0
    )

    assert "somewhat higher than usual" in mild
    assert "markedly higher than usual" in dramatic


def test_a_mild_neural_deviation_is_worded_more_softly_than_a_dramatic_one() -> None:
    """Same boundary as above, for the neural driver's special-cased
    phrasing. Regression for the exact reported case: z=1.2 (~83%) read as
    "further than usual" with no qualifier, same as a dramatic deviation."""
    mild = ExplanationService().explain(
        _breakdown(
            83.0, [_feature("Overall writing fingerprint", 1.2, key="luar_distance")]
        ),
        75.0,
    )
    dramatic = ExplanationService().explain(
        _breakdown(
            13.0, [_feature("Overall writing fingerprint", 4.0, key="luar_distance")]
        ),
        75.0,
    )

    assert "somewhat further than usual from" in mild
    assert "unusually far from" in dramatic


def test_distributions_are_not_described_as_higher_or_lower() -> None:
    """Jensen-Shannon divergence is always positive, so a direction would be
    meaningless for a distribution feature."""
    text = ExplanationService().explain(
        _breakdown(50.0, [_feature("Function-word usage", 3.0, kind="distribution")]),
        75.0,
    )

    assert "different pattern" in text
    assert "higher than usual" not in text


def test_flags_when_the_top_driver_is_an_approximation() -> None:
    text = ExplanationService().explain(
        _breakdown(
            50.0, [_feature("Unrecognised words", 3.0, measurement="approximation")]
        ),
        75.0,
    )

    assert "approximate" in text


def test_mentions_suppressed_profiles() -> None:
    text = ExplanationService().explain(_breakdown(90.0, [], available=False), 75.0)

    assert "could not be measured" in text


def test_warns_about_a_thin_baseline() -> None:
    text = ExplanationService().explain(
        _breakdown(90.0, []),
        75.0,
        {"n_baseline_papers": 1, "submission_word_count": 800},
    )

    assert "thin profile" in text


def test_warns_about_a_short_submission() -> None:
    text = ExplanationService().explain(
        _breakdown(90.0, []),
        75.0,
        {"n_baseline_papers": 5, "submission_word_count": 90},
    )

    assert "short" in text

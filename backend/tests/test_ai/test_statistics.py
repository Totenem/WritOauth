"""Pins the comparison maths.

These are the formulas every feature score depends on, so each degenerate
case is asserted explicitly rather than left to emerge from an end-to-end
test.
"""

import math

import pytest

from ai.statistics import (
    count_z,
    jensen_shannon,
    kernel,
    scalar_z,
    shrunk_sigma,
    stdev,
    weighted_rms,
)


class TestKernel:
    def test_zero_deviation_scores_100(self) -> None:
        assert kernel(0.0) == pytest.approx(100.0)

    def test_is_monotonically_decreasing(self) -> None:
        scores = [kernel(z) for z in (0, 1, 2, 3, 4, 6)]
        assert scores == sorted(scores, reverse=True)

    def test_is_symmetric_in_sign(self) -> None:
        assert kernel(2.5) == pytest.approx(kernel(-2.5))

    def test_saturates_without_clipping(self) -> None:
        """The old engine clipped at 0, so every deviation past 100% read as
        exactly 0.0 and large anomalies were indistinguishable."""
        assert kernel(8.0) > 0.0
        assert kernel(12.0) < kernel(8.0)


class TestShrunkSigma:
    def test_single_paper_falls_back_to_the_prior(self) -> None:
        assert shrunk_sigma(None, 1, prior_sigma=2.0, floor=0.1) == pytest.approx(2.0)

    def test_two_papers_stay_prior_dominated(self) -> None:
        """A freak-small sample stdev must not explode later z-scores."""
        assert shrunk_sigma(0.01, 2, prior_sigma=2.0, floor=0.01) > 1.5

    def test_converges_to_the_sample_stdev(self) -> None:
        far = shrunk_sigma(1.5, 500, prior_sigma=2.0, floor=0.01)
        assert far == pytest.approx(1.5, abs=0.05)

    def test_never_returns_less_than_the_floor(self) -> None:
        assert shrunk_sigma(0.0, 50, prior_sigma=0.0, floor=0.25) == 0.25

    def test_more_papers_move_monotonically_toward_the_sample(self) -> None:
        sigmas = [
            shrunk_sigma(1.0, n, prior_sigma=4.0, floor=0.001)
            for n in (1, 2, 5, 20, 100)
        ]
        assert sigmas == sorted(sigmas, reverse=True)


class TestScalarZ:
    def test_matching_value_scores_zero(self) -> None:
        assert scalar_z(10.0, 10.0, 1.0, 5, 1.0, 0.01) == pytest.approx(0.0)

    def test_sign_records_direction(self) -> None:
        assert scalar_z(12.0, 10.0, 1.0, 5, 1.0, 0.01) > 0
        assert scalar_z(8.0, 10.0, 1.0, 5, 1.0, 0.01) < 0


class TestCountZ:
    def test_never_expected_never_seen_is_no_deviation(self) -> None:
        assert count_z(0, 0.0, 500) == pytest.approx(0.0)

    def test_new_error_habit_is_positive(self) -> None:
        assert count_z(5, 0.0, 500) > 2.0

    def test_vanished_error_habit_is_strongly_negative(self) -> None:
        """The ghostwriting signal: a student who always makes an error
        suddenly making none. A Gaussian z divides by zero here."""
        assert count_z(0, 8 / 500, 500) < -3.0

    def test_expected_rate_matched_is_near_zero(self) -> None:
        assert abs(count_z(8, 8 / 500, 500)) < 0.5

    def test_zero_length_submission_is_safe(self) -> None:
        assert count_z(3, 0.01, 0) == 0.0


class TestJensenShannon:
    def test_identical_distributions_diverge_by_zero(self) -> None:
        dist = {"a": 0.5, "b": 0.5}
        assert jensen_shannon(dist, dist) == pytest.approx(0.0)

    def test_disjoint_distributions_reach_the_maximum(self) -> None:
        """Regression: additive smoothing used to cap this at 0.35, which
        compressed every distribution feature toward zero."""
        assert jensen_shannon({"a": 1.0}, {"b": 1.0}) == pytest.approx(1.0)

    def test_is_symmetric(self) -> None:
        p, q = {"a": 0.7, "b": 0.3}, {"a": 0.2, "b": 0.8}
        assert jensen_shannon(p, q) == pytest.approx(jensen_shannon(q, p))

    def test_is_bounded(self) -> None:
        for p, q in (
            ({"a": 1.0}, {"b": 1.0}),
            ({"a": 0.9, "b": 0.1}, {"a": 0.1, "b": 0.9}),
        ):
            assert 0.0 <= jensen_shannon(p, q) <= 1.0

    def test_empty_distribution_compares_as_uniform(self) -> None:
        assert jensen_shannon(
            {"a": 0.0, "b": 0.0}, {"a": 0.5, "b": 0.5}
        ) == pytest.approx(0.0)


class TestWeightedRms:
    def test_is_at_least_the_weighted_mean(self) -> None:
        values = [(1.0, 1.0), (1.0, 3.0), (1.0, 5.0)]
        arithmetic_mean = sum(z for _, z in values) / len(values)
        assert weighted_rms(values) >= arithmetic_mean

    def test_keeps_a_single_large_deviation_visible(self) -> None:
        """Seven perfect features and one 5-sigma outlier. A weighted mean of
        scores would report ~90 and shrug at the anomaly."""
        values = [(1.0, 0.0)] * 7 + [(1.0, 5.0)]
        assert kernel(weighted_rms(values)) < 75.0

    def test_zero_weight_is_safe(self) -> None:
        assert weighted_rms([]) == 0.0


class TestStdev:
    def test_undefined_below_two_values(self) -> None:
        assert stdev([]) is None
        assert stdev([1.0]) is None

    def test_uses_sample_denominator(self) -> None:
        assert stdev([1.0, 3.0]) == pytest.approx(math.sqrt(2.0))

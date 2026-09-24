"""Scores a submission against a student's baseline profile.

Every feature is reduced to a z-score (see `ai/statistics.py` for the three
comparison methods), profiles aggregate their features by weighted RMS *in
z-space*, and one kernel converts z to a 0-100 score at each level.

Aggregating in z-space rather than averaging sub-scores is deliberate: a
weighted mean of scores dilutes exactly the signal this product exists to
find. Seven features at 100 and one at 20 averages to 90 - the engine would
shrug at a 5-sigma anomaly.

Scoring uses |z|, so deviation in either direction counts equally. The sign
is preserved in the output so the explanation can say the interpretively
loaded thing ("markedly *fewer* spelling errors than this student's
baseline") without that asymmetry leaking into the arithmetic.
"""

from __future__ import annotations

from typing import Any

from ai.features.mechanical import TYPOGRAPHY_FEATURES
from ai.features.registry import (
    COUNT,
    PROFILE_LABELS,
    PROFILE_ORDER,
    PROFILE_WEIGHTS,
    SCALAR,
    FeatureSpec,
    for_profile,
)
from ai.statistics import count_z, jensen_shannon, kernel, scalar_z, weighted_rms


class ScoringService:
    """Turns a submission fingerprint + baseline profile into the breakdown."""

    def score(
        self,
        submission: dict[str, Any],
        baseline: dict[str, Any],
        *,
        same_source_format: bool = True,
        habitual_coverage: float | None = None,
    ) -> dict[str, Any]:
        meta = submission.get("meta", {})
        submission_words = int(meta.get("word_count", 0))
        sentence_count = int(meta.get("sentence_count", 0))
        paragraphs_reliable = bool(meta.get("paragraphs_reliable", False))
        baseline_papers = int(baseline.get("num_baseline_papers", 0))

        profiles: dict[str, Any] = {}
        profile_zs: list[tuple[float, float]] = []

        for profile in PROFILE_ORDER:
            evaluated = [
                self._score_feature(
                    spec,
                    submission,
                    baseline,
                    submission_words=submission_words,
                    sentence_count=sentence_count,
                    paragraphs_reliable=paragraphs_reliable,
                    baseline_papers=baseline_papers,
                    same_source_format=same_source_format,
                    habitual_coverage=habitual_coverage,
                )
                for spec in for_profile(profile)
            ]

            available = [f for f in evaluated if f["available"]]
            if available:
                profile_z = weighted_rms(
                    [(float(f["weight"]), float(f["z"])) for f in available]
                )
                profiles[profile] = {
                    "label": PROFILE_LABELS[profile],
                    "score": kernel(profile_z),
                    "z": profile_z,
                    "weight": PROFILE_WEIGHTS[profile],
                    "available": True,
                    "suppressed_reason": None,
                    "features": evaluated,
                }
                profile_zs.append((PROFILE_WEIGHTS[profile], profile_z))
            else:
                # No feature in this profile met its gate. Suppress the whole
                # profile and let the remaining weights renormalise, rather
                # than scoring it 0 and calling that a deviation.
                profiles[profile] = {
                    "label": PROFILE_LABELS[profile],
                    "score": None,
                    "z": None,
                    "weight": PROFILE_WEIGHTS[profile],
                    "available": False,
                    "suppressed_reason": "Not enough text to measure this profile",
                    "features": evaluated,
                }

        overall_z = weighted_rms(profile_zs)
        return {
            "overall": {"z": overall_z, "score": kernel(overall_z)},
            "profiles": profiles,
        }

    # ------------------------------------------------------------------
    # One feature
    # ------------------------------------------------------------------
    def _score_feature(
        self,
        spec: FeatureSpec,
        submission: dict[str, Any],
        baseline: dict[str, Any],
        *,
        submission_words: int,
        sentence_count: int,
        paragraphs_reliable: bool,
        baseline_papers: int,
        same_source_format: bool,
        habitual_coverage: float | None,
    ) -> dict[str, Any]:
        base = {
            "key": spec.key,
            "label": spec.label,
            "kind": spec.kind,
            "measurement": spec.measurement,
            "weight": spec.weight,
            "note": spec.note,
        }

        reason = self._suppression_reason(
            spec,
            submission_words=submission_words,
            sentence_count=sentence_count,
            paragraphs_reliable=paragraphs_reliable,
            baseline_papers=baseline_papers,
            same_source_format=same_source_format,
        )
        if reason is not None:
            return {**base, "available": False, "suppressed_reason": reason, "z": 0.0}

        if spec.kind == SCALAR:
            result = self._score_scalar(spec, submission, baseline, habitual_coverage)
        elif spec.kind == COUNT:
            result = self._score_count(spec, submission, baseline, submission_words)
        else:
            result = self._score_distribution(spec, submission, baseline)

        if result is None:
            return {
                **base,
                "available": False,
                "suppressed_reason": "Not present in the baseline",
                "z": 0.0,
            }

        result["score"] = kernel(float(result["z"]))
        return {**base, "available": True, "suppressed_reason": None, **result}

    @staticmethod
    def _suppression_reason(
        spec: FeatureSpec,
        *,
        submission_words: int,
        sentence_count: int,
        paragraphs_reliable: bool,
        baseline_papers: int,
        same_source_format: bool,
    ) -> str | None:
        if submission_words < spec.min_words:
            return f"Needs at least {spec.min_words} words"
        if sentence_count < spec.min_sentences:
            return f"Needs at least {spec.min_sentences} sentences"
        if spec.requires_paragraphs and not paragraphs_reliable:
            return "The submission has no paragraph breaks"
        if baseline_papers < spec.min_baseline_papers:
            return f"Needs at least {spec.min_baseline_papers} baseline papers"
        if spec.key in TYPOGRAPHY_FEATURES and not same_source_format:
            # Curly quotes and spacing describe the editor, not the writer.
            # Comparing a pasted baseline against an extracted PDF here would
            # flag a student for changing tools.
            return "Baseline and submission came from different file formats"
        return None

    @staticmethod
    def _score_scalar(
        spec: FeatureSpec,
        submission: dict[str, Any],
        baseline: dict[str, Any],
        habitual_coverage: float | None,
    ) -> dict[str, Any] | None:
        if spec.key == "habitual_ngram_coverage":
            if habitual_coverage is None:
                return None
            value = habitual_coverage
            # A student's own baseline papers are the reference: perfect
            # retention is the expectation, so the baseline mean is 1.0.
            stats = {
                "mean": 1.0,
                "stdev": None,
                "n": baseline.get("num_baseline_papers", 1),
            }
        else:
            stats = baseline.get("scalars", {}).get(spec.key)
            if stats is None or spec.key not in submission.get("scalars", {}):
                return None
            value = float(submission["scalars"][spec.key])

        z = scalar_z(
            value=value,
            baseline_mean=float(stats["mean"]),
            sample_stdev=stats.get("stdev"),
            n=int(stats.get("n", 1)),
            prior_sigma=spec.prior_sigma,
            floor=spec.floor,
        )
        return {
            "z": z,
            "submission": value,
            "baseline_mean": float(stats["mean"]),
            "baseline_stdev": stats.get("stdev"),
            "baseline_n": int(stats.get("n", 1)),
        }

    @staticmethod
    def _score_count(
        spec: FeatureSpec,
        submission: dict[str, Any],
        baseline: dict[str, Any],
        submission_words: int,
    ) -> dict[str, Any] | None:
        stats = baseline.get("counts", {}).get(spec.key)
        if stats is None or spec.key not in submission.get("counts", {}):
            return None

        events = int(submission["counts"][spec.key])
        rate = float(stats.get("rate_per_word", 0.0))
        z = count_z(events, rate, submission_words)
        return {
            "z": z,
            "submission": float(events),
            "baseline_mean": rate * submission_words,
            "baseline_stdev": None,
            "baseline_n": int(stats.get("total_words", 0)),
        }

    @staticmethod
    def _score_distribution(
        spec: FeatureSpec,
        submission: dict[str, Any],
        baseline: dict[str, Any],
    ) -> dict[str, Any] | None:
        stats = baseline.get("distributions", {}).get(spec.key)
        if stats is None or spec.key not in submission.get("distributions", {}):
            return None

        observed = submission["distributions"][spec.key]
        expected = stats.get("mean", {})
        divergence = jensen_shannon(observed, expected)

        # Scale the divergence by the student's own paper-to-paper spread
        # where it is measurable, falling back to the per-feature prior.
        spread = stats.get("mean_pairwise_jsd")
        scale = float(spread) if spread else spec.prior_sigma
        scale = max(scale, spec.floor)

        return {
            "z": divergence / scale,
            "submission": divergence,
            "baseline_mean": 0.0,
            "baseline_stdev": spread,
            "baseline_n": int(stats.get("n", 1)),
        }

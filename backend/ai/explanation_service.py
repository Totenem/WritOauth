"""Builds a teacher-facing explanation of an analysis.

Deterministic template, no LLM: the sentences below are assembled from
z-scores the scoring service already computed. That keeps explanations
reproducible and free, and means the wording can never assert something the
numbers don't support.

Two deliberate choices:

* Features are ranked by |z| across *all* profiles, not from a hardcoded
  list of four. Whatever actually diverged is what gets named.
* Direction is stated, because "markedly fewer spelling errors than usual"
  and "markedly more" tell a teacher very different stories - even though
  the score treats them identically.
"""

from __future__ import annotations

from typing import Any

from ai.features.registry import APPROXIMATION, DISTRIBUTION

_TOP_DRIVERS = 3
# Below this, a feature is within normal variation for the student and
# naming it would imply significance that isn't there.
_NOTEWORTHY_Z = 1.0


class ExplanationService:
    def explain(
        self,
        breakdown: dict[str, Any],
        threshold: float,
        reliability: dict[str, Any] | None = None,
    ) -> str:
        overall = breakdown.get("overall", {})
        score = float(overall.get("score", 0.0))

        verdict = "is consistent with" if score >= threshold else "diverges from"
        sentences = [
            f"This submission scores {score:.0f}% and {verdict} the student's "
            f"baseline (flag threshold {threshold:.0f}%)."
        ]

        drivers = _rank_drivers(breakdown)
        if drivers:
            sentences.append(_describe_drivers(drivers))
            if any(f["measurement"] == APPROXIMATION for f in drivers[:1]):
                sentences.append(
                    "The strongest signal here comes from an approximate "
                    "measure, so treat it as a prompt to look closer rather "
                    "than as evidence on its own."
                )
        else:
            sentences.append(
                "No individual writing feature diverged meaningfully from "
                "this student's usual range."
            )

        suppressed = [
            profile["label"]
            for profile in breakdown.get("profiles", {}).values()
            if not profile.get("available")
        ]
        if suppressed:
            sentences.append(
                f"{_join(suppressed)} could not be measured on this submission."
            )

        if reliability:
            caveat = _reliability_caveat(reliability)
            if caveat:
                sentences.append(caveat)

        return " ".join(sentences)


def _rank_drivers(breakdown: dict[str, Any]) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for profile in breakdown.get("profiles", {}).values():
        for feature in profile.get("features", []):
            if not feature.get("available"):
                continue
            if abs(float(feature.get("z", 0.0))) < _NOTEWORTHY_Z:
                continue
            features.append(feature)
    features.sort(key=lambda f: abs(float(f["z"])), reverse=True)
    return features[:_TOP_DRIVERS]


def _describe_drivers(drivers: list[dict[str, Any]]) -> str:
    phrases = []
    for index, feature in enumerate(drivers):
        label = str(feature["label"]).lower()
        lead = "the largest difference is" if index == 0 else "also notable is"
        phrases.append(f"{lead} {label}, which {_direction(feature)}")
    joined = "; ".join(phrases)
    return joined[0].upper() + joined[1:] + "."


def _direction(feature: dict[str, Any]) -> str:
    """Describe which way a feature moved.

    Distributions are compared by Jensen-Shannon divergence, which is always
    positive - "higher than usual" would be meaningless for them, so they
    get a shape-based phrasing instead.
    """
    if feature.get("kind") == DISTRIBUTION:
        return "follows a different pattern from usual"
    return "is higher than usual" if float(feature["z"]) > 0 else "is lower than usual"


def _reliability_caveat(reliability: dict[str, Any]) -> str | None:
    words = int(reliability.get("submission_word_count", 0))
    papers = int(reliability.get("n_baseline_papers", 0))

    if papers < 3:
        return (
            f"This student has only {papers} baseline "
            f"{'paper' if papers == 1 else 'papers'} on file, so the "
            "comparison rests on a thin profile."
        )
    if words < 150:
        return (
            f"At {words} words this submission is short, which makes every "
            "measurement noisier than usual."
        )
    return None


def _join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" and {items[-1]}"

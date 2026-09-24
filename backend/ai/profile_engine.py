"""Builds and reads a student's baseline writing profile.

The profile is the *distribution* of a student's writing, not just its
average. For each scalar feature it stores mean, standard deviation, n and
the raw per-paper values; the previous version stored means only, which made
it impossible to tell a student with wildly variable sentence length from a
metronomic one - both were scored against a single number.

Counts are pooled across baseline papers rather than averaged per paper,
which is materially more stable when events are sparse.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ai.features.registry import EXTRACTOR_VERSION, SCHEMA_VERSION
from ai.statistics import jensen_shannon, mean, stdev
from models.baseline_profile import BaselineProfile
from models.feature_vector import FeatureVector
from models.paper import Paper

# Confidence saturates at this many papers / this much text. Both are
# documented judgement calls, not measurements.
_CONFIDENT_PAPERS = 5
_CONFIDENT_WORDS = 2000


class NoBaselinePapersError(Exception):
    def __init__(self, student_id: int) -> None:
        self.student_id = student_id
        super().__init__(f"Student {student_id} has no baseline feature vectors yet")


class ProfileEngine:
    def update_profile(self, student_id: int, db: Session) -> BaselineProfile:
        feature_vectors = (
            db.query(FeatureVector)
            .join(Paper, FeatureVector.paper_id == Paper.id)
            .filter(Paper.student_id == student_id, Paper.type == "baseline")
            .order_by(FeatureVector.paper_id)
            .all()
        )
        if not feature_vectors:
            raise NoBaselinePapersError(student_id)

        fingerprints = [fv.features for fv in feature_vectors]
        aggregated = aggregate(fingerprints)
        aggregated["paper_ids"] = [fv.paper_id for fv in feature_vectors]

        latest = (
            db.query(BaselineProfile)
            .filter(BaselineProfile.student_id == student_id)
            .order_by(BaselineProfile.version.desc())
            .first()
        )
        next_version = (latest.version + 1) if latest is not None else 1

        profile = BaselineProfile(
            student_id=student_id,
            version=next_version,
            confidence_level=confidence(
                len(fingerprints), aggregated["total_baseline_words"]
            ),
            aggregated_features=aggregated,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    def get_profile(self, student_id: int, db: Session) -> BaselineProfile | None:
        return (
            db.query(BaselineProfile)
            .filter(BaselineProfile.student_id == student_id)
            .order_by(BaselineProfile.version.desc())
            .first()
        )


def confidence(paper_count: int, total_words: int) -> float:
    """How much the baseline can be trusted, 0-1.

    Both terms matter: three papers of forty words each is not a profile.
    The previous formula (`min(1, n/3)`) ignored how much text those papers
    actually contained.
    """
    by_papers = min(1.0, paper_count / _CONFIDENT_PAPERS)
    by_words = min(1.0, total_words / _CONFIDENT_WORDS) if _CONFIDENT_WORDS else 1.0
    return by_papers * by_words


def aggregate(fingerprints: list[dict[str, Any]]) -> dict[str, Any]:
    """Collapse per-paper fingerprints into one baseline profile."""
    scalars: dict[str, Any] = {}
    counts: dict[str, Any] = {}
    distributions: dict[str, Any] = {}

    total_words = sum(
        int(fp.get("meta", {}).get("word_count", 0)) for fp in fingerprints
    )

    # --- scalars: mean + stdev + the raw values ---
    for key in _keys(fingerprints, "scalars"):
        values = [
            float(fp["scalars"][key])
            for fp in fingerprints
            if key in fp.get("scalars", {})
        ]
        if not values:
            continue
        scalars[key] = {
            "mean": mean(values),
            "stdev": stdev(values),
            "n": len(values),
            # Keeping the raw values costs a few dozen floats and lets a
            # future formula change be recomputed without re-reading papers.
            "values": values,
        }

    # --- counts: pooled totals, not a mean of per-paper rates ---
    for key in _keys(fingerprints, "counts"):
        per_paper = [int(fp.get("counts", {}).get(key, 0)) for fp in fingerprints]
        total_events = sum(per_paper)
        counts[key] = {
            "total": total_events,
            "total_words": total_words,
            "rate_per_word": (total_events / total_words) if total_words else 0.0,
            "per_paper": per_paper,
        }

    # --- distributions: mean bins + within-author spread ---
    for key in _keys(fingerprints, "distributions"):
        present = [
            fp["distributions"][key]
            for fp in fingerprints
            if key in fp.get("distributions", {})
        ]
        if not present:
            continue
        distributions[key] = {
            "mean": _mean_distribution(present),
            # The student's own paper-to-paper divergence *is* the natural
            # scale for "how unusual is this submission" - available from
            # just two baseline papers, which scalars can't manage.
            "mean_pairwise_jsd": _mean_pairwise_jsd(present),
            "n": len(present),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "num_baseline_papers": len(fingerprints),
        "total_baseline_words": total_words,
        "scalars": scalars,
        "counts": counts,
        "distributions": distributions,
    }


def _keys(fingerprints: list[dict[str, Any]], bucket: str) -> list[str]:
    seen: dict[str, None] = {}
    for fingerprint in fingerprints:
        for key in fingerprint.get(bucket, {}):
            seen.setdefault(key, None)
    return list(seen)


def _mean_distribution(distributions: list[dict[str, float]]) -> dict[str, float]:
    keys: dict[str, None] = {}
    for dist in distributions:
        for key in dist:
            keys.setdefault(key, None)
    return {key: mean([float(d.get(key, 0.0)) for d in distributions]) for key in keys}


def _mean_pairwise_jsd(distributions: list[dict[str, float]]) -> float | None:
    if len(distributions) < 2:
        return None
    divergences = []
    for i in range(len(distributions)):
        for j in range(i + 1, len(distributions)):
            divergences.append(jensen_shannon(distributions[i], distributions[j]))
    return mean(divergences)

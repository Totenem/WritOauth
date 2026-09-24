"""Shared result type for the six profile extractors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass
class ProfileFeatures:
    """One profile's contribution to a paper's fingerprint.

    The three buckets are kept apart because they are compared with three
    different statistics (see `ai/statistics.py`): scalars get a shrinkage
    z-score, counts get an Anscombe-transformed Poisson z, and distributions
    get Jensen-Shannon divergence.
    """

    scalars: dict[str, float] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    distributions: dict[str, dict[str, float]] = field(default_factory=dict)


def as_distribution(counts: Mapping[str, float]) -> dict[str, float]:
    """Normalize raw bin counts to proportions summing to 1."""
    total = sum(max(0.0, float(v)) for v in counts.values())
    if total <= 0:
        return {k: 0.0 for k in counts}
    return {k: max(0.0, float(v)) / total for k, v in counts.items()}

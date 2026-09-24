"""Extracts a paper's authorship fingerprint across the six profiles.

The document is parsed with spaCy exactly once and the resulting `Document`
is shared by all six extractors - parsing is by far the most expensive step,
so running six feature sets over one essay costs barely more than running
one.

Output shape (v2):

    {
      "schema_version": 2,
      "extractor_version": "2.0.0",
      "meta": {...},             # word/sentence/paragraph counts
      "scalars": {...},          # compared by shrinkage z-score
      "counts": {...},           # compared by Anscombe-transformed Poisson z
      "distributions": {...},    # compared by Jensen-Shannon divergence
    }

The three buckets exist because the three feature kinds need three different
statistics. The previous version stored four flat floats and compared all of
them with relative deviation against a bare mean.
"""

from __future__ import annotations

from typing import Any

from ai.features import (
    discourse,
    grammatical,
    lexical,
    mechanical,
    pipeline,
    stylistic,
    syntactic,
)
from ai.features.base import ProfileFeatures
from ai.features.registry import EXTRACTOR_VERSION, SCHEMA_VERSION


class FingerprintService:
    """Runs the six profile extractors over a single parsed document."""

    def extract(
        self,
        content: str,
        baseline_vocabulary: set[str] | None = None,
    ) -> dict[str, Any]:
        """Extract every feature for one paper.

        `baseline_vocabulary` is the set of words already seen in this
        student's baseline papers. Passing it stops recurring names and
        technical terms from being counted as fresh spelling errors on every
        submission.
        """
        document = pipeline.parse(content)

        if not document.words:
            return _empty(document)

        parts: list[ProfileFeatures] = [
            lexical.extract(document),
            syntactic.extract(document),
            grammatical.extract(document),
            mechanical.extract(document, baseline_vocabulary=baseline_vocabulary),
            stylistic.extract(document),
            discourse.extract(document),
        ]

        merged = _merge(parts)
        # Stored raw (165 floats) so Burrows's Delta or the JSD stand-in can
        # be recomputed later without re-reading the paper.
        merged.distributions["function_word_freqs"] = lexical.function_word_frequencies(
            document
        )

        return {
            "schema_version": SCHEMA_VERSION,
            "extractor_version": EXTRACTOR_VERSION,
            "meta": document.meta(),
            "scalars": merged.scalars,
            "counts": merged.counts,
            "distributions": merged.distributions,
        }

    @staticmethod
    def vocabulary(content: str) -> set[str]:
        """Distinct lowercase words in a paper, for the spelling allowlist."""
        return set(pipeline.parse(content).words_lower)


def _merge(parts: list[ProfileFeatures]) -> ProfileFeatures:
    merged = ProfileFeatures()
    for part in parts:
        merged.scalars.update(part.scalars)
        merged.counts.update(part.counts)
        merged.distributions.update(part.distributions)
    return merged


def _empty(document: pipeline.Document) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "meta": document.meta(),
        "scalars": {},
        "counts": {},
        "distributions": {},
    }

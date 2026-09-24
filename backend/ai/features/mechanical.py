"""Mechanical profile: spelling, punctuation, capitalisation, apostrophes.

Pure counting, so this is one of the most honestly-measured profiles - with
one important caveat. The typography features at the bottom (curly quotes,
double-spacing after a period) describe the *editor*, not the author: Word
and most chat UIs emit curly quotes, plain textareas emit straight ones. The
scoring layer suppresses that sub-block whenever a submission's source
format differs from the baseline's, so a student isn't flagged for switching
tools.
"""

from __future__ import annotations

import re

from ai.features.base import ProfileFeatures, as_distribution
from ai.features.pipeline import Document
from ai.features.wordlists import APOSTROPHE_OMISSIONS, HOMOPHONE_PATTERNS
from ai.spelling_service import ERROR_TYPES, SpellingService

_PUNCTUATION_MARKS = {
    "comma": ",",
    "semicolon": ";",
    "colon": ":",
    "exclamation": "!",
    "question": "?",
    "quote": '"',
    "apostrophe": "'",
    "parenthesis": "(",
    "dash": "-",
}

_APOSTROPHE_OMISSION_RE = re.compile(
    r"\b(" + "|".join(APOSTROPHE_OMISSIONS) + r")\b", re.IGNORECASE
)
_POSSESSIVE = re.compile(r"\w['\u2019]s\b")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+[,.;:!?]")
_MISSING_SPACE_AFTER = re.compile(r"[,;:][A-Za-z]")
# Literal spaces only: \s{2} would also match a paragraph break, which
# is a layout artifact rather than a typing habit.
_DOUBLE_SPACE_SENTENCE = re.compile(r"[.!?][ ]{2}[A-Z]")
_CURLY = re.compile(r"[\u2018\u2019\u201c\u201d]")
_STRAIGHT = re.compile(r"[\"']")
_ALL_CAPS = re.compile(r"\b[A-Z]{2,}\b")


def extract(
    document: Document, baseline_vocabulary: set[str] | None = None
) -> ProfileFeatures:
    words = document.words_lower
    if not words:
        return ProfileFeatures()

    total = len(words)
    text = document.raw

    unknown = SpellingService.unknown_words(document, extra_known=baseline_vocabulary)
    spelling_types = {name: 0 for name in ERROR_TYPES}
    for word in unknown:
        spelling_types[SpellingService.classify(word)] += 1

    homophone_hits = sum(
        len(re.findall(pattern, text, re.IGNORECASE))
        for pattern, _ in HOMOPHONE_PATTERNS
    )

    counts = {
        "spelling_errors": len(unknown),
        "apostrophe_omissions": len(_APOSTROPHE_OMISSION_RE.findall(text)),
        "homophone_confusions": homophone_hits,
        "lowercase_i": len(re.findall(r"\bi\b", text)),
        "sentence_initial_lowercase": _sentence_initial_lowercase(document),
        # Sparse events, so they are scored as Poisson counts rather than
        # per-1000-word rates. A single occurrence in a short submission
        # swings a rate far more than it should: one "museum's" in 120 words
        # reads as 8.3 per 1k against a baseline of zero.
        "possessives": len(_POSSESSIVE.findall(text)),
        "space_before_punct": len(_SPACE_BEFORE_PUNCT.findall(text)),
        "missing_space_after_punct": len(_MISSING_SPACE_AFTER.findall(text)),
    }

    scalars = {
        "all_caps_ratio": len(_ALL_CAPS.findall(text)) / total,
        # --- typography sub-block (suppressed on format mismatch) ---
        "curly_quote_ratio": _curly_ratio(text),
        "double_space_after_period_ratio": (
            len(_DOUBLE_SPACE_SENTENCE.findall(text)) / len(document.sentences)
            if document.sentences
            else 0.0
        ),
    }

    distributions = {
        "punctuation_profile": as_distribution(
            {name: text.count(mark) for name, mark in _PUNCTUATION_MARKS.items()}
        ),
        "spelling_error_types": as_distribution(spelling_types),
    }
    return ProfileFeatures(scalars=scalars, counts=counts, distributions=distributions)


# Features that describe the editing tool rather than the writer. The
# scoring layer drops these when baseline and submission source formats
# differ - see `ScoringService`.
TYPOGRAPHY_FEATURES = frozenset(
    {
        "curly_quote_ratio",
        "double_space_after_period_ratio",
        "space_before_punct",
    }
)


def _curly_ratio(text: str) -> float:
    curly = len(_CURLY.findall(text))
    straight = len(_STRAIGHT.findall(text))
    total = curly + straight
    return curly / total if total else 0.0


def _sentence_initial_lowercase(document: Document) -> int:
    hits = 0
    for sentence in document.sentences:
        first = next((t for t in sentence if not t.is_punct and not t.is_space), None)
        if first is not None and first.text[:1].islower() and first.is_alpha:
            hits += 1
    return hits

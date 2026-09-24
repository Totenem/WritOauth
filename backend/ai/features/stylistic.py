"""Stylistic profile: function words, transitions, pronouns, contractions.

This profile carries the most weight in the overall score. Function-word
usage is the gold-standard authorship signal in the stylometry literature:
it is topic-independent and largely unconscious, so it survives a student
writing about something new - which is exactly where the old embedding-based
score failed.
"""

from __future__ import annotations

import re

from ai.features.base import ProfileFeatures, as_distribution
from ai.features.pipeline import Document
from ai.features.wordlists import EXPANDED_FORMS, PRONOUNS, TRANSITIONS

_CONTRACTION = re.compile(r"\b\w+['\u2019](?:t|s|re|ve|ll|d|m)\b", re.IGNORECASE)

# Flatten the transition table once: longest phrases first so "as a result
# of" matches before "as a result".
_TRANSITION_PHRASES: tuple[tuple[str, str], ...] = tuple(
    sorted(
        (
            (phrase, category)
            for category, phrases in TRANSITIONS.items()
            for phrase in phrases
        ),
        key=lambda item: -len(item[0]),
    )
)

_PRONOUN_LOOKUP: dict[str, str] = {
    word: category for category, words in PRONOUNS.items() for word in words
}


def extract(document: Document) -> ProfileFeatures:
    words = document.words_lower
    if not words:
        return ProfileFeatures()

    total = len(words)
    lowered = document.raw.lower()

    transition_counts = _transition_counts(lowered)
    pronoun_counts = _pronoun_counts(words)
    contractions = len(_CONTRACTION.findall(document.raw))
    expanded = sum(lowered.count(form) for form in EXPANDED_FORMS)

    scalars = {
        "transition_rate_per_1k": sum(transition_counts.values()) / total * 1000,
        "pronoun_rate_per_1k": sum(pronoun_counts.values()) / total * 1000,
        "contraction_rate_per_1k": contractions / total * 1000,
        # Preference between "don't" and "do not" is more length-robust than
        # a raw contraction rate, and is a strong register signal.
        "contraction_preference": (
            contractions / (contractions + expanded)
            if (contractions + expanded) > 0
            else 0.0
        ),
        "function_word_ratio": sum(
            1
            for t in document.words
            if t.pos_ in ("ADP", "DET", "CCONJ", "SCONJ", "PRON", "AUX", "PART")
        )
        / total,
    }

    distributions = {
        "transition_categories": as_distribution(transition_counts),
        "pronoun_categories": as_distribution(pronoun_counts),
    }
    return ProfileFeatures(scalars=scalars, distributions=distributions)


def _transition_counts(lowered_text: str) -> dict[str, int]:
    """Count connectives by category.

    Matched phrases are blanked out as they are consumed so a long phrase
    isn't also counted as the shorter one nested inside it.
    """
    counts = {category: 0 for category in TRANSITIONS}
    remaining = lowered_text
    for phrase, category in _TRANSITION_PHRASES:
        pattern = re.compile(r"\b" + re.escape(phrase) + r"\b")
        found = pattern.findall(remaining)
        if found:
            counts[category] += len(found)
            remaining = pattern.sub(" \x00 ", remaining)
    return counts


def _pronoun_counts(words: list[str]) -> dict[str, int]:
    counts = {category: 0 for category in PRONOUNS}
    for word in words:
        category = _PRONOUN_LOOKUP.get(word)
        if category is not None:
            counts[category] += 1
    return counts


def habitual_ngrams(
    documents: list[Document], top_k: int = 20, min_document_frequency: int = 2
) -> list[dict[str, object]]:
    """Recurring 3- and 4-grams across a student's baseline papers.

    Only n-grams containing at least two function words are kept, so the
    result is phrasing habit ("one of the most", "it is clear that") rather
    than subject matter. The document-frequency floor is essential: with a
    single baseline paper this would just memorise that document.
    """
    if len(documents) < min_document_frequency:
        return []

    per_document: list[dict[str, int]] = []
    for document in documents:
        counts: dict[str, int] = {}
        words = document.words_lower
        for size in (3, 4):
            for i in range(len(words) - size + 1):
                gram = words[i : i + size]
                if _function_word_count(gram) < 2:
                    continue
                key = " ".join(gram)
                counts[key] = counts.get(key, 0) + 1
        per_document.append(counts)

    document_frequency: dict[str, int] = {}
    total_occurrences: dict[str, int] = {}
    for counts in per_document:
        for phrase, occurrences in counts.items():
            document_frequency[phrase] = document_frequency.get(phrase, 0) + 1
            total_occurrences[phrase] = total_occurrences.get(phrase, 0) + occurrences

    eligible = [
        (phrase, document_frequency[phrase], total_occurrences[phrase])
        for phrase in document_frequency
        if document_frequency[phrase] >= min_document_frequency
    ]
    eligible.sort(key=lambda item: (-item[2], -item[1], item[0]))

    total_words = sum(len(d.words_lower) for d in documents) or 1
    return [
        {
            "ngram": phrase,
            "document_frequency": df,
            "rate_per_1k": occurrences / total_words * 1000,
        }
        for phrase, df, occurrences in eligible[:top_k]
    ]


def habitual_coverage(document: Document, ngrams: list[dict[str, object]]) -> float:
    """Share of the student's habitual phrases present in this paper."""
    if not ngrams:
        return 0.0
    haystack = " ".join(document.words_lower)
    present = sum(1 for entry in ngrams if str(entry["ngram"]) in haystack)
    return present / len(ngrams)


def _function_word_count(gram: list[str]) -> int:
    function_words = _function_word_set()
    return sum(1 for w in gram if w in function_words)


_FUNCTION_WORD_CACHE: frozenset[str] | None = None


def _function_word_set() -> frozenset[str]:
    global _FUNCTION_WORD_CACHE
    if _FUNCTION_WORD_CACHE is None:
        from ai.features.wordlists import FUNCTION_WORDS

        _FUNCTION_WORD_CACHE = frozenset(FUNCTION_WORDS)
    return _FUNCTION_WORD_CACHE

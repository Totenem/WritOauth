"""Spelling checks for the Mechanical profile.

`pyspellchecker` has no dependencies and ships a ~130k-entry frequency
dictionary. That dictionary materialises to roughly 25-40 MB of RSS, so it
is loaded lazily once per process, the same way the spaCy pipeline is.

Performance note: `unknown()` is an O(1) dict lookup per word, but
`candidates()`/`correction()` generate every edit-1 permutation of a word
(~54 * len(word) lookups). Candidate generation therefore runs *only* over
the handful of words already known to be unknown, never over the whole
document.
"""

from __future__ import annotations

from typing import Any

# Error shapes, derived by comparing an unknown word to its nearest known
# neighbour. Gives "recurring error types" rather than just a count.
ERROR_TYPES = (
    "transposition",
    "doubled_letter",
    "omitted_letter",
    "inserted_letter",
    "substitution",
    "unclassified",
)


class SpellingService:
    _checker: Any = None

    @classmethod
    def _get(cls) -> Any:
        if cls._checker is None:
            from spellchecker import SpellChecker

            cls._checker = SpellChecker(language="en", distance=1)
        return cls._checker

    @classmethod
    def reset(cls) -> None:
        """Test hook."""
        cls._checker = None

    @classmethod
    def unknown_words(
        cls, document: Any, extra_known: set[str] | None = None
    ) -> list[str]:
        """Words the dictionary doesn't recognise.

        Proper nouns are the dominant false positive, so tokens spaCy tags
        as PROPN are skipped, as is any capitalised token that isn't
        sentence-initial. Names and technical terms can still leak through,
        and the filter cuts the other way too: a misspelling that spaCy
        mistags as PROPN (common for an unknown capitalised word at the
        start of a sentence) is skipped. This measures "unrecognised words",
        not "misspellings". The same filter runs over baseline and
        submission, so the bias cancels in a z-score.
        """
        checker = cls._get()
        sentence_starts = {s.start for s in document.doc.sents}

        candidates: list[str] = []
        for token in document.doc:
            if not token.is_alpha or len(token.text) < 3:
                continue
            if token.pos_ == "PROPN":
                continue
            if token.text.isupper():
                continue
            if token.text[0].isupper() and token.i not in sentence_starts:
                continue
            candidates.append(token.text.lower())

        if not candidates:
            return []

        known_extra = extra_known or set()
        unknown = checker.unknown(candidates)
        return [w for w in candidates if w in unknown and w not in known_extra]

    @classmethod
    def classify(cls, word: str) -> str:
        """Bucket an unknown word by its cheapest edit-1 transform.

        Only ever called on the small set of already-unknown words.
        """
        checker = cls._get()
        try:
            candidates = checker.candidates(word)
        except Exception:  # pragma: no cover - defensive
            return "unclassified"
        if not candidates:
            return "unclassified"

        best = min(candidates, key=lambda c: (abs(len(c) - len(word)), c))
        return _edit_type(word, best)


def _edit_type(wrong: str, right: str) -> str:
    if wrong == right:
        return "unclassified"

    if len(wrong) == len(right):
        differences = [i for i in range(len(wrong)) if wrong[i] != right[i]]
        if len(differences) == 2:
            i, j = differences
            if j == i + 1 and wrong[i] == right[j] and wrong[j] == right[i]:
                return "transposition"
        if len(differences) == 1:
            return "substitution"
        return "unclassified"

    if len(wrong) == len(right) + 1:
        # An extra character: doubled if it repeats its neighbour.
        for i in range(len(wrong) - 1):
            if wrong[i] == wrong[i + 1] and wrong[:i] + wrong[i + 1 :] == right:
                return "doubled_letter"
        return "inserted_letter"

    if len(wrong) + 1 == len(right):
        return "omitted_letter"

    return "unclassified"

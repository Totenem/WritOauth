"""Syllable counting for the readability formulas.

Uses pyphen (hyphenation dictionaries) rather than textstat: textstat pulls
in nltk plus four transitive dependencies, and some of its code paths expect
corpora to be downloadable at runtime, which would break the engine's
offline and deterministic guarantees.

Hyphenation points approximate syllable boundaries. The approximation is
consistent across baseline and submission, so it cancels in a z-score - but
an absolute syllable count from here is not authoritative.
"""

from __future__ import annotations

import re
from typing import Any

_VOWEL_GROUPS = re.compile(r"[aeiouy]+")


class _Hyphenator:
    _dic: Any = None
    _unavailable = False

    @classmethod
    def get(cls) -> Any:
        if cls._dic is None and not cls._unavailable:
            try:
                import pyphen

                cls._dic = pyphen.Pyphen(lang="en_US")
            except Exception:  # pragma: no cover - defensive
                cls._unavailable = True
        return cls._dic


def count_syllables(word: str) -> int:
    """Syllables in a single word, minimum 1."""
    cleaned = word.strip().lower()
    if not cleaned:
        return 0

    dic = _Hyphenator.get()
    if dic is not None:
        positions = dic.positions(cleaned)
        if positions or len(cleaned) <= 3:
            return len(positions) + 1

    return _fallback_syllables(cleaned)


def _fallback_syllables(word: str) -> int:
    """Vowel-group heuristic, used when pyphen is unavailable."""
    groups = _VOWEL_GROUPS.findall(word)
    count = len(groups)
    # A trailing silent "e" isn't a syllable ("make" = 1, not 2).
    if word.endswith("e") and count > 1 and not word.endswith(("le", "ee", "ye")):
        count -= 1
    return max(1, count)

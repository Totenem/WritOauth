"""Lexical profile: vocabulary diversity, density, word preferences, length.

Every feature here is length-invariant by construction. The previous engine
scored raw `type_token_ratio`, which falls monotonically with document
length - the same student's 1500-word and 400-word essays differed by ~0.15,
reading as a large deviation for what is purely a length artifact.

Yule's K was considered and rejected for the same reason: it carries a
systematic 5000/N length bias (doubling a text shifts K by that amount), and
MATTR-100 plus the windowed hapax ratio already cover vocabulary diversity
without it.
"""

from __future__ import annotations

from ai.features.base import ProfileFeatures
from ai.features.pipeline import Document
from ai.features.syllables import count_syllables
from ai.features.wordlists import FUNCTION_WORDS

_FUNCTION_WORD_SET = frozenset(FUNCTION_WORDS)
_MATTR_WINDOW = 100

# POS tags spaCy assigns to content (open-class) words.
_CONTENT_POS = frozenset({"NOUN", "PROPN", "VERB", "ADJ", "ADV"})

_LATINATE_SUFFIXES = (
    "tion",
    "sion",
    "ment",
    "ity",
    "ous",
    "ive",
    "ate",
    "ize",
    "ise",
    "ance",
    "ence",
    "ism",
    "ify",
)


def extract(document: Document) -> ProfileFeatures:
    words = document.words_lower
    if not words:
        return ProfileFeatures()

    scalars = {
        "mattr_100": _mattr(words, _MATTR_WINDOW),
        "hapax_ratio_windowed": _windowed_hapax(words, _MATTR_WINDOW),
        "lexical_density": _lexical_density(document),
        "avg_word_length": sum(len(w) for w in words) / len(words),
        "long_word_ratio": sum(1 for w in words if len(w) >= 7) / len(words),
        "avg_syllables_per_word": sum(count_syllables(w) for w in words) / len(words),
        "latinate_suffix_ratio": sum(1 for w in words if w.endswith(_LATINATE_SUFFIXES))
        / len(words),
    }
    return ProfileFeatures(scalars=scalars)


def _mattr(words: list[str], window: int) -> float:
    """Moving-average type-token ratio.

    Length-invariant, unlike plain TTR: every window is the same size, so
    comparing a long and a short document is meaningful.
    """
    if len(words) < window:
        # Too short for a full window - fall back to plain TTR. The caller's
        # `min_words` gate normally prevents this from being scored.
        return len(set(words)) / len(words)

    ratios = []
    for start in range(len(words) - window + 1):
        ratios.append(len(set(words[start : start + window])) / window)
    return sum(ratios) / len(ratios)


def _windowed_hapax(words: list[str], window: int) -> float:
    """Proportion of once-only words, measured inside fixed windows.

    A raw hapax ratio over the whole document is length-dependent; averaging
    it over equal-sized windows is not.
    """
    if len(words) < window:
        counts: dict[str, int] = {}
        for word in words:
            counts[word] = counts.get(word, 0) + 1
        return sum(1 for c in counts.values() if c == 1) / len(set(words) or {1})

    ratios = []
    for start in range(0, len(words) - window + 1, max(1, window // 4)):
        chunk = words[start : start + window]
        counts = {}
        for word in chunk:
            counts[word] = counts.get(word, 0) + 1
        types = len(counts)
        ratios.append(sum(1 for c in counts.values() if c == 1) / types)
    return sum(ratios) / len(ratios) if ratios else 0.0


def _lexical_density(document: Document) -> float:
    """Content words as a share of all words.

    Measured from spaCy POS tags. The usual no-tagger substitute - "any word
    not in a stoplist is content" - misclassifies every function word the
    list happens to omit; this is the real thing.
    """
    words = document.words
    if not words:
        return 0.0
    content = sum(1 for t in words if t.pos_ in _CONTENT_POS)
    return content / len(words)


def function_word_frequencies(document: Document) -> dict[str, float]:
    """Relative frequency of each tracked function word.

    Stored raw on the fingerprint so Burrows's Delta (or the JSD stand-in)
    can be recomputed later without re-reading the paper.
    """
    words = document.words_lower
    if not words:
        return {w: 0.0 for w in FUNCTION_WORDS}

    counts: dict[str, int] = {}
    for word in words:
        if word in _FUNCTION_WORD_SET:
            counts[word] = counts.get(word, 0) + 1
    total = len(words)
    return {w: counts.get(w, 0) / total for w in FUNCTION_WORDS}

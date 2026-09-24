"""Grammatical profile: accuracy, error frequency, recurring error types.

HONEST LIMITS - read before presenting any number from this module.

This detector is high-precision and **low-recall**. It catches a minority of
genuine grammatical errors: it cannot detect most tense inconsistency,
article omission, countability errors, word-order errors, or anything
needing real semantic understanding. A true grammar checker means
`language_tool_python`, which requires a JVM and a ~200 MB download - out of
scope.

It is also **dialect-normative**: subject-verb patterns that are standard in
AAVE, Indian English, Singaporean English and some L2 varieties are counted
as errors here.

Because the engine only ever compares a student against *their own*
baseline, a constant detection bias cancels out in a z-score. But an
absolute error count from this module is NOT a valid measure of a student's
grammatical ability and must never be presented to a teacher as one.

Precision is prioritised over recall deliberately: counts are z-scored, so a
rule that fires spuriously at a constant rate is harmless, while a rule with
a high false-positive rate contributes mostly noise variance and drowns the
real signal.
"""

from __future__ import annotations

import re

from ai.features.base import ProfileFeatures, as_distribution
from ai.features.pipeline import Document
from ai.features.wordlists import (
    A_BEFORE_VOWEL_OK,
    AN_BEFORE_CONSONANT_OK,
    LEGITIMATE_DOUBLES,
    SV_DISAGREEMENTS,
)

ERROR_FAMILIES = (
    "subject_verb_agreement",
    "article_a_an",
    "repeated_word",
    "comma_splice",
    "missing_terminal_punctuation",
    "run_on",
)

_SV_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in SV_DISAGREEMENTS)
_REPEATED = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)
_COMMA_SPLICE = re.compile(
    r",\s+(i|he|she|it|we|they|you)\s+"
    r"(is|are|was|were|have|has|had|will|would|can|could|do|does|did|am)\b",
    re.IGNORECASE,
)
_A_AN = re.compile(r"\b(an?)\s+([a-z]+)", re.IGNORECASE)
_VOWELS = frozenset("aeiou")

# A sentence longer than this with no internal punctuation reads as a run-on.
_RUN_ON_WORDS = 30


def extract(document: Document) -> ProfileFeatures:
    if not document.words:
        return ProfileFeatures()

    text = document.raw
    counts = {
        "subject_verb_agreement": _subject_verb_errors(document, text),
        "article_a_an": _article_errors(text),
        "repeated_word": _repeated_words(text),
        "comma_splice": len(_COMMA_SPLICE.findall(text)),
        "missing_terminal_punctuation": _missing_terminal(document),
        "run_on": _run_ons(document),
    }

    distributions = {
        "grammar_error_types": as_distribution(
            {family: counts[family] for family in ERROR_FAMILIES}
        )
    }
    return ProfileFeatures(counts=counts, distributions=distributions)


def _subject_verb_errors(document: Document, text: str) -> int:
    """Agreement errors, from closed-class patterns plus spaCy morphology.

    The regex patterns are near-perfect precision (both sides closed-class).
    The morphological pass catches cases the patterns miss by comparing the
    `Number` feature of an `nsubj` against its governing verb.
    """
    hits = sum(len(pattern.findall(text)) for pattern in _SV_PATTERNS)

    for token in document.doc:
        if token.dep_ != "nsubj" or token.head.pos_ not in ("VERB", "AUX"):
            continue
        subject_number = token.morph.get("Number")
        verb_number = token.head.morph.get("Number")
        verb_tense = token.head.morph.get("Tense")
        # Only present-tense finite verbs mark number in English, so this is
        # the only place a disagreement is detectable morphologically.
        if not subject_number or not verb_number or verb_tense != ["Pres"]:
            continue
        if subject_number != verb_number:
            hits += 1

    return hits


def _article_errors(text: str) -> int:
    hits = 0
    for match in _A_AN.finditer(text):
        article = match.group(1).lower()
        word = match.group(2).lower()
        if not word:
            continue
        starts_with_vowel = word[0] in _VOWELS
        if article == "a" and starts_with_vowel and word not in A_BEFORE_VOWEL_OK:
            hits += 1
        elif (
            article == "an"
            and not starts_with_vowel
            and word not in AN_BEFORE_CONSONANT_OK
        ):
            hits += 1
    return hits


def _repeated_words(text: str) -> int:
    return sum(
        1
        for match in _REPEATED.finditer(text)
        if match.group(0).lower() not in LEGITIMATE_DOUBLES
    )


def _missing_terminal(document: Document) -> int:
    """Sentences not closed by terminal punctuation.

    The final sentence is exempt: an unterminated last line is usually a
    truncated paste, not a habit.
    """
    sentences = document.sentences
    if len(sentences) < 2:
        return 0
    return sum(
        1
        for sentence in sentences[:-1]
        if not sentence.text.strip().endswith((".", "!", "?", '"', "'", ")"))
    )


def _run_ons(document: Document) -> int:
    hits = 0
    for sentence in document.sentences:
        words = [t for t in sentence if t.is_alpha]
        if len(words) < _RUN_ON_WORDS:
            continue
        internal = sum(1 for t in sentence if t.text in (",", ";", ":", "-"))
        if internal == 0:
            hits += 1
    return hits

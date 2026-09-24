"""Discourse & Complexity profile: paragraphs, cohesion, readability.

Flesch Reading Ease and Gunning Fog are implemented here rather than taken
from `textstat`, which pulls in nltk plus four transitive dependencies and
expects downloadable corpora at runtime. Owning the formulas keeps the
engine offline and deterministic, and lets Fog exclude proper nouns and
purely inflectional complexity the way its definition actually specifies.

Flesch-Kincaid Grade is deliberately omitted: it correlates ~-0.99 with
Flesch Reading Ease (same two inputs, rearranged), so scoring both would
double-count under the RMS aggregation.
"""

from __future__ import annotations

from ai.features.base import ProfileFeatures
from ai.features.pipeline import Document
from ai.features.syllables import count_syllables
from ai.features.wordlists import PRONOUNS, TRANSITIONS
from ai.statistics import mean, stdev

_ANAPHORA = frozenset(
    PRONOUNS["third_singular"] + PRONOUNS["third_plural"] + PRONOUNS["demonstrative"]
)
_CONNECTIVES = frozenset(
    phrase
    for phrases in TRANSITIONS.values()
    for phrase in phrases
    if " " not in phrase
)
_CONTENT_POS = frozenset({"NOUN", "PROPN", "VERB", "ADJ", "ADV"})

# Paragraph features are only meaningful when the source kept its blank
# lines. Listed here so the scoring layer can suppress them as a block.
PARAGRAPH_FEATURES = frozenset(
    {"sentences_per_paragraph", "words_per_paragraph", "paragraph_length_cv"}
)


def extract(document: Document) -> ProfileFeatures:
    words = document.words
    sentences = document.sentences
    if not words or not sentences:
        return ProfileFeatures()

    word_count = len(words)
    syllable_total = sum(count_syllables(t.text) for t in words)
    words_per_sentence = word_count / len(sentences)
    syllables_per_word = syllable_total / word_count

    paragraph_word_counts = [
        float(len([w for w in p.split() if w.strip()])) for p in document.paragraphs
    ]
    paragraph_mean = mean(paragraph_word_counts)
    paragraph_sd = stdev(paragraph_word_counts)

    scalars = {
        "sentences_per_paragraph": len(sentences) / max(1, document.paragraph_count),
        "words_per_paragraph": paragraph_mean,
        "paragraph_length_cv": (
            (paragraph_sd / paragraph_mean)
            if (paragraph_sd is not None and paragraph_mean > 0)
            else 0.0
        ),
        "flesch_reading_ease": 206.835
        - 1.015 * words_per_sentence
        - 84.6 * syllables_per_word,
        "gunning_fog": 0.4
        * (words_per_sentence + 100.0 * _complex_word_ratio(document)),
        "lexical_overlap_adjacent": _adjacent_overlap(document),
        "anaphora_per_sentence": sum(1 for w in document.words_lower if w in _ANAPHORA)
        / len(sentences),
        "connective_per_sentence": sum(
            1 for w in document.words_lower if w in _CONNECTIVES
        )
        / len(sentences),
    }
    return ProfileFeatures(scalars=scalars)


def _complex_word_ratio(document: Document) -> float:
    """Share of words with 3+ syllables, per Gunning Fog's definition.

    Excludes proper nouns, and words that only reach three syllables through
    an -es/-ed/-ing inflection. Most implementations skip these exclusions,
    which inflates the score for any text full of names.
    """
    words = document.words
    if not words:
        return 0.0

    complex_count = 0
    for token in words:
        if token.pos_ == "PROPN":
            continue
        lowered = token.text.lower()
        syllables = count_syllables(lowered)
        if syllables < 3:
            continue
        for suffix in ("es", "ed", "ing"):
            if (
                lowered.endswith(suffix)
                and count_syllables(lowered[: -len(suffix)]) < 3
            ):
                syllables = 0
                break
        if syllables >= 3:
            complex_count += 1
    return complex_count / len(words)


def _adjacent_overlap(document: Document) -> float:
    """Mean content-word overlap between consecutive sentences.

    Coh-Metrix-style local cohesion. This is a *rate of self-repetition*, so
    it reflects how tightly a writer chains ideas rather than what the ideas
    are about - it stays topic-robust.
    """
    sentences = document.sentences
    if len(sentences) < 2:
        return 0.0

    content_sets = [
        {t.lemma_.lower() for t in s if t.pos_ in _CONTENT_POS and t.is_alpha}
        for s in sentences
    ]

    overlaps = []
    for first, second in zip(content_sets, content_sets[1:]):
        smaller = min(len(first), len(second))
        if smaller == 0:
            continue
        overlaps.append(len(first & second) / smaller)
    return mean(overlaps)

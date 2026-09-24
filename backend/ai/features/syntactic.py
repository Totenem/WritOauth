r"""Syntactic profile: sentence length, sentence patterns, clause complexity.

Built on spaCy's dependency parse rather than conjunction keyword-counting.
That matters for two features in particular: passive voice is read off the
`nsubjpass`/`auxpass` labels instead of a `be + \w+ed` regex (which fires on
"was tired" and misses reduced passives), and sentence openers use the actual
POS tag of the first token instead of guessing from `-ly`/`-ing` suffixes.
"""

from __future__ import annotations

from ai.features.base import ProfileFeatures, as_distribution
from ai.features.pipeline import Document
from ai.statistics import mean, stdev

# Dependency labels marking a subordinate clause.
_CLAUSE_DEPS = frozenset(
    {"advcl", "ccomp", "xcomp", "acl", "relcl", "csubj", "csubjpass", "pcomp"}
)

_OPENER_CLASSES = (
    "pronoun",
    "determiner",
    "subordinator",
    "coordinator",
    "adverb",
    "preposition",
    "verb",
    "noun",
    "other",
)


def extract(document: Document) -> ProfileFeatures:
    sentences = document.sentences
    lengths = [n for n in document.sentence_lengths if n > 0]
    if not sentences or not lengths:
        return ProfileFeatures()

    avg_length = mean([float(n) for n in lengths])
    sample_sd = stdev([float(n) for n in lengths])

    scalars = {
        "mean_sentence_length": avg_length,
        # Coefficient of variation: how much a writer *varies* sentence
        # length. Scale-free, and as characteristic as the mean itself -
        # the previous engine measured only the mean.
        "sentence_length_cv": (
            (sample_sd / avg_length)
            if (sample_sd is not None and avg_length > 0)
            else 0.0
        ),
        "commas_per_sentence": _char_per_sentence(document, ","),
        "clauses_per_sentence": _clauses_per_sentence(document),
        "max_dependency_depth": _mean_tree_depth(document),
        "interrogative_rate": sum(1 for s in sentences if s.text.strip().endswith("?"))
        / len(sentences),
        "exclamative_rate": sum(1 for s in sentences if s.text.strip().endswith("!"))
        / len(sentences),
        "passive_rate": _passive_rate(document),
    }

    distributions = {
        "sentence_length_bins": as_distribution(_length_bins(lengths)),
        "opener_profile": as_distribution(_opener_counts(document)),
    }
    return ProfileFeatures(scalars=scalars, distributions=distributions)


def _char_per_sentence(document: Document, char: str) -> float:
    if not document.sentences:
        return 0.0
    return document.raw.count(char) / len(document.sentences)


def _clauses_per_sentence(document: Document) -> float:
    """Subordinate clauses per sentence, from dependency labels."""
    if not document.sentences:
        return 0.0
    clauses = sum(1 for t in document.doc if t.dep_ in _CLAUSE_DEPS)
    return clauses / len(document.sentences)


def _mean_tree_depth(document: Document) -> float:
    """Mean depth of each sentence's dependency tree.

    A direct measure of syntactic embedding: deeply nested sentences and
    flat ones are a strong, topic-independent authorial habit.
    """
    depths = []
    for sentence in document.sentences:
        sentence_max = 0
        for token in sentence:
            depth = 0
            current = token
            # Walk to the root. spaCy returns a fresh Token object on every
            # `.head` access, so identity (`is`) never matches - the root
            # test must compare token indices or this loop never exits.
            while current.head.i != current.i and depth < 50:
                depth += 1
                current = current.head
            sentence_max = max(sentence_max, depth)
        depths.append(float(sentence_max))
    return mean(depths)


def _passive_rate(document: Document) -> float:
    """Passive constructions per sentence, from `nsubjpass`/`auxpass`."""
    if not document.sentences:
        return 0.0
    # One passive clause produces both an `nsubjpass` and an `auxpass`
    # token ("the report was written" -> report, was), so count distinct
    # governing verbs rather than tokens.
    heads = {t.head.i for t in document.doc if t.dep_ in ("nsubjpass", "auxpass")}
    return len(heads) / len(document.sentences)


def _length_bins(lengths: list[int]) -> dict[str, int]:
    bins = {"short": 0, "medium": 0, "long": 0}
    for n in lengths:
        if n < 10:
            bins["short"] += 1
        elif n < 25:
            bins["medium"] += 1
        else:
            bins["long"] += 1
    return bins


def _opener_counts(document: Document) -> dict[str, int]:
    """How each sentence begins, by POS tag of its first real token."""
    counts = {name: 0 for name in _OPENER_CLASSES}
    for sentence in document.sentences:
        first = next((t for t in sentence if not t.is_punct and not t.is_space), None)
        if first is None:
            continue
        counts[_classify_opener(first)] += 1
    return counts


def _classify_opener(token) -> str:  # type: ignore[no-untyped-def]
    pos = token.pos_
    if pos == "PRON":
        return "pronoun"
    if pos == "DET":
        return "determiner"
    if pos == "SCONJ":
        return "subordinator"
    if pos == "CCONJ":
        return "coordinator"
    if pos == "ADV":
        return "adverb"
    if pos == "ADP":
        return "preposition"
    if pos in ("VERB", "AUX"):
        return "verb"
    if pos in ("NOUN", "PROPN"):
        return "noun"
    return "other"

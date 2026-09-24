"""The feature registry - one definition per measured feature.

This drives extraction, scoring, weighting, the API schema and the UI
labels. Changing a weight or a prior is a one-line edit here, not a hunt
through the scoring code.

Two version numbers, and they mean different things:

* SCHEMA_VERSION    - the *shape* of the stored JSON changed.
* EXTRACTOR_VERSION - the *numbers* would come out different.

A formula tweak that leaves the shape alone still invalidates every stored
score, so both are needed.
"""

from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = 2
EXTRACTOR_VERSION = "2.0.0"

LEXICAL = "lexical"
SYNTACTIC = "syntactic"
GRAMMATICAL = "grammatical"
MECHANICAL = "mechanical"
STYLISTIC = "stylistic"
DISCOURSE = "discourse"

PROFILE_ORDER = (LEXICAL, SYNTACTIC, GRAMMATICAL, MECHANICAL, STYLISTIC, DISCOURSE)

PROFILE_LABELS = {
    LEXICAL: "Lexical",
    SYNTACTIC: "Syntactic",
    GRAMMATICAL: "Grammatical",
    MECHANICAL: "Mechanical",
    STYLISTIC: "Stylistic",
    DISCOURSE: "Discourse & Complexity",
}

# How much each profile contributes to the overall consistency score.
#
# Stylistic is weighted highest because function-word usage is the
# gold-standard authorship signal: topic-independent and unconscious.
# Grammatical is weighted lowest because its detector is low-recall,
# dialect-normative and produces sparse counts (see ai/features/grammatical.py).
PROFILE_WEIGHTS = {
    STYLISTIC: 0.30,
    SYNTACTIC: 0.20,
    LEXICAL: 0.15,
    MECHANICAL: 0.15,
    DISCOURSE: 0.12,
    GRAMMATICAL: 0.08,
}

DIRECT = "direct"
APPROXIMATION = "approximation"

SCALAR = "scalar"
COUNT = "count"
DISTRIBUTION = "distribution"


@dataclass(frozen=True)
class FeatureSpec:
    key: str
    profile: str
    kind: str
    label: str
    weight: float
    measurement: str = DIRECT
    # Expected within-author standard deviation. Used at n=1 and blended
    # away as real baseline papers accumulate.
    prior_sigma: float = 1.0
    # Smallest difference that means anything; stops a near-zero variance
    # from producing an enormous z.
    floor: float = 1e-6
    min_words: int = 0
    min_sentences: int = 0
    min_baseline_papers: int = 1
    requires_paragraphs: bool = False
    note: str = ""


def _s(key, profile, label, weight, prior, floor, **kw) -> FeatureSpec:
    return FeatureSpec(
        key=key,
        profile=profile,
        kind=SCALAR,
        label=label,
        weight=weight,
        prior_sigma=prior,
        floor=floor,
        **kw,
    )


def _c(key, profile, label, weight, **kw) -> FeatureSpec:
    return FeatureSpec(
        key=key, profile=profile, kind=COUNT, label=label, weight=weight, **kw
    )


def _d(key, profile, label, weight, prior, **kw) -> FeatureSpec:
    return FeatureSpec(
        key=key,
        profile=profile,
        kind=DISTRIBUTION,
        label=label,
        weight=weight,
        prior_sigma=prior,
        floor=1e-4,
        **kw,
    )


_TYPOGRAPHY_NOTE = "Typographic artifact - indicates the tool used, not the author."

# PRIOR_SIGMA values below are EXPERT JUDGEMENT, not measurement. There is
# no honest way to measure within-author variation before the deployment has
# data. `scripts/calibrate_engine.py` recomputes them as pooled within-
# student standard deviations once enough papers exist; until then they are
# a documented guess and must not be presented as calibrated.
FEATURES: tuple[FeatureSpec, ...] = (
    # ---------------- Lexical ----------------
    _s(
        "mattr_100",
        LEXICAL,
        "Vocabulary diversity (MATTR-100)",
        0.25,
        0.04,
        0.005,
        min_words=120,
    ),
    _s(
        "hapax_ratio_windowed",
        LEXICAL,
        "Once-only word rate",
        0.15,
        0.05,
        0.005,
        min_words=120,
    ),
    _s(
        "lexical_density",
        LEXICAL,
        "Lexical density (content words)",
        0.20,
        0.04,
        0.005,
        min_words=60,
    ),
    _s(
        "avg_word_length",
        LEXICAL,
        "Average word length",
        0.12,
        0.35,
        0.02,
        min_words=60,
        note="Correlated with syllables/word; weight split between them.",
    ),
    _s(
        "long_word_ratio",
        LEXICAL,
        "Long-word rate (7+ letters)",
        0.14,
        0.04,
        0.005,
        min_words=60,
    ),
    _s(
        "avg_syllables_per_word",
        LEXICAL,
        "Average syllables per word",
        0.08,
        0.15,
        0.01,
        measurement=APPROXIMATION,
        min_words=60,
        note="Hyphenation points approximate syllable boundaries.",
    ),
    _s(
        "latinate_suffix_ratio",
        LEXICAL,
        "Latinate-suffix rate (register)",
        0.06,
        0.03,
        0.003,
        measurement=APPROXIMATION,
        min_words=60,
    ),
    # ---------------- Syntactic ----------------
    _s(
        "mean_sentence_length",
        SYNTACTIC,
        "Average sentence length",
        0.20,
        2.5,
        0.2,
        min_sentences=5,
    ),
    _s(
        "sentence_length_cv",
        SYNTACTIC,
        "Sentence-length variability",
        0.18,
        0.12,
        0.01,
        min_sentences=5,
    ),
    _s(
        "commas_per_sentence",
        SYNTACTIC,
        "Commas per sentence",
        0.12,
        0.5,
        0.05,
        min_sentences=5,
    ),
    _s(
        "clauses_per_sentence",
        SYNTACTIC,
        "Subordinate clauses per sentence",
        0.16,
        0.3,
        0.03,
        min_sentences=5,
    ),
    _s(
        "max_dependency_depth",
        SYNTACTIC,
        "Syntactic embedding depth",
        0.14,
        0.6,
        0.05,
        min_sentences=5,
    ),
    _s(
        "passive_rate",
        SYNTACTIC,
        "Passive constructions per sentence",
        0.10,
        0.12,
        0.01,
        min_sentences=5,
    ),
    _s(
        "interrogative_rate",
        SYNTACTIC,
        "Question rate",
        0.03,
        0.05,
        0.005,
        min_sentences=8,
    ),
    _s(
        "exclamative_rate",
        SYNTACTIC,
        "Exclamation rate",
        0.03,
        0.05,
        0.005,
        min_sentences=8,
    ),
    _d(
        "sentence_length_bins",
        SYNTACTIC,
        "Sentence-length mix",
        0.02,
        0.06,
        min_sentences=8,
    ),
    _d("opener_profile", SYNTACTIC, "How sentences open", 0.02, 0.08, min_sentences=8),
    # ---------------- Grammatical ----------------
    _c(
        "subject_verb_agreement",
        GRAMMATICAL,
        "Subject-verb agreement errors",
        0.28,
        measurement=APPROXIMATION,
        min_words=100,
    ),
    _c("article_a_an", GRAMMATICAL, "a/an errors", 0.14, min_words=100),
    _c(
        "repeated_word", GRAMMATICAL, "Accidentally repeated words", 0.14, min_words=100
    ),
    _c(
        "comma_splice",
        GRAMMATICAL,
        "Comma splices",
        0.14,
        measurement=APPROXIMATION,
        min_words=100,
    ),
    _c(
        "missing_terminal_punctuation",
        GRAMMATICAL,
        "Missing sentence-end punctuation",
        0.10,
        min_words=100,
    ),
    _c(
        "run_on",
        GRAMMATICAL,
        "Run-on sentences",
        0.10,
        measurement=APPROXIMATION,
        min_words=100,
    ),
    _d(
        "grammar_error_types",
        GRAMMATICAL,
        "Which errors recur",
        0.10,
        0.12,
        min_words=200,
        measurement=APPROXIMATION,
    ),
    # ---------------- Mechanical ----------------
    _c(
        "spelling_errors",
        MECHANICAL,
        "Unrecognised words",
        0.24,
        measurement=APPROXIMATION,
        min_words=60,
        note="Unknown to the dictionary, which is not identical to misspelled.",
    ),
    _c(
        "apostrophe_omissions",
        MECHANICAL,
        "Contractions missing an apostrophe",
        0.14,
        min_words=60,
    ),
    _c(
        "homophone_confusions",
        MECHANICAL,
        "Homophone confusions",
        0.12,
        measurement=APPROXIMATION,
        min_words=60,
    ),
    _c("lowercase_i", MECHANICAL, "Lowercase personal pronoun", 0.08, min_words=60),
    _c(
        "sentence_initial_lowercase",
        MECHANICAL,
        "Sentences starting lowercase",
        0.10,
        min_words=60,
    ),
    _c(
        "possessives",
        MECHANICAL,
        "Possessive apostrophes",
        0.08,
        min_words=100,
    ),
    _s("all_caps_ratio", MECHANICAL, "ALL-CAPS rate", 0.04, 0.01, 0.002, min_words=100),
    _c(
        "missing_space_after_punct",
        MECHANICAL,
        "Missing space after punctuation",
        0.06,
        min_words=100,
    ),
    _d("punctuation_profile", MECHANICAL, "Punctuation mix", 0.10, 0.06, min_words=100),
    _d(
        "spelling_error_types",
        MECHANICAL,
        "Which spelling slips recur",
        0.04,
        0.15,
        min_words=200,
        measurement=APPROXIMATION,
    ),
    # --- typography sub-block: describes the editor, not the author ---
    _s(
        "curly_quote_ratio",
        MECHANICAL,
        "Curly vs straight quotes",
        0.03,
        0.10,
        0.02,
        min_words=100,
        measurement=APPROXIMATION,
        note=_TYPOGRAPHY_NOTE,
    ),
    _s(
        "double_space_after_period_ratio",
        MECHANICAL,
        "Double-spacing after a period",
        0.03,
        0.08,
        0.01,
        min_words=100,
        measurement=APPROXIMATION,
        note=_TYPOGRAPHY_NOTE,
    ),
    _c(
        "space_before_punct",
        MECHANICAL,
        "Space before punctuation",
        0.04,
        min_words=100,
        measurement=APPROXIMATION,
        note=_TYPOGRAPHY_NOTE,
    ),
    # ---------------- Stylistic ----------------
    _d(
        "function_word_freqs",
        STYLISTIC,
        "Function-word usage",
        0.34,
        0.035,
        min_words=100,
        note="The strongest authorship signal: topic-independent and unconscious.",
    ),
    _s(
        "function_word_ratio",
        STYLISTIC,
        "Function-word share",
        0.12,
        0.03,
        0.005,
        min_words=100,
    ),
    _s(
        "transition_rate_per_1k",
        STYLISTIC,
        "Transitions per 1k words",
        0.10,
        6.0,
        0.5,
        min_words=100,
    ),
    _s(
        "pronoun_rate_per_1k",
        STYLISTIC,
        "Pronouns per 1k words",
        0.10,
        12.0,
        1.0,
        min_words=100,
    ),
    _s(
        "contraction_preference",
        STYLISTIC,
        "Contraction preference",
        0.10,
        0.12,
        0.01,
        min_words=100,
    ),
    _d(
        "transition_categories",
        STYLISTIC,
        "Which transitions are preferred",
        0.08,
        0.10,
        min_words=150,
    ),
    _d(
        "pronoun_categories", STYLISTIC, "Pronoun person mix", 0.08, 0.08, min_words=150
    ),
    _s(
        "habitual_ngram_coverage",
        STYLISTIC,
        "Habitual phrasing retained",
        0.08,
        0.18,
        0.02,
        min_words=150,
        min_baseline_papers=2,
    ),
    # ---------------- Discourse & Complexity ----------------
    _s(
        "flesch_reading_ease",
        DISCOURSE,
        "Flesch Reading Ease",
        0.20,
        7.0,
        0.5,
        measurement=APPROXIMATION,
        min_words=100,
        note="Syllable counts are approximate; FK Grade omitted (~-0.99 correlated).",
    ),
    _s(
        "gunning_fog",
        DISCOURSE,
        "Gunning Fog index",
        0.16,
        2.0,
        0.2,
        measurement=APPROXIMATION,
        min_words=100,
    ),
    _s(
        "lexical_overlap_adjacent",
        DISCOURSE,
        "Sentence-to-sentence cohesion",
        0.18,
        0.07,
        0.01,
        min_sentences=5,
    ),
    _s(
        "connective_per_sentence",
        DISCOURSE,
        "Connectives per sentence",
        0.12,
        0.15,
        0.02,
        min_sentences=5,
    ),
    _s(
        "anaphora_per_sentence",
        DISCOURSE,
        "Referring pronouns per sentence",
        0.10,
        0.35,
        0.03,
        measurement=APPROXIMATION,
        min_sentences=5,
        note="Counts candidate anaphors; no coreference resolution.",
    ),
    _s(
        "sentences_per_paragraph",
        DISCOURSE,
        "Sentences per paragraph",
        0.10,
        1.2,
        0.1,
        requires_paragraphs=True,
    ),
    _s(
        "words_per_paragraph",
        DISCOURSE,
        "Words per paragraph",
        0.08,
        25.0,
        2.0,
        requires_paragraphs=True,
    ),
    _s(
        "paragraph_length_cv",
        DISCOURSE,
        "Paragraph-length variability",
        0.06,
        0.20,
        0.02,
        requires_paragraphs=True,
    ),
)

BY_KEY: dict[str, FeatureSpec] = {spec.key: spec for spec in FEATURES}


def for_profile(profile: str) -> tuple[FeatureSpec, ...]:
    return tuple(spec for spec in FEATURES if spec.profile == profile)

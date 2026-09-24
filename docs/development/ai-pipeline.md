# Authorship Engine Developer Guide

## What it does

The engine answers one question: **does this submission look like the same
person who wrote this student's baseline papers?**

It is not an AI-content detector and does not try to be. It compares a
submission against *that student's own* writing, across six linguistic
profiles.

There is **no LLM**. Scores are deterministic and reproducible: the same
text always produces the same numbers. `spaCy` (`en_core_web_sm`) supplies
POS tags, a dependency parse and morphology; everything above that is
arithmetic.

## The six profiles

| Profile | What it measures | Weight |
|---|---|---|
| Stylistic | Function words, transitions, pronouns, contractions, habitual phrasing | 0.30 |
| Syntactic | Sentence length and variation, clause complexity, dependency depth, passives, sentence openers | 0.20 |
| Lexical | Vocabulary diversity (MATTR-100), lexical density, word length, register | 0.15 |
| Mechanical | Spelling, punctuation, capitalisation, apostrophes | 0.15 |
| Discourse & Complexity | Paragraph shape, cohesion, readability | 0.12 |
| Grammatical | Error rate and which errors recur | 0.08 |

Stylistic carries the most weight because function-word usage is the
gold-standard authorship signal in the literature: topic-independent and
largely unconscious. Grammatical carries the least — see its limits below.

Weights, priors and gates all live in one place:
`backend/ai/features/registry.py`. Changing a weight is a one-line edit
there, not a hunt through the scoring code.

## Services

| Service | File | Responsibility |
|---|---|---|
| `FingerprintService` | `ai/fingerprint_service.py` | Parse once with spaCy, run the six extractors |
| feature extractors | `ai/features/{lexical,syntactic,grammatical,mechanical,stylistic,discourse}.py` | One profile each |
| `SpellingService` | `ai/spelling_service.py` | Dictionary lookups and edit-1 error typing |
| `ProfileEngine` | `ai/profile_engine.py` | Aggregate baselines into mean/stdev/distribution |
| `ScoringService` | `ai/scoring_service.py` | Compare submission to profile, aggregate to a score |
| `ExplanationService` | `ai/explanation_service.py` | Deterministic teacher-facing sentences |
| `AIOrchestrator` | `ai/orchestrator.py` | Wire it together, persist the result |
| statistics | `ai/statistics.py` | Shrinkage z, Poisson z, JSD, kernel, weighted RMS |

## How comparison works

Three feature kinds need three different statistics. Using one for all of
them is what the previous engine got wrong.

**Scalars** (means and ratios) use a shrinkage z-score. A plain sample
stdev is unusable at small n: two baseline papers landing 0.3 words apart
on mean sentence length give σ = 0.21, so a perfectly normal third paper
would score |z| = 20. The estimate blends the student's own variance with a
per-feature prior, so n=1 is fully defined and n≥10 ignores the prior.

**Counts** (grammar and spelling errors) use an Anscombe-transformed
Poisson z. The common case is zero errors in every baseline paper, where a
Gaussian z is undefined. This also handles the case that matters most for
ghostwriting — an established error habit *disappearing* — which a naive
implementation scores as a perfect match.

**Distributions** (punctuation mix, sentence openers, function words) use
Jensen-Shannon divergence, scaled by the student's own paper-to-paper
spread. That spread is measurable from just two baseline papers, which
scalars can't manage.

Every feature ends up as a z. One kernel maps z → 0-100:
`100 · exp(−0.5·(|z|/2)²)`. Profiles aggregate their features by **weighted
RMS in z-space**, not by averaging sub-scores — a weighted mean of scores
dilutes exactly the signal this product exists to find (seven features at
100 and one at 20 averages to 90).

Scoring uses `|z|`; the sign is kept so the explanation can say which way a
feature moved without that asymmetry leaking into the arithmetic.

## Gates and suppression

Every feature declares a minimum (words, sentences, baseline papers). Below
it, the feature is marked unavailable with a reason, excluded from the
maths, and the remaining weights renormalise — rather than being computed as
0.0 and scored as a deviation.

Typography features (curly quotes, spacing) describe the *editor*, not the
writer. They are suppressed when a submission's `source_format` differs
from the baselines', so a student isn't flagged for switching from a
textarea to a PDF.

## Honest limits

- **The Grammatical profile is high-precision, low-recall.** It catches a
  minority of genuine errors and cannot detect most things needing semantic
  understanding. It is also dialect-normative. An absolute error count from
  it is **not** a measure of a student's grammatical ability and must never
  be presented as one. A real grammar checker means `language_tool_python`,
  which needs a JVM — out of scope.
- **Priors and weights are expert judgement, not measurement.** There is no
  honest way to measure within-author variation before a deployment has
  data. They are labelled as such in the code.
- **Spelling means "unknown to the dictionary"**, not "misspelled". Proper
  nouns are filtered out, which also drops some real misspellings that spaCy
  mistags as PROPN. The same filter runs on both sides, so the bias cancels.

## Versioning and rebuilds

`schema_version` tracks the *shape* of stored JSON; `extractor_version`
tracks whether the *numbers* would come out different. A formula tweak that
leaves the shape alone still invalidates stored scores, so both exist.

`feature_vectors`, `baseline_profiles` and `analysis_results` are all
derived from `papers.content`. To regenerate them:

```bash
cd backend && python -m scripts.rebuild_analysis          # everything
cd backend && python -m scripts.rebuild_analysis --dry-run
```

Reading an analysis stored by an older engine version raises
`StaleAnalysisError` → HTTP 409, rather than coercing a v1 blob into the
current models.

## Setup

```bash
pip install -r requirements.txt   # includes en_core_web_sm as a pinned wheel
```

No model download at runtime and no network access needed. spaCy, thinc and
blis are pinned together because they must all resolve to prebuilt wheels on
linux aarch64 — `thinc`'s latest release publishes none.

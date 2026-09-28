# Authorship Models: Neural Style Verification

> **Status:** implemented (extractor v3.0.0), pending validation (§8).
> **Audience:** project developers, thesis readers and competition reviewers.
> **Companion doc:** [ai-pipeline.md](ai-pipeline.md) covers the six stylometric profiles.

## 1. Summary

WritOauth answers one question per submission: **"Is this paper consistent
with the way this student has written before?"** This is *authorship
verification*. It is not AI-text detection and not a grading exercise.

The engine is a hybrid of a learned model and interpretable statistics:

| Layer | What it contributes |
|---|---|
| **LUAR style embedding (AI)** | A learned 512-dimension "writing fingerprint", trained on about a million authors. It captures style patterns that hand-built features miss. |
| **Six stylometric profiles (statistics)** | Interpretable evidence: *which* habits changed (sentence length, contractions, function words, spelling slips…). |
| **Explanation template** | Turns both into a plain-language summary for the teacher. |

The neural model supplies **detection power**; the statistical profiles
supply **explainability**. Neither verdict is automatic: a flag asks the
teacher to review, and the teacher decides.

## 2. Why a neural model

Stylometry has a long track record. It goes back to Mosteller & Wallace's
study of the *Federalist Papers* [1] and is surveyed in Stamatatos [2]. But
hand-built features have limits:

- They only measure what someone thought to measure.
- The features treat each habit as independent, while real style shows up as
  *combinations* of habits.
- Our weights and priors are expert estimates, not learned from data
  (`backend/ai/features/registry.py`).

Neural authorship representations learned from large numbers of authors
outperform statistical methods at scale [3]. A pre-trained model brings that
learned knowledge to every student without us needing training data.

## 3. Model selection

Candidates evaluated (all open weights on Hugging Face and CPU-friendly):

| Model | Params | License | Built for | Verdict |
|---|---|---|---|---|
| **`rrivera1849/LUAR-MUD`** [3][4] | 82.5M | Apache-2.0 | Author verification from **multiple documents per author** | **Chosen** |
| `StyleDistance/styledistance` [5][6] | ~125M | MIT | Content-independent sentence-level style similarity | Strong alternative; sentence-level, not author-level |
| `AnnaWegmann/Style-Embedding` [7][8] | ~125M | — | Style representations with content control | Older; superseded by StyleDistance |
| `desklib/ai-text-detector-academic-v1.01` [9] | ~435M | MIT | Binary "AI-generated?" classifier | Different question; possible future *separate* signal (§9) |
| Binoculars (two small LLMs, e.g. Qwen2.5-0.5B) [10] | 2 × 0.5B | Apache-2.0 | Zero-shot AI-text detection | Same as above; slower, and accuracy at 0.5B is unproven |

**Why LUAR:**

1. **It fits our data shape.** LUAR takes an *episode*, a set of text
   segments by one author, and returns one author vector.
2. **It is trained for verification.** It was trained contrastively so that
   texts by the same author embed close together and texts by different
   authors embed far apart, across about 1M Reddit users (the Million User
   Dataset) [3].
3. **It is small:** a 6-layer DistilRoBERTa backbone
   (`paraphrase-distilroberta-base-v1`), 768 hidden units, projected to a
   512-dimension embedding [4]. It runs on a laptop CPU.
4. **It is permissively licensed and widely used:** Apache-2.0, 130k+
   monthly downloads.

**Why not an LLM judge (e.g. Qwen-Instruct)?** LLMs asked "did this student
write this?" give answers that aren't reproducible, can't be calibrated, and
aren't grounded in the student's baseline. An earlier design included Qwen
via Ollama; it was never implemented and was removed. See §9 for the one role
an LLM could safely play.

**Why not the previous embedding (`BAAI/bge-small-en-v1.5`)?** It is a
*semantic* model: it measures topic, not style. A class writing to one prompt
all looked alike, which produced systematic false negatives. LUAR's training
objective separates authors *regardless* of topic, and we add a second
protection by scoring against each student's own variation (§5.2).

## 4. How LUAR works

```
paper text ──► RoBERTa BPE tokens ──► 32-token segments (≤ 64, sampled evenly)
                                               │
                         DistilRoBERTa encodes each segment (6 layers)
                                               │
                 attention pooling across segments ─► linear projection
                                               │
                               512-d author style vector (L2-normalised)
```

- **Input:** tensor shape `(episodes, segments, tokens)`. We pass one
  episode per paper: `(1, n_segments, 32)` [4]. The model was trained on
  32-token segments, so we match that.
- **Output:** `(1, 512)`. Cosine similarity between vectors roughly means
  "how likely the same author".
- **Loading:**
  - `AutoModel.from_pretrained(model, revision=<sha>, trust_remote_code=True, use_safetensors=True)`.
  - The architecture ships as custom code in the model repo, so the revision
    is **pinned to a reviewed commit**: `f1db50251805ed69b43cf4f72ea2f0e231f36a1c`.
    It was reviewed and found to be pure model definition, with no network,
    file or process access.
  - Weights load from safetensors, never pickle.
- **Dependencies:** `backend/requirements-ml.txt`, which has CPU-only
  `torch`, `transformers` and `einops`.

## 5. How WritOauth scores with LUAR

### 5.1 Embedding each paper
`AIOrchestrator._extract_and_store_features` calls `NeuralStyleService.embed()`
for every baseline and submission. The vector is stored next to the
stylometric features in `feature_vectors.features`:

```json
"neural_style": {"model": "rrivera1849/LUAR-MUD@f1db50251805", "vector": [512 floats]}
```

The model id travels with the vector because vectors from different model
revisions live in different spaces. They are never compared, and the
profile reports "different AI model version" instead.

### 5.2 Building the baseline (`profile_engine._aggregate_neural`)
For baseline vectors `b₁…bₙ`:

- **Centroid** `c = normalise(mean(bᵢ))`: the student's "average
  fingerprint".
- **Leave-one-out (LOO) distances** `dᵢ = 1 − cos(bᵢ, centroid of the other
  n−1 papers)`: how far a *genuine* paper by this student typically sits
  from the rest of their work.
- The mean and standard deviation of the LOO distances are stored alongside
  the centroid.

The LOO step is the key design choice. It makes the score **relative to this
student**:
- A student who writes very differently across assignments gets a wide
  tolerance.
- A very consistent student gets a narrow one.
- A topic shift that affects *all* of a student's papers is already built
  into their tolerance.

### 5.3 Scoring a submission (`scoring_service._score_neural`)

```
d_sub = 1 − cos(submission, c)
σ     = shrunk_sigma(LOO stdev, n, prior σ₀ = 0.08, floor 0.02)
z     = max(0, (d_sub − mean LOO distance) / σ)
score = 100 · exp(−½ (z/2)²)
```

- `shrunk_sigma` is the same prior shrinkage the scalar features use (see
  `ai/statistics.py`), with prior strength 3 papers.
- The kernel is the same one every other feature uses.
- **One-sided:** a submission *closer* than usual to the student's style is
  not evidence of anything, so z is clamped at 0.
- **Gates:** at least 60 words in the submission and **at least 2 baseline
  papers** (LOO needs two). Otherwise the profile is marked unavailable, with
  the reason shown to the teacher.
- σ₀ and the floor are expert estimates until the evaluation (§8) calibrates
  them.

### 5.4 Combining with the six profiles
LUAR is treated as the primary signal: the neural profile is weighted 0.80.
The six stylometric profiles are kept mainly for their explanatory value and
share the remaining 0.20 in their original ratios:

| Profile | Old weight | New weight |
|---|---|---|
| **AI Style Fingerprint (LUAR)** | — | **0.800** |
| Stylistic | 0.30 | 0.060 |
| Syntactic | 0.20 | 0.040 |
| Lexical | 0.15 | 0.030 |
| Mechanical | 0.15 | 0.030 |
| Discourse | 0.12 | 0.024 |
| Grammatical | 0.08 | 0.016 |

At this weight the overall score tracks LUAR closely and the stylometric
profiles mostly explain *why* rather than move the number much themselves.
That tradeoff is deliberate for now - see the calibration note in §8 - but
it does mean a false positive or negative from LUAR alone is much less
diluted by the six profiles than it would be at, say, 0.35.

- The overall score is the same weighted-RMS of profile z-scores as before.
  It is flagged below `ANALYSIS_FLAG_THRESHOLD` (75).
- **Graceful fallback:** if the model is disabled, still loading, missing its
  dependencies or failed to download, the neural profile is "not measured"
  and the weights renormalise over the six. Weighted RMS doesn't change when
  every weight is scaled by the same factor, so this reproduces the pre-LUAR
  engine exactly. A test asserts it.

### 5.5 Explanation
When the LUAR profile is among the top three drivers, the report says:

> "The largest difference is the overall writing fingerprint: the AI style
> model places this paper unusually far from the student's earlier work."

The stylometric drivers that follow say *what* changed. In the report UI the
profile carries an "AI model" badge and reads "further than usual" rather
than "higher".

## 6. Implementation map

| File | Role |
|---|---|
| `backend/ai/neural_style_service.py` | Lazy, thread-safe singleton loader; segmenting; `embed()`; vector maths (`centroid`, `cosine_distance`, `leave_one_out_distances`) |
| `backend/config/settings.py` | `NEURAL_STYLE_ENABLED`, `NEURAL_STYLE_MODEL`, `NEURAL_STYLE_REVISION` |
| `backend/main.py` | Background warm-up at startup, so the first upload doesn't wait for the model |
| `backend/ai/orchestrator.py` | Stores the vector alongside the stylometric features |
| `backend/ai/profile_engine.py` | Centroid and LOO aggregation |
| `backend/ai/features/registry.py` | `NEURAL` profile, `luar_distance` feature, `one_sided`, weights, `EXTRACTOR_VERSION = "3.0.0"` |
| `backend/ai/scoring_service.py` | `_score_neural`; profile-level suppression reason |
| `backend/ai/explanation_service.py` | Plain-language sentence for the neural driver |
| `backend/requirements-ml.txt`, `Dockerfile`, `docker-compose.yml` | CPU torch layer; `INSTALL_ML` build arg; `hf_cache` volume |
| `frontend/types/analysis.ts`, `features/analysis/ScoreBreakdown.tsx` | `neural_style` profile (optional on old analyses), "AI model" badge |
| `backend/tests/test_ai/test_neural_style.py` | Fake-embedder tests of the maths, scoring, fallback and end to end; opt-in real-model test |

`SCHEMA_VERSION` stays at 2: the stored JSON shape didn't change, because
`profiles` is a dictionary that gained a key. Analyses produced before v3.0.0
still render, just without the neural profile, until
`python -m scripts.rebuild_analysis` recomputes them.

## 7. Requirements and data guidance

| Quantity | Guidance |
|---|---|
| Baseline papers | ≥ 2 for the neural profile; ≥ 3 before the report stops warning about a thin profile; **≥ 5 recommended** (also maxes out baseline strength) |
| Words per paper | ≥ 60 for the LUAR gate; ≥ 200 for every stylometric feature to be measured |
| Segments | Papers are cut into 30-token segments, up to 64 (~1,500 words). Longer papers are sampled evenly across their length |
| Runtime | Model ~330 MB on disk; time per paper on a laptop CPU **to be measured** (§8) |
| Hosting | Local Docker demo. The model downloads once into the `hf_cache` volume |

## 8. Validation plan

The claims above need numbers before they're presented as results:

- **Dataset:** for N volunteer students, take real essays plus (a)
  ChatGPT-written essays on the same prompts and (b) essays by *other*
  students on the same prompts.
- **Method:** hold out one real essay per student and score all three kinds.
- **Metrics:** ROC-AUC and false-positive rate at threshold 75, reported for
  stylometry only, LUAR only and the hybrid.
- **Calibrate** σ₀, the floor and the 0.80 weight from these results - at
  this weight in particular, an uncalibrated σ₀ has an outsized effect on
  the overall score.
- **Measure** embedding latency per paper.

Run the opt-in real-model test with
`RUN_NEURAL_MODEL_TESTS=1 pytest tests/test_ai/test_neural_style.py`.

## 9. Limitations and ethics

- **Domain shift.** LUAR was trained on Reddit comments. Its own authors
  report that transfer between domains is uneven: strong for some pairs of
  domains, weak for others [3]. Student essays are a new domain, which is
  why we score against each student's LOO spread rather than a fixed cutoff,
  and why §8 matters.
- **Change is not misconduct.** Growth, a different genre, a writing centre
  visit or Grammarly can all move a fingerprint. Flags prompt a
  conversation, not a sanction.
- **Fairness.** AI-text detectors misclassify non-native English writing as
  AI-generated at very high rates [11]. Our approach compares a student
  *only to themselves*, which avoids penalising a style that differs from
  the norm. Any future AI-text detector (desklib [9], Binoculars [10]) will
  be shown as a separate advisory signal, never mixed into this score.
- **Privacy.** Models run locally, so student text never leaves the server.
  Embeddings are derived data and are deleted with the paper.
- **Supply chain.** `trust_remote_code` executes model-repo code. The
  revision is pinned and reviewed, weights load from safetensors, and
  upgrades are deliberate: bump `NEURAL_STYLE_REVISION` and `transformers`
  together, re-review, then rebuild.
- **Possible LLM role (future):** a small instruct model such as
  Qwen2.5-1.5B could reword the explanation. It would only receive the
  computed evidence and would never produce the score.

## 10. References

1. F. Mosteller & D. L. Wallace. *Inference and Disputed Authorship: The Federalist.* Addison-Wesley, 1964.
2. E. Stamatatos. "A Survey of Modern Authorship Attribution Methods." *JASIST* 60(3), 2009.
3. R. A. Rivera-Soto, O. Miano, J. Ordonez, B. Chen, A. Khan, M. Bishop, N. Andrews. "Learning Universal Authorship Representations." *EMNLP 2021*, pp. 913–919. https://aclanthology.org/2021.emnlp-main.70/ · code: https://github.com/llnl/luar
4. LUAR-MUD model card and config. https://huggingface.co/rrivera1849/LUAR-MUD
5. A. Patel et al. "StyleDistance: Stronger Content-Independent Style Embeddings with Synthetic Parallel Examples." *NAACL 2025*. https://arxiv.org/abs/2410.12757
6. StyleDistance model card. https://huggingface.co/StyleDistance/styledistance
7. A. Wegmann, M. Schraagen, D. Nguyen. "Same Author or Just Same Topic? Towards Content-Independent Style Representations." *RepL4NLP 2022*. https://arxiv.org/abs/2204.04907
8. Style-Embedding model card. https://huggingface.co/AnnaWegmann/Style-Embedding
9. desklib AI text detector (academic). https://huggingface.co/desklib/ai-text-detector-academic-v1.01
10. A. Hans et al. "Spotting LLMs With Binoculars: Zero-Shot Detection of Machine-Generated Text." *ICML 2024*. https://arxiv.org/abs/2401.12070
11. W. Liang, M. Yuksekgonul, Y. Mao, E. Wu, J. Zou. "GPT detectors are biased against non-native English writers." *Patterns* 4(7), 2023. https://arxiv.org/abs/2304.02819

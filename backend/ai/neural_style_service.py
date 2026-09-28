"""Neural authorship embeddings from LUAR (Rivera-Soto et al., EMNLP 2021).

LUAR ("Learning Universal Authorship Representations") maps an *episode* - a
set of text segments by one author - to a single 512-d style vector. It was
trained contrastively across ~1M Reddit authors so that same-author episodes
land close together regardless of topic. That makes it an authorship model,
unlike the `bge-small` semantic embedding this engine previously used and
removed (see ai/orchestrator.py): that one measured what a text was *about*.

Each paper is embedded on its own: its token stream is cut into short
segments (the model was trained on 32-token segments), and those segments
form the episode. The profile engine then compares a submission's vector
with the student's baseline vectors - see docs/development/authorship-models.md.

Everything here degrades gracefully. torch/transformers are imported lazily,
and if they're missing, the model can't be fetched, or the feature is
switched off (NEURAL_STYLE_ENABLED=false), `embed()` returns None and the
engine scores with the six stylometric profiles alone.

Security: the LUAR architecture ships as custom code in the model repo
(`trust_remote_code=True`). The revision is pinned to a reviewed commit and
weights load from safetensors, so neither an upstream push nor a pickle can
change what runs here.
"""

from __future__ import annotations

import logging
import math
import threading
from functools import lru_cache
from typing import Any, Protocol

from config.settings import get_settings

logger = logging.getLogger(__name__)

# LUAR-MUD was trained on 32-token segments; matching that keeps inputs
# in-distribution. Two of the 32 are the <s> and </s> special tokens.
SEGMENT_TOKENS = 32
# Cap on segments per paper. 64 x 30 content tokens covers ~1,500 words -
# a long essay - and longer papers are sampled evenly across their length
# rather than truncated, so the ending counts as much as the opening.
MAX_SEGMENTS = 64
# Characters tokenized at most. Bounds tokenizer work on pathological input;
# far more than MAX_SEGMENTS can use.
_MAX_CHARS = 60_000


class StyleEmbedder(Protocol):
    """What the orchestrator needs - satisfied by NeuralStyleService and by
    the deterministic fake the test suite injects."""

    model_id: str

    def embed(self, text: str) -> list[float] | None: ...


class NeuralStyleService:
    def __init__(self, model_name: str, revision: str, enabled: bool = True) -> None:
        self.model_name = model_name
        self.revision = revision
        self.enabled = enabled
        self.model_id = f"{model_name}@{revision[:12]}"
        self._model: Any = None
        self._tokenizer: Any = None
        self._failed = False
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return self._ensure_loaded()

    def embed(self, text: str) -> list[float] | None:
        """L2-normalised 512-d style vector for one paper, or None when the
        model is unavailable or the text has no tokens."""
        if not text.strip() or not self._ensure_loaded():
            return None

        import torch

        ids = self._tokenizer(
            text[:_MAX_CHARS], add_special_tokens=False, verbose=False
        )["input_ids"]
        width = SEGMENT_TOKENS - 2
        segments = [ids[i : i + width] for i in range(0, len(ids), width)]
        segments = [s for s in _sample_evenly(segments, MAX_SEGMENTS) if s]
        if not segments:
            return None

        batch = self._tokenizer.pad(
            {
                "input_ids": [
                    self._tokenizer.build_inputs_with_special_tokens(s)
                    for s in segments
                ]
            },
            padding="max_length",
            max_length=SEGMENT_TOKENS,
            return_tensors="pt",
        )
        # (episodes=1, segments, tokens) - one author episode per paper.
        input_ids = batch["input_ids"].unsqueeze(0)
        attention_mask = batch["attention_mask"].unsqueeze(0)

        with torch.inference_mode():
            vector = self._model(input_ids=input_ids, attention_mask=attention_mask)
        return normalize([float(x) for x in vector[0].tolist()])

    def _ensure_loaded(self) -> bool:
        if not self.enabled or self._failed:
            return False
        if self._model is not None:
            return True
        with self._lock:
            if self._model is not None:
                return True
            try:
                import torch
                from transformers import AutoModel, AutoTokenizer

                torch.set_grad_enabled(False)
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name, revision=self.revision
                )
                model = AutoModel.from_pretrained(
                    self.model_name,
                    revision=self.revision,
                    trust_remote_code=True,
                    use_safetensors=True,
                )
                model.eval()
                self._model = model
                logger.info("Loaded neural style model %s", self.model_id)
            except Exception:  # noqa: BLE001 - any failure means "run without it"
                logger.exception(
                    "Neural style model %s unavailable; scoring with the "
                    "stylometric profiles only",
                    self.model_id,
                )
                self._failed = True
                return False
        return True


@lru_cache
def get_neural_style_service() -> NeuralStyleService:
    """Process-wide instance: the model is loaded once, on first use, not
    per request."""
    settings = get_settings()
    return NeuralStyleService(
        model_name=settings.neural_style_model,
        revision=settings.neural_style_revision,
        enabled=settings.neural_style_enabled,
    )


# ----------------------------------------------------------------------
# Vector maths - plain Python so the profile engine and scorer can use it
# without importing torch.
# ----------------------------------------------------------------------


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return list(vector)
    return [x / norm for x in vector]


def centroid(vectors: list[list[float]]) -> list[float]:
    """Mean direction of unit vectors - the student's average fingerprint."""
    dims = len(vectors[0])
    summed = [sum(v[d] for v in vectors) for d in range(dims)]
    return normalize(summed)


def cosine_distance(a: list[float], b: list[float]) -> float:
    """1 - cosine similarity, for unit vectors. 0 = identical direction."""
    dot = sum(x * y for x, y in zip(a, b))
    return 1.0 - max(-1.0, min(1.0, dot))


def leave_one_out_distances(vectors: list[list[float]]) -> list[float]:
    """Distance from each vector to the centroid of all the *others*.

    This is how far a genuine paper by this student sits from the rest of
    their work, and it is the natural scale for judging a new submission. A
    student whose writing varies a lot between assignments gets a wide
    tolerance; a very consistent one gets a narrow one.
    """
    if len(vectors) < 2:
        return []
    return [
        cosine_distance(vector, centroid(vectors[:i] + vectors[i + 1 :]))
        for i, vector in enumerate(vectors)
    ]


def _sample_evenly(items: list[Any], limit: int) -> list[Any]:
    if len(items) <= limit:
        return items
    step = len(items) / limit
    return [items[int(i * step)] for i in range(limit)]

from collections.abc import Callable
from typing import ClassVar

from config.settings import get_settings


class EmbeddingService:
    """Wraps a local, in-process embedding model.

    Uses `fastembed` (ONNX runtime, CPU-only, no torch dependency) so
    embeddings are computed in-process instead of calling out to a
    separately-hosted Ollama server. The model is expensive to load, so it's
    loaded once per process and cached on the class (shared across every
    instance), not per call and not per instance.

    For tests: pass `embed_fn` to bypass the real model entirely (recommended
    for anything except a dedicated, opt-in integration test), e.g.:

        EmbeddingService(embed_fn=lambda text: [0.1, 0.2, 0.3])
    """

    _model: ClassVar[object | None] = None

    def __init__(
        self,
        model_name: str | None = None,
        embed_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._model_name = model_name or get_settings().embedding_model
        self._embed_fn = embed_fn

    def _get_model(self) -> object:
        if EmbeddingService._model is None:
            from fastembed import TextEmbedding

            EmbeddingService._model = TextEmbedding(model_name=self._model_name)
        return EmbeddingService._model

    def embed(self, content: str) -> list[float]:
        if self._embed_fn is not None:
            return self._embed_fn(content)

        model = self._get_model()
        vectors = list(model.embed([content]))  # type: ignore[attr-defined]
        return [float(x) for x in vectors[0]]

import os

import pytest

from ai.embedding_service import EmbeddingService


def test_embed_uses_injected_embed_fn() -> None:
    service = EmbeddingService(embed_fn=lambda content: [float(len(content)), 1.0])

    result = service.embed("hello")

    assert result == [5.0, 1.0]


def test_embed_fn_receives_the_content_passed_in() -> None:
    seen: list[str] = []

    def _record_and_embed(content: str) -> list[float]:
        seen.append(content)
        return [0.0]

    service = EmbeddingService(embed_fn=_record_and_embed)

    service.embed("some text")

    assert seen == ["some text"]


@pytest.mark.skipif(
    not os.environ.get("RUN_FASTEMBED_INTEGRATION_TEST"),
    reason=(
        "Loads the real fastembed model (downloads ONNX weights over the "
        "network on first use) - opt in with RUN_FASTEMBED_INTEGRATION_TEST=1"
    ),
)
def test_embed_with_real_model_returns_a_vector() -> None:
    service = EmbeddingService()

    result = service.embed("A short sample sentence.")

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(x, float) for x in result)

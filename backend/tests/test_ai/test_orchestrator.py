import pytest

from ai.orchestrator import AIOrchestrator
from ai.fingerprint_service import FingerprintService
from ai.embedding_service import EmbeddingService
from ai.retrieval_service import RetrievalService
from ai.scoring_service import ScoringService
from ai.explanation_service import ExplanationService
from ai.profile_engine import ProfileEngine
from llm.langchain_pipeline import LangChainPipeline


def _make_orchestrator() -> AIOrchestrator:
    return AIOrchestrator(
        fingerprint=FingerprintService(),
        embedding=EmbeddingService(),
        retrieval=RetrievalService(),
        scoring=ScoringService(),
        explanation=ExplanationService(),
        profile=ProfileEngine(),
        langchain=LangChainPipeline(),
    )


def test_analyze_raises_not_implemented() -> None:
    orchestrator = _make_orchestrator()
    with pytest.raises(NotImplementedError):
        orchestrator.analyze("sample text", student_id=1)


def test_fingerprint_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        FingerprintService().extract("sample text")


def test_embedding_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        EmbeddingService().embed("sample text")

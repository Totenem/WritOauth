from ai.embedding_service import EmbeddingService
from ai.explanation_service import ExplanationService
from ai.fingerprint_service import FingerprintService
from ai.profile_engine import ProfileEngine
from ai.retrieval_service import RetrievalService
from ai.scoring_service import ScoringService
from llm.langchain_pipeline import LangChainPipeline


class AIOrchestrator:
    def __init__(
        self,
        fingerprint: FingerprintService,
        embedding: EmbeddingService,
        retrieval: RetrievalService,
        scoring: ScoringService,
        explanation: ExplanationService,
        profile: ProfileEngine,
        langchain: LangChainPipeline,
    ) -> None:
        self.fingerprint = fingerprint
        self.embedding = embedding
        self.retrieval = retrieval
        self.scoring = scoring
        self.explanation = explanation
        self.profile = profile
        self.langchain = langchain

    def analyze(self, paper_content: str, student_id: int) -> dict:
        raise NotImplementedError

from sqlalchemy.orm import Session

from ai.embedding_service import EmbeddingService
from ai.explanation_service import ExplanationService
from ai.fingerprint_service import FingerprintService
from ai.orchestrator import AIOrchestrator
from ai.profile_engine import ProfileEngine
from ai.retrieval_service import RetrievalService
from ai.scoring_service import ScoringService
from application.repositories.paper_repository import (
    PaperReferenceIntegrityError,
    PaperRepository,
)
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate, PaperResponse


def _build_default_orchestrator() -> AIOrchestrator:
    return AIOrchestrator(
        fingerprint=FingerprintService(),
        embedding=EmbeddingService(),
        retrieval=RetrievalService(),
        scoring=ScoringService(),
        explanation=ExplanationService(),
        profile=ProfileEngine(),
    )


class PaperNotFoundError(Exception):
    def __init__(self, paper_id: int) -> None:
        self.paper_id = paper_id
        super().__init__(f"Paper {paper_id} not found")


class PaperInvalidReferenceError(Exception):
    def __init__(self, student_id: int, subject_id: int) -> None:
        self.student_id = student_id
        self.subject_id = subject_id
        super().__init__(f"Student {student_id} or subject {subject_id} does not exist")


class PaperService:
    def __init__(self, db: Session, orchestrator: AIOrchestrator | None = None) -> None:
        self.db = db
        self.paper_repository = PaperRepository(db)
        self.orchestrator = orchestrator or _build_default_orchestrator()

    def upload_baseline(self, data: BaselinePaperCreate) -> PaperResponse:
        try:
            paper = self.paper_repository.create_baseline(data)
        except PaperReferenceIntegrityError as exc:
            raise PaperInvalidReferenceError(data.student_id, data.subject_id) from exc
        self.orchestrator.process_baseline(paper, self.db)
        return PaperResponse.model_validate(paper)

    def upload_for_analysis(self, data: AnalysisPaperCreate) -> PaperResponse:
        try:
            paper = self.paper_repository.create_submission(data)
        except PaperReferenceIntegrityError as exc:
            raise PaperInvalidReferenceError(data.student_id, data.subject_id) from exc
        analysis_result = self.orchestrator.analyze_submission(paper, self.db)
        response = PaperResponse.model_validate(paper)
        response.analysis_id = (
            analysis_result.id if analysis_result is not None else None
        )
        return response

    def get_paper(self, paper_id: int) -> PaperResponse:
        paper = self.paper_repository.get_by_id(paper_id)
        if paper is None:
            raise PaperNotFoundError(paper_id)
        return PaperResponse.model_validate(paper)

from typing import Any

from sqlalchemy.orm import Session

from application.repositories.analysis_repository import AnalysisRepository
from models.analysis_result import AnalysisResult
from schemas.analysis import (
    AnalysisResultResponse,
    BreakdownScore,
    FeedbackCreate,
    FeedbackResponse,
)


class AnalysisNotFoundError(Exception):
    def __init__(self, analysis_id: int) -> None:
        self.analysis_id = analysis_id
        super().__init__(f"Analysis {analysis_id} not found")


class AnalysisService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.analysis_repository = AnalysisRepository(db)

    def get_analysis(self, analysis_id: int) -> AnalysisResultResponse:
        analysis = self.analysis_repository.get_by_id(analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError(analysis_id)
        return _to_response(analysis)

    def submit_feedback(
        self, analysis_id: int, data: FeedbackCreate
    ) -> FeedbackResponse:
        analysis = self.analysis_repository.get_by_id(analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError(analysis_id)
        feedback = self.analysis_repository.save_feedback(analysis.paper_id, data)
        return FeedbackResponse.model_validate(feedback)


def _to_response(analysis: AnalysisResult) -> AnalysisResultResponse:
    # `breakdown` is a JSON blob that carries the 5 BreakdownScore fields
    # plus bookkeeping (threshold/deltas/explanation) that isn't part of the
    # analysis_results schema. BreakdownScore ignores the extra keys; the
    # explanation is pulled out separately since it's a sibling response field.
    breakdown_data: dict[str, Any] = dict(analysis.breakdown)
    explanation = breakdown_data.get("explanation", "")

    return AnalysisResultResponse(
        id=analysis.id,
        paper_id=analysis.paper_id,
        consistency_score=analysis.consistency_score,
        confidence_level=analysis.confidence_level,
        breakdown=BreakdownScore(**breakdown_data),
        explanation=explanation,
    )

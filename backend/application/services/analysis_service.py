from typing import Any

from sqlalchemy.orm import Session

from ai.features.registry import SCHEMA_VERSION
from application.repositories.analysis_repository import AnalysisRepository
from models.analysis_result import AnalysisResult
from schemas.analysis import (
    AnalysisBreakdown,
    AnalysisResultResponse,
    FeedbackCreate,
    FeedbackResponse,
)


class AnalysisNotFoundError(Exception):
    def __init__(self, analysis_id: int) -> None:
        self.analysis_id = analysis_id
        super().__init__(f"Analysis {analysis_id} not found")


class AnalysisForbiddenError(Exception):
    """Another teacher's analysis. Mapped to 404, same as not-found."""

    def __init__(self, analysis_id: int) -> None:
        self.analysis_id = analysis_id
        super().__init__(f"Analysis {analysis_id} not found")


class StaleAnalysisError(Exception):
    """Stored by an older engine version and not yet regenerated.

    Mapped to 409 rather than coerced into the current models - a v1
    breakdown holds five ad-hoc scores that have no v2 equivalent, and
    inventing one would misreport the result. `scripts/rebuild_analysis.py`
    regenerates these from the papers they were derived from.
    """

    def __init__(self, analysis_id: int, found: int) -> None:
        self.analysis_id = analysis_id
        self.found = found
        super().__init__(
            f"Analysis {analysis_id} was produced by an earlier version of the "
            f"engine (schema v{found}, current v{SCHEMA_VERSION}) and is being "
            "regenerated"
        )


class AnalysisService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.analysis_repository = AnalysisRepository(db)

    def get_analysis(self, analysis_id: int, teacher_id: int) -> AnalysisResultResponse:
        analysis = self._get_owned(analysis_id, teacher_id)
        return _to_response(analysis)

    def submit_feedback(
        self, analysis_id: int, teacher_id: int, data: FeedbackCreate
    ) -> FeedbackResponse:
        analysis = self._get_owned(analysis_id, teacher_id)
        feedback = self.analysis_repository.save_feedback(analysis.paper_id, data)
        return FeedbackResponse.model_validate(feedback)

    def _get_owned(self, analysis_id: int, teacher_id: int) -> AnalysisResult:
        """Ownership runs analysis -> paper -> subject -> teacher.

        This matters most for feedback: `save_feedback` is an upsert, so an
        unguarded write silently overwrites the owning teacher's recorded
        decision on their own student.
        """
        analysis = self.analysis_repository.get_by_id(analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError(analysis_id)
        paper = analysis.paper
        if paper is None or paper.subject is None:
            raise AnalysisForbiddenError(analysis_id)
        if paper.subject.teacher_id != teacher_id:
            raise AnalysisForbiddenError(analysis_id)
        return analysis


def _to_response(analysis: AnalysisResult) -> AnalysisResultResponse:
    breakdown_data: dict[str, Any] = dict(analysis.breakdown or {})
    found_version = int(breakdown_data.get("schema_version", 1))
    if found_version != SCHEMA_VERSION:
        raise StaleAnalysisError(analysis.id, found_version)

    breakdown = AnalysisBreakdown.model_validate(breakdown_data)
    return AnalysisResultResponse(
        id=analysis.id,
        paper_id=analysis.paper_id,
        consistency_score=analysis.consistency_score,
        confidence_level=analysis.confidence_level,
        flagged=breakdown.flagged,
        breakdown=breakdown,
        # Also exposed as a sibling field: the existing frontend contract
        # reads `explanation` at the top level.
        explanation=breakdown.explanation,
    )

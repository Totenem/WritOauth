from sqlalchemy.orm import Session

from models.analysis_result import AnalysisResult
from models.feedback import Feedback
from schemas.analysis import FeedbackCreate


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_paper_id(self, paper_id: int) -> AnalysisResult | None:
        return (
            self.db.query(AnalysisResult)
            .filter(AnalysisResult.paper_id == paper_id)
            .first()
        )

    def get_by_id(self, analysis_id: int) -> AnalysisResult | None:
        return self.db.get(AnalysisResult, analysis_id)

    def save(self, paper_id: int, result: dict) -> AnalysisResult:
        """Create or update the (unique, per-paper) analysis result."""
        analysis = self.get_by_paper_id(paper_id)
        if analysis is None:
            analysis = AnalysisResult(paper_id=paper_id)
            self.db.add(analysis)

        analysis.consistency_score = result["consistency_score"]
        analysis.confidence_level = result["confidence_level"]
        analysis.breakdown = result["breakdown"]

        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_feedback_by_paper_id(self, paper_id: int) -> Feedback | None:
        return self.db.query(Feedback).filter(Feedback.paper_id == paper_id).first()

    def save_feedback(self, paper_id: int, data: FeedbackCreate) -> Feedback:
        """Create or update the (unique, per-paper) feedback - a teacher
        revising their decision on the same submission overwrites it rather
        than erroring, since there is exactly one meaningful piece of
        feedback per paper."""
        feedback = self.get_feedback_by_paper_id(paper_id)
        if feedback is None:
            feedback = Feedback(paper_id=paper_id)
            self.db.add(feedback)

        feedback.decision = data.decision
        feedback.remarks = data.remarks

        self.db.commit()
        self.db.refresh(feedback)
        return feedback

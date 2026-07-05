from sqlalchemy.orm import Session

from models.analysis_result import AnalysisResult
from models.feedback import Feedback
from schemas.analysis import FeedbackCreate


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_paper_id(self, paper_id: int) -> AnalysisResult | None:
        raise NotImplementedError

    def get_by_id(self, analysis_id: int) -> AnalysisResult | None:
        raise NotImplementedError

    def save(self, paper_id: int, result: dict) -> AnalysisResult:
        raise NotImplementedError

    def save_feedback(self, paper_id: int, data: FeedbackCreate) -> Feedback:
        raise NotImplementedError

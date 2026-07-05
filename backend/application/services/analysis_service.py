from sqlalchemy.orm import Session

from schemas.analysis import AnalysisResultResponse, FeedbackCreate, FeedbackResponse


class AnalysisService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_analysis(self, analysis_id: int) -> AnalysisResultResponse:
        raise NotImplementedError

    def submit_feedback(self, analysis_id: int, data: FeedbackCreate) -> FeedbackResponse:
        raise NotImplementedError

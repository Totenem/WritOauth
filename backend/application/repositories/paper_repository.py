from sqlalchemy.orm import Session

from models.paper import Paper
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate


class PaperRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, paper_id: int) -> Paper | None:
        raise NotImplementedError

    def create_baseline(self, data: BaselinePaperCreate) -> Paper:
        raise NotImplementedError

    def create_submission(self, data: AnalysisPaperCreate) -> Paper:
        raise NotImplementedError

    def get_baselines_for_student(self, student_id: int) -> list[Paper]:
        raise NotImplementedError

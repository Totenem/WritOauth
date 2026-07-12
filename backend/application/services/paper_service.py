from sqlalchemy.orm import Session

from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate, PaperResponse


class PaperService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upload_baseline(self, data: BaselinePaperCreate) -> PaperResponse:
        raise NotImplementedError

    def upload_for_analysis(self, data: AnalysisPaperCreate) -> PaperResponse:
        raise NotImplementedError

    def get_paper(self, paper_id: int) -> PaperResponse:
        raise NotImplementedError

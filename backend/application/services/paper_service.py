from sqlalchemy.orm import Session

from application.repositories.paper_repository import (
    PaperReferenceIntegrityError,
    PaperRepository,
)
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate, PaperResponse


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
    def __init__(self, db: Session) -> None:
        self.db = db
        self.paper_repository = PaperRepository(db)

    def upload_baseline(self, data: BaselinePaperCreate) -> PaperResponse:
        try:
            paper = self.paper_repository.create_baseline(data)
        except PaperReferenceIntegrityError as exc:
            raise PaperInvalidReferenceError(data.student_id, data.subject_id) from exc
        return PaperResponse.model_validate(paper)

    def upload_for_analysis(self, data: AnalysisPaperCreate) -> PaperResponse:
        try:
            paper = self.paper_repository.create_submission(data)
        except PaperReferenceIntegrityError as exc:
            raise PaperInvalidReferenceError(data.student_id, data.subject_id) from exc
        return PaperResponse.model_validate(paper)

    def get_paper(self, paper_id: int) -> PaperResponse:
        paper = self.paper_repository.get_by_id(paper_id)
        if paper is None:
            raise PaperNotFoundError(paper_id)
        return PaperResponse.model_validate(paper)

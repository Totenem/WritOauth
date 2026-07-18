from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.paper import Paper
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate


class PaperReferenceIntegrityError(Exception):
    def __init__(self, student_id: int, subject_id: int) -> None:
        self.student_id = student_id
        self.subject_id = subject_id
        super().__init__(f"Student {student_id} or subject {subject_id} does not exist")


class PaperRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, paper_id: int) -> Paper | None:
        return self.db.get(Paper, paper_id)

    def create_baseline(self, data: BaselinePaperCreate) -> Paper:
        return self._create(data, "baseline")

    def create_submission(self, data: AnalysisPaperCreate) -> Paper:
        return self._create(data, "submission")

    def get_baselines_for_student(self, student_id: int) -> list[Paper]:
        return (
            self.db.query(Paper)
            .filter(Paper.student_id == student_id, Paper.type == "baseline")
            .all()
        )

    def _create(
        self, data: BaselinePaperCreate | AnalysisPaperCreate, paper_type: str
    ) -> Paper:
        paper = Paper(
            student_id=data.student_id,
            subject_id=data.subject_id,
            type=paper_type,
            content=data.content,
        )
        self.db.add(paper)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise PaperReferenceIntegrityError(
                data.student_id, data.subject_id
            ) from exc
        self.db.refresh(paper)
        return paper

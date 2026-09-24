from sqlalchemy.orm import Session

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
from application.repositories.student_repository import StudentRepository
from application.repositories.subject_repository import SubjectRepository
from models.paper import Paper
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate, PaperResponse


def _build_default_orchestrator() -> AIOrchestrator:
    return AIOrchestrator(
        fingerprint=FingerprintService(),
        retrieval=RetrievalService(),
        scoring=ScoringService(),
        explanation=ExplanationService(),
        profile=ProfileEngine(),
    )


class PaperNotFoundError(Exception):
    def __init__(self, paper_id: int) -> None:
        self.paper_id = paper_id
        super().__init__(f"Paper {paper_id} not found")


class PaperForbiddenError(Exception):
    """Raised when a referenced student/subject/paper isn't the caller's.

    Deliberately carries the same message shape as "not found": callers map
    both to 404 so a teacher can't probe which ids exist.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PaperInvalidReferenceError(Exception):
    def __init__(self, student_id: int, subject_id: int) -> None:
        self.student_id = student_id
        self.subject_id = subject_id
        super().__init__(f"Student {student_id} or subject {subject_id} does not exist")


class PaperService:
    def __init__(self, db: Session, orchestrator: AIOrchestrator | None = None) -> None:
        self.db = db
        self.paper_repository = PaperRepository(db)
        self.student_repository = StudentRepository(db)
        self.subject_repository = SubjectRepository(db)
        self.orchestrator = orchestrator or _build_default_orchestrator()

    def upload_baseline(
        self, data: BaselinePaperCreate, teacher_id: int
    ) -> PaperResponse:
        self._assert_owns_references(data.student_id, data.subject_id, teacher_id)
        try:
            paper = self.paper_repository.create_baseline(data)
        except PaperReferenceIntegrityError as exc:
            raise PaperInvalidReferenceError(data.student_id, data.subject_id) from exc
        self.orchestrator.process_baseline(paper, self.db)
        return PaperResponse.model_validate(paper)

    def upload_for_analysis(
        self, data: AnalysisPaperCreate, teacher_id: int
    ) -> PaperResponse:
        self._assert_owns_references(data.student_id, data.subject_id, teacher_id)
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

    def list_papers(
        self,
        teacher_id: int,
        student_id: int | None = None,
        subject_id: int | None = None,
        paper_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PaperResponse]:
        papers = self.paper_repository.list_for_teacher(
            teacher_id,
            student_id=student_id,
            subject_id=subject_id,
            paper_type=paper_type,
            limit=limit,
            offset=offset,
        )
        return [PaperResponse.model_validate(paper) for paper in papers]

    def get_paper(self, paper_id: int, teacher_id: int) -> PaperResponse:
        paper = self.paper_repository.get_by_id(paper_id)
        if paper is None:
            raise PaperNotFoundError(paper_id)
        self._assert_owns_paper(paper, teacher_id)
        return PaperResponse.model_validate(paper)

    def _assert_owns_references(
        self, student_id: int, subject_id: int, teacher_id: int
    ) -> None:
        """Both the student and the subject must belong to the caller.

        A missing reference and someone else's reference raise the same
        error, so the response can't be used to enumerate ids.
        """
        student = self.student_repository.get_by_id(student_id)
        if student is None or student.teacher_id != teacher_id:
            raise PaperForbiddenError(f"Student {student_id} not found")

        subject = self.subject_repository.get_by_id(subject_id)
        if subject is None or subject.teacher_id != teacher_id:
            raise PaperForbiddenError(f"Subject {subject_id} not found")

    @staticmethod
    def _assert_owns_paper(paper: Paper, teacher_id: int) -> None:
        # Papers carry no teacher_id of their own; ownership runs through
        # the subject the paper was filed under.
        if paper.subject is None or paper.subject.teacher_id != teacher_id:
            raise PaperForbiddenError(f"Paper {paper.id} not found")

from sqlalchemy.orm import Session

from application.repositories.subject_repository import SubjectRepository
from models.subject import Subject
from schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate


class SubjectNotFoundError(Exception):
    def __init__(self, subject_id: int) -> None:
        self.subject_id = subject_id
        super().__init__(f"Subject {subject_id} not found")


class SubjectForbiddenError(Exception):
    def __init__(self, subject_id: int) -> None:
        self.subject_id = subject_id
        super().__init__(f"Subject {subject_id} does not belong to this teacher")


class SubjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.subject_repository = SubjectRepository(db)

    def list_subjects(self, teacher_id: int) -> list[SubjectResponse]:
        subjects = self.subject_repository.get_all(teacher_id)
        return [SubjectResponse.model_validate(subject) for subject in subjects]

    def get_subject(self, subject_id: int, teacher_id: int) -> SubjectResponse:
        subject = self._get_owned(subject_id, teacher_id)
        return SubjectResponse.model_validate(subject)

    def create_subject(self, teacher_id: int, data: SubjectCreate) -> SubjectResponse:
        subject = self.subject_repository.create(teacher_id, data)
        return SubjectResponse.model_validate(subject)

    def update_subject(
        self, subject_id: int, teacher_id: int, data: SubjectUpdate
    ) -> SubjectResponse:
        self._get_owned(subject_id, teacher_id)
        subject = self.subject_repository.update(subject_id, data)
        return SubjectResponse.model_validate(subject)

    def delete_subject(self, subject_id: int, teacher_id: int) -> None:
        self._get_owned(subject_id, teacher_id)
        self.subject_repository.delete(subject_id)

    def _get_owned(self, subject_id: int, teacher_id: int) -> Subject:
        subject = self.subject_repository.get_by_id(subject_id)
        if subject is None:
            raise SubjectNotFoundError(subject_id)
        if subject.teacher_id != teacher_id:
            raise SubjectForbiddenError(subject_id)
        return subject

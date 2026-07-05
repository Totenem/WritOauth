from sqlalchemy.orm import Session

from schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse


class SubjectService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_subjects(self, teacher_id: int) -> list[SubjectResponse]:
        raise NotImplementedError

    def get_subject(self, subject_id: int) -> SubjectResponse:
        raise NotImplementedError

    def create_subject(self, teacher_id: int, data: SubjectCreate) -> SubjectResponse:
        raise NotImplementedError

    def update_subject(self, subject_id: int, data: SubjectUpdate) -> SubjectResponse:
        raise NotImplementedError

    def delete_subject(self, subject_id: int) -> None:
        raise NotImplementedError

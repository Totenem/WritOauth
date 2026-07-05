from sqlalchemy.orm import Session

from models.subject import Subject
from schemas.subject import SubjectCreate, SubjectUpdate


class SubjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self, teacher_id: int) -> list[Subject]:
        raise NotImplementedError

    def get_by_id(self, subject_id: int) -> Subject | None:
        raise NotImplementedError

    def create(self, teacher_id: int, data: SubjectCreate) -> Subject:
        raise NotImplementedError

    def update(self, subject_id: int, data: SubjectUpdate) -> Subject | None:
        raise NotImplementedError

    def delete(self, subject_id: int) -> bool:
        raise NotImplementedError

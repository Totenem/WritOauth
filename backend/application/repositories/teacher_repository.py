from sqlalchemy.orm import Session

from models.teacher import Teacher
from schemas.teacher import TeacherCreate


class TeacherRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> Teacher | None:
        raise NotImplementedError

    def get_by_id(self, teacher_id: int) -> Teacher | None:
        raise NotImplementedError

    def create(self, data: TeacherCreate) -> Teacher:
        raise NotImplementedError

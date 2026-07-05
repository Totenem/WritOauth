from sqlalchemy.orm import Session

from models.student import Student
from schemas.student import StudentCreate, StudentUpdate


class StudentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[Student]:
        raise NotImplementedError

    def get_by_id(self, student_id: int) -> Student | None:
        raise NotImplementedError

    def create(self, data: StudentCreate) -> Student:
        raise NotImplementedError

    def update(self, student_id: int, data: StudentUpdate) -> Student | None:
        raise NotImplementedError

    def delete(self, student_id: int) -> bool:
        raise NotImplementedError

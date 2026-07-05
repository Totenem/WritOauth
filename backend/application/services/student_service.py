from sqlalchemy.orm import Session

from schemas.student import StudentCreate, StudentUpdate, StudentResponse


class StudentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_students(self) -> list[StudentResponse]:
        raise NotImplementedError

    def get_student(self, student_id: int) -> StudentResponse:
        raise NotImplementedError

    def create_student(self, data: StudentCreate) -> StudentResponse:
        raise NotImplementedError

    def update_student(self, student_id: int, data: StudentUpdate) -> StudentResponse:
        raise NotImplementedError

    def delete_student(self, student_id: int) -> None:
        raise NotImplementedError

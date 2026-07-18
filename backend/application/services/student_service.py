from sqlalchemy.orm import Session

from application.repositories.student_repository import StudentRepository
from schemas.student import StudentCreate, StudentResponse, StudentUpdate


class StudentNotFoundError(Exception):
    def __init__(self, student_id: int) -> None:
        self.student_id = student_id
        super().__init__(f"Student {student_id} not found")


class StudentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.student_repository = StudentRepository(db)

    def list_students(self) -> list[StudentResponse]:
        students = self.student_repository.get_all()
        return [StudentResponse.model_validate(student) for student in students]

    def get_student(self, student_id: int) -> StudentResponse:
        student = self.student_repository.get_by_id(student_id)
        if student is None:
            raise StudentNotFoundError(student_id)
        return StudentResponse.model_validate(student)

    def create_student(self, data: StudentCreate) -> StudentResponse:
        student = self.student_repository.create(data)
        return StudentResponse.model_validate(student)

    def update_student(self, student_id: int, data: StudentUpdate) -> StudentResponse:
        student = self.student_repository.update(student_id, data)
        if student is None:
            raise StudentNotFoundError(student_id)
        return StudentResponse.model_validate(student)

    def delete_student(self, student_id: int) -> None:
        deleted = self.student_repository.delete(student_id)
        if not deleted:
            raise StudentNotFoundError(student_id)

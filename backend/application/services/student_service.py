from sqlalchemy.orm import Session

from application.repositories.student_repository import StudentRepository
from models.student import Student
from schemas.student import StudentCreate, StudentResponse, StudentUpdate


class StudentNotFoundError(Exception):
    def __init__(self, student_id: int) -> None:
        self.student_id = student_id
        super().__init__(f"Student {student_id} not found")


class StudentForbiddenError(Exception):
    def __init__(self, student_id: int) -> None:
        self.student_id = student_id
        super().__init__(f"Student {student_id} does not belong to this teacher")


class StudentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.student_repository = StudentRepository(db)

    def list_students(self, teacher_id: int) -> list[StudentResponse]:
        students = self.student_repository.get_all(teacher_id)
        return [StudentResponse.model_validate(student) for student in students]

    def get_student(self, student_id: int, teacher_id: int) -> StudentResponse:
        student = self._get_owned(student_id, teacher_id)
        return StudentResponse.model_validate(student)

    def create_student(self, teacher_id: int, data: StudentCreate) -> StudentResponse:
        student = self.student_repository.create(teacher_id, data)
        return StudentResponse.model_validate(student)

    def update_student(
        self, student_id: int, teacher_id: int, data: StudentUpdate
    ) -> StudentResponse:
        self._get_owned(student_id, teacher_id)
        student = self.student_repository.update(student_id, data)
        return StudentResponse.model_validate(student)

    def delete_student(self, student_id: int, teacher_id: int) -> None:
        self._get_owned(student_id, teacher_id)
        self.student_repository.delete(student_id)

    def _get_owned(self, student_id: int, teacher_id: int) -> Student:
        student = self.student_repository.get_by_id(student_id)
        if student is None:
            raise StudentNotFoundError(student_id)
        if student.teacher_id != teacher_id:
            raise StudentForbiddenError(student_id)
        return student

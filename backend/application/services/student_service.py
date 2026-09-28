from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from application.repositories.student_repository import StudentRepository
from application.repositories.subject_repository import SubjectRepository
from models.student import Student
from schemas.student import StudentCreate, StudentResponse, StudentUpdate
from utils.names import display_name


class StudentNotFoundError(Exception):
    def __init__(self, student_id: int) -> None:
        self.student_id = student_id
        super().__init__(f"Student {student_id} not found")


class StudentForbiddenError(Exception):
    def __init__(self, student_id: int) -> None:
        self.student_id = student_id
        super().__init__(f"Student {student_id} does not belong to this teacher")


class SubjectNotEnrollableError(Exception):
    """Raised when a submitted subject_id doesn't belong to the teacher.

    Reported the same way SubjectService reports a cross-owner subject: a
    404, so a teacher can't probe which other teacher's course ids exist.
    """

    def __init__(self, subject_id: int) -> None:
        self.subject_id = subject_id
        super().__init__(f"Subject {subject_id} not found")


class DuplicateStudentError(Exception):
    """The teacher already has a student with this name (case- and
    whitespace-insensitive). Reported as 409 Conflict."""

    def __init__(self, first_name: str, last_name: str) -> None:
        self.name = display_name(first_name, last_name)
        super().__init__(f"A student named {self.name} already exists")


class StudentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.student_repository = StudentRepository(db)
        self.subject_repository = SubjectRepository(db)

    def list_students(self, teacher_id: int) -> list[StudentResponse]:
        students = self.student_repository.get_all(teacher_id)
        return [StudentResponse.model_validate(student) for student in students]

    def get_student(self, student_id: int, teacher_id: int) -> StudentResponse:
        student = self._get_owned(student_id, teacher_id)
        return StudentResponse.model_validate(student)

    def create_student(self, teacher_id: int, data: StudentCreate) -> StudentResponse:
        self._assert_subjects_owned(data.subject_ids, teacher_id)
        self._assert_name_free(teacher_id, data.first_name, data.last_name)
        try:
            student = self.student_repository.create(teacher_id, data)
        except IntegrityError as exc:
            # Lost a race with a concurrent create of the same name - the
            # unique index caught what the pre-check couldn't.
            self.db.rollback()
            raise DuplicateStudentError(data.first_name, data.last_name) from exc
        return StudentResponse.model_validate(student)

    def update_student(
        self, student_id: int, teacher_id: int, data: StudentUpdate
    ) -> StudentResponse:
        self._get_owned(student_id, teacher_id)
        self._assert_name_free(
            teacher_id, data.first_name, data.last_name, ignore_id=student_id
        )
        try:
            student = self.student_repository.update(student_id, data)
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateStudentError(data.first_name, data.last_name) from exc
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

    def _assert_name_free(
        self,
        teacher_id: int,
        first_name: str,
        last_name: str,
        ignore_id: int | None = None,
    ) -> None:
        """`ignore_id` lets an update keep (or re-case) its own name."""
        match = self.student_repository.find_by_name(teacher_id, first_name, last_name)
        if match is not None and match.id != ignore_id:
            raise DuplicateStudentError(first_name, last_name)

    def _assert_subjects_owned(self, subject_ids: list[int], teacher_id: int) -> None:
        for subject_id in subject_ids:
            subject = self.subject_repository.get_by_id(subject_id)
            if subject is None or subject.teacher_id != teacher_id:
                raise SubjectNotEnrollableError(subject_id)

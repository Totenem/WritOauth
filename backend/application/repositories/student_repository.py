from sqlalchemy import func
from sqlalchemy.orm import Session

from models.enrollment import Enrollment
from models.student import Student
from schemas.student import StudentCreate, StudentUpdate
from utils.names import NameKey, name_key, normalize_name


class StudentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self, teacher_id: int) -> list[Student]:
        return (
            self.db.query(Student)
            .filter(Student.teacher_id == teacher_id)
            .order_by(Student.id)
            .all()
        )

    def get_by_id(self, student_id: int) -> Student | None:
        """Unscoped by design - the service layer performs the ownership
        check so it can distinguish not-found from not-yours."""
        return self.db.get(Student, student_id)

    def find_by_name(
        self, teacher_id: int, first_name: str, last_name: str
    ) -> Student | None:
        """The teacher's student with this name, ignoring case and extra
        whitespace - the same identity the unique index enforces."""
        first, last = name_key(first_name, last_name)
        return (
            self.db.query(Student)
            .filter(
                Student.teacher_id == teacher_id,
                func.lower(Student.first_name) == first,
                func.lower(Student.last_name) == last,
            )
            .first()
        )

    def name_index(self, teacher_id: int) -> dict[NameKey, Student]:
        """Every student the teacher owns, keyed by normalized name - one
        query for a whole batch upload instead of one per CSV row."""
        return {
            name_key(student.first_name, student.last_name): student
            for student in self.get_all(teacher_id)
        }

    def create(self, teacher_id: int, data: StudentCreate) -> Student:
        student = Student(
            first_name=normalize_name(data.first_name),
            last_name=normalize_name(data.last_name),
            email=data.email,
            teacher_id=teacher_id,
        )
        self.db.add(student)
        self.db.flush()  # assigns student.id without ending the transaction

        for subject_id in data.subject_ids:
            self.db.add(Enrollment(student_id=student.id, subject_id=subject_id))

        self.db.commit()
        self.db.refresh(student)
        return student

    def update(self, student_id: int, data: StudentUpdate) -> Student | None:
        student = self.get_by_id(student_id)
        if student is None:
            return None
        student.first_name = normalize_name(data.first_name)
        student.last_name = normalize_name(data.last_name)
        student.email = data.email
        self.db.commit()
        self.db.refresh(student)
        return student

    def delete(self, student_id: int) -> bool:
        student = self.get_by_id(student_id)
        if student is None:
            return False
        self.db.delete(student)
        self.db.commit()
        return True

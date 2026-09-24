from sqlalchemy.orm import Session

from models.student import Student
from schemas.student import StudentCreate, StudentUpdate


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

    def create(self, teacher_id: int, data: StudentCreate) -> Student:
        student = Student(name=data.name, teacher_id=teacher_id)
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def update(self, student_id: int, data: StudentUpdate) -> Student | None:
        student = self.get_by_id(student_id)
        if student is None:
            return None
        student.name = data.name
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

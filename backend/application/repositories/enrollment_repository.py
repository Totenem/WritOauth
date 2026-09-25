from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.enrollment import Enrollment
from models.paper import Paper
from models.student import Student


@dataclass
class RosterRow:
    student: Student
    status: str
    baseline_paper_count: int


@dataclass
class NewEnrollee:
    first_name: str
    last_name: str
    email: str | None
    status: str
    teacher_id: int


class EnrollmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_subject(self, subject_id: int) -> list[RosterRow]:
        baseline_counts = (
            select(
                Paper.student_id.label("student_id"),
                func.count(Paper.id).label("n"),
            )
            .where(Paper.type == "baseline")
            .group_by(Paper.student_id)
            .subquery()
        )

        rows = self.db.execute(
            select(Student, Enrollment.status, func.coalesce(baseline_counts.c.n, 0))
            .join(Enrollment, Enrollment.student_id == Student.id)
            .outerjoin(baseline_counts, baseline_counts.c.student_id == Student.id)
            .where(Enrollment.subject_id == subject_id)
            .order_by(Student.last_name, Student.first_name)
        ).all()

        return [
            RosterRow(student=student, status=status, baseline_paper_count=int(count))
            for student, status, count in rows
        ]

    def batch_create_students(self, subject_id: int, rows: list[NewEnrollee]) -> int:
        """Creates a new Student + Enrollment pair for every row, all in one
        transaction so a mid-batch failure can't half-apply. Every valid CSV
        row becomes a new Student - Student has no natural unique key to
        dedupe against."""
        for row in rows:
            student = Student(
                first_name=row.first_name,
                last_name=row.last_name,
                email=row.email,
                teacher_id=row.teacher_id,
            )
            self.db.add(student)
            self.db.flush()
            self.db.add(
                Enrollment(
                    student_id=student.id, subject_id=subject_id, status=row.status
                )
            )
        self.db.commit()
        return len(rows)

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from application.constants import MIN_BASELINE_PAPERS
from models.enrollment import Enrollment
from models.paper import Paper
from models.subject import Subject
from schemas.subject import SubjectCreate, SubjectUpdate
from utils.course_code import generate_course_code


class SubjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self, teacher_id: int) -> list[Subject]:
        return self.db.query(Subject).filter(Subject.teacher_id == teacher_id).all()

    def get_by_id(self, subject_id: int) -> Subject | None:
        return self.db.get(Subject, subject_id)

    def create(self, teacher_id: int, data: SubjectCreate) -> Subject:
        code = generate_course_code(data.name, self._code_exists)
        subject = Subject(teacher_id=teacher_id, name=data.name, course_code=code)
        self.db.add(subject)
        self.db.commit()
        self.db.refresh(subject)
        return subject

    def update(self, subject_id: int, data: SubjectUpdate) -> Subject | None:
        subject = self.get_by_id(subject_id)
        if subject is None:
            return None
        subject.name = data.name
        self.db.commit()
        self.db.refresh(subject)
        return subject

    def delete(self, subject_id: int) -> bool:
        subject = self.get_by_id(subject_id)
        if subject is None:
            return False
        self.db.delete(subject)
        self.db.commit()
        return True

    def _code_exists(self, code: str) -> bool:
        return (
            self.db.scalar(select(Subject.id).where(Subject.course_code == code))
            is not None
        )

    def roster_stats(self, subject_ids: list[int]) -> dict[int, tuple[int, int]]:
        """subject_id -> (active student_count, baseline_ready_count).

        One query for however many subjects are being listed, rather than
        one query per card.
        """
        if not subject_ids:
            return {}

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
            select(
                Enrollment.subject_id,
                func.count(Enrollment.id),
                func.sum(
                    case(
                        (
                            func.coalesce(baseline_counts.c.n, 0)
                            >= MIN_BASELINE_PAPERS,
                            1,
                        ),
                        else_=0,
                    )
                ),
            )
            .outerjoin(
                baseline_counts, baseline_counts.c.student_id == Enrollment.student_id
            )
            .where(
                Enrollment.subject_id.in_(subject_ids), Enrollment.status == "active"
            )
            .group_by(Enrollment.subject_id)
        ).all()

        stats = {sid: (int(count), int(ready or 0)) for sid, count, ready in rows}
        return {sid: stats.get(sid, (0, 0)) for sid in subject_ids}

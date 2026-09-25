from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Enrollment(Base):
    """A student's membership in one course.

    A pure join record - CASCADE on both FKs, unlike the RESTRICT used for
    ownership edges elsewhere, because an enrollment row means nothing once
    either side is gone.

    `status` is per-enrollment rather than per-student: a student can be
    active in one course and inactive in another.
    """

    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "subject_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", name="enrollment_status"),
        nullable=False,
        server_default="active",
        default="active",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # No `student`/`subject` relationships here - EnrollmentRepository joins
    # on the FK columns directly. Student.subjects / Subject.students (below)
    # are the read paths; adding parallel relationships on this side too
    # would just create two ways to load the same edge.

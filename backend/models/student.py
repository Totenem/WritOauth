from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.baseline_profile import BaselineProfile
    from models.paper import Paper
    from models.subject import Subject
    from models.teacher import Teacher


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # No uniqueness constraint - a shared family inbox across siblings is a
    # real scenario, not a data error.
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Students are owned by the teacher who created them. RESTRICT (rather
    # than CASCADE) so deleting a teacher can never silently destroy student
    # records and the papers hanging off them.
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="students")
    papers: Mapped[list["Paper"]] = relationship("Paper", back_populates="student")
    profiles: Mapped[list["BaselineProfile"]] = relationship(
        "BaselineProfile", back_populates="student"
    )
    # Course membership - separate from `teacher_id`. A student is owned by
    # one teacher but can be enrolled in any number of that teacher's
    # courses (or none, right after being created via a form that hasn't
    # submitted yet).
    subjects: Mapped[list["Subject"]] = relationship(
        "Subject", secondary="enrollments", back_populates="students", viewonly=True
    )

    @property
    def name(self) -> str:
        """Every consumer outside the student CRUD path (dashboard, cards,
        recent activity) displays a student as one string - this is the
        single place that decides how first/last combine for them."""
        return f"{self.first_name} {self.last_name}".strip()

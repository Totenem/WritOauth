from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.paper import Paper
    from models.student import Student
    from models.teacher import Teacher


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Unique, auto-generated at creation (see utils/course_code.py) - the
    # identifier a teacher hands out for batch student enrollment.
    course_code: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="subjects")
    papers: Mapped[list["Paper"]] = relationship("Paper", back_populates="subject")
    students: Mapped[list["Student"]] = relationship(
        "Student", secondary="enrollments", back_populates="subjects", viewonly=True
    )

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.baseline_profile import BaselineProfile
    from models.paper import Paper
    from models.teacher import Teacher


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
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

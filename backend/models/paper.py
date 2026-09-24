from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.analysis_result import AnalysisResult
    from models.feature_vector import FeatureVector
    from models.feedback import Feedback
    from models.student import Student
    from models.subject import Subject


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        Enum("baseline", "submission", name="paper_type"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # How the text arrived: "paste", "pdf", "docx", "txt". Typography
    # features (curly quotes, spacing) describe the editor rather than the
    # author, so scoring suppresses them when a submission's format differs
    # from the baselines'.
    source_format: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="paste", default="paste"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student: Mapped["Student"] = relationship("Student", back_populates="papers")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="papers")
    feature_vector: Mapped["FeatureVector"] = relationship(
        "FeatureVector", back_populates="paper", uselist=False
    )
    analysis_result: Mapped["AnalysisResult"] = relationship(
        "AnalysisResult", back_populates="paper", uselist=False
    )
    feedback: Mapped["Feedback"] = relationship(
        "Feedback", back_populates="paper", uselist=False
    )

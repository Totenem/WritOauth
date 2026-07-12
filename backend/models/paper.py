from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


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
    type: Mapped[str] = mapped_column(Enum("baseline", "submission"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
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

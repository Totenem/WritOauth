from sqlalchemy import Float, ForeignKey, Integer, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class BaselineProfile(Base):
    __tablename__ = "baseline_profiles"
    __table_args__ = (
        UniqueConstraint("student_id", "version", name="uq_student_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    aggregated_features: Mapped[dict] = mapped_column(JSON, nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="profiles")

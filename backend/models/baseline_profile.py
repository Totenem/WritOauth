from typing import TYPE_CHECKING

from sqlalchemy import JSON, Float, ForeignKey, Integer, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.student import Student


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
    # Which engine version produced this row. Lets stale derived data be
    # found with plain SQL rather than JSON probing.
    schema_version: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="2", default=2
    )

    student: Mapped["Student"] = relationship("Student", back_populates="profiles")

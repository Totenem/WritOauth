from typing import TYPE_CHECKING

from sqlalchemy import JSON, Float, ForeignKey, Integer, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.paper import Paper


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("papers.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    consistency_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False)
    breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Which engine version produced this row. Lets stale derived data be
    # found with plain SQL rather than JSON probing.
    schema_version: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="2", default=2
    )

    paper: Mapped["Paper"] = relationship("Paper", back_populates="analysis_result")

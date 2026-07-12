from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.baseline_profile import BaselineProfile
    from models.paper import Paper


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    papers: Mapped[list["Paper"]] = relationship("Paper", back_populates="student")
    profiles: Mapped[list["BaselineProfile"]] = relationship(
        "BaselineProfile", back_populates="student"
    )

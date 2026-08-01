from sqlalchemy.orm import Session

from ai.profile_engine import ProfileEngine
from models.baseline_profile import BaselineProfile


class RetrievalService:
    """Fetches the comparison profile for a submission.

    Kept as its own module/class - matching the original "retrieval"
    responsibility boundary - even though profiles are now read directly
    from Postgres/SQLite (via ProfileEngine) instead of a Chroma vector DB.
    """

    def __init__(self, profile_engine: ProfileEngine | None = None) -> None:
        self.profile_engine = profile_engine or ProfileEngine()

    def retrieve(self, student_id: int, db: Session) -> BaselineProfile | None:
        return self.profile_engine.get_profile(student_id, db)

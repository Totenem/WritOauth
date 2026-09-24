import os
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401 - registers all mapped models on Base.metadata
from models.base import Base
from models.teacher import Teacher


def pytest_configure(config: pytest.Config) -> None:
    # Settings.jwt_secret has no hardcoded default (secrets must never ship
    # with an insecure fallback), so tests need their own value. This runs
    # before collection, i.e. before anything imports `main`/`database.connection`
    # and triggers Settings() construction.
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only")


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite ignores FK constraints unless a connection opts in; prod
    # (Postgres) enforces them by default.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def teacher(db_session: Session) -> Teacher:
    """An owning teacher.

    Students and subjects are teacher-owned, so almost every repository and
    service test needs one to hang its fixtures off.
    """
    record = Teacher(
        name="Ada Lovelace",
        email="ada@example.com",
        password="not-a-real-hash",
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


@pytest.fixture()
def other_teacher(db_session: Session) -> Teacher:
    """A second teacher, for asserting that scoping actually filters."""
    record = Teacher(
        name="Bob Barker",
        email="bob@example.com",
        password="not-a-real-hash",
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


"""A valid v2 analysis breakdown, for tests that need a stored analysis
row without running the whole engine."""


def breakdown_v2(score: float = 92.0, flagged: bool = False) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "extractor_version": "2.0.0",
        "overall": {"z": 0.4, "score": score},
        "profiles": {
            "stylistic": {
                "label": "Stylistic",
                "score": score,
                "z": 0.4,
                "weight": 0.30,
                "available": True,
                "suppressed_reason": None,
                "features": [
                    {
                        "key": "contraction_preference",
                        "label": "Contraction preference",
                        "kind": "scalar",
                        "measurement": "direct",
                        "weight": 0.10,
                        "note": "",
                        "available": True,
                        "suppressed_reason": None,
                        "z": 0.4,
                        "score": score,
                        "submission": 0.2,
                        "baseline_mean": 0.18,
                        "baseline_stdev": 0.05,
                        "baseline_n": 3,
                    }
                ],
            }
        },
        "reliability": {
            "confidence_level": 0.8,
            "n_baseline_papers": 3,
            "total_baseline_words": 1500,
            "submission_word_count": 620,
            "paragraphs_reliable": True,
        },
        "threshold": 75.0,
        "flagged": flagged,
        "explanation": "This submission scores 92% and is consistent with the student's baseline.",
    }


@pytest.fixture()
def analysis_breakdown_v2() -> dict[str, Any]:
    return breakdown_v2()

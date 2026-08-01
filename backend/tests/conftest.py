import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401 - registers all mapped models on Base.metadata
from ai.embedding_service import EmbeddingService
from models.base import Base


def pytest_configure(config: pytest.Config) -> None:
    # Settings.jwt_secret has no hardcoded default (secrets must never ship
    # with an insecure fallback), so tests need their own value. This runs
    # before collection, i.e. before anything imports `main`/`database.connection`
    # and triggers Settings() construction.
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only")


@pytest.fixture(autouse=True)
def _fake_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid loading the real fastembed model (slow, needs a network download
    of ONNX weights on first use) in the default test suite. Patches the
    "load a real model" fallback with a small deterministic, content-derived
    vector so cosine-similarity based scoring still behaves meaningfully.
    Tests that construct `EmbeddingService(embed_fn=...)` explicitly are
    unaffected - their injected callable still takes priority, exactly as
    it does in production.
    """

    def _fake_embed(self: EmbeddingService, content: str) -> list[float]:
        if self._embed_fn is not None:
            return self._embed_fn(content)
        seed = sum(ord(c) for c in content) or 1
        return [((seed * (i + 1)) % 97) / 97 for i in range(8)]

    monkeypatch.setattr(EmbeddingService, "embed", _fake_embed)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite ignores FK constraints unless a connection opts in; MySQL
    # (used in production) enforces them by default.
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

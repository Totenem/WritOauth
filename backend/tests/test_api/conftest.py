"""Shared harness for the API test suite.

The `client` fixture below was previously copy-pasted verbatim into all five
`test_api/*.py` modules. It is hoisted here so there is one definition to keep
correct - notably the SQLite foreign-key pragma, which two of the five copies
were missing.
"""

from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401 - registers all mapped models on Base.metadata
from database.connection import get_db
from main import app
from models.base import Base


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
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

    def override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def register_and_login(client: TestClient) -> Callable[..., dict]:
    """Register a teacher and return their auth header.

    Call it twice with different emails to get two independent teachers -
    that is the harness for every cross-tenant test.
    """

    def _register_and_login(
        email: str = "ada@example.com",
        name: str = "Ada Lovelace",
        password: str = "secret123",
    ) -> dict:
        client.post(
            "/api/auth/register",
            json={"name": name, "email": email, "password": password},
        )
        token = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        ).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _register_and_login


@pytest.fixture()
def auth_headers(register_and_login: Callable[..., dict]) -> dict:
    """The default teacher used by single-tenant tests."""
    return register_and_login()


@pytest.fixture()
def other_headers(register_and_login: Callable[..., dict]) -> dict:
    """A second, unrelated teacher. Must never be able to see the first's data."""
    return register_and_login(email="bob@example.com", name="Bob Barker")

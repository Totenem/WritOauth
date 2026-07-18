import pytest
from sqlalchemy.orm import Session

from application.repositories.teacher_repository import TeacherEmailAlreadyExistsError
from application.services.auth_service import AuthService, InvalidCredentialsError
from schemas.auth import LoginRequest
from schemas.teacher import TeacherCreate
from utils.security import decode_access_token


def _register(service: AuthService, email: str = "ada@example.com"):
    return service.register(
        TeacherCreate(name="Ada Lovelace", email=email, password="secret123")
    )


def test_register_creates_teacher(db_session: Session) -> None:
    service = AuthService(db_session)

    response = _register(service)

    assert response.id is not None
    assert response.email == "ada@example.com"


def test_register_rejects_duplicate_email(db_session: Session) -> None:
    service = AuthService(db_session)
    _register(service)

    with pytest.raises(TeacherEmailAlreadyExistsError):
        _register(service)


def test_login_returns_decodable_token_on_success(db_session: Session) -> None:
    service = AuthService(db_session)
    _register(service)

    token = service.login(LoginRequest(email="ada@example.com", password="secret123"))

    assert token.token_type == "bearer"
    payload = decode_access_token(token.access_token)
    assert payload["sub"] == "ada@example.com"


def test_login_raises_on_unknown_email(db_session: Session) -> None:
    service = AuthService(db_session)

    with pytest.raises(InvalidCredentialsError):
        service.login(LoginRequest(email="missing@example.com", password="whatever"))


def test_login_raises_on_wrong_password(db_session: Session) -> None:
    service = AuthService(db_session)
    _register(service)

    with pytest.raises(InvalidCredentialsError):
        service.login(LoginRequest(email="ada@example.com", password="wrong-password"))


def test_login_errors_are_the_same_for_unknown_email_and_wrong_password(
    db_session: Session,
) -> None:
    service = AuthService(db_session)
    _register(service)

    unknown_email_error = None
    wrong_password_error = None

    try:
        service.login(LoginRequest(email="missing@example.com", password="whatever"))
    except InvalidCredentialsError as exc:
        unknown_email_error = str(exc)

    try:
        service.login(LoginRequest(email="ada@example.com", password="wrong-password"))
    except InvalidCredentialsError as exc:
        wrong_password_error = str(exc)

    assert unknown_email_error == wrong_password_error

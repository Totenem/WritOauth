from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from application.repositories.teacher_repository import TeacherRepository
from database.connection import get_db
from models.teacher import Teacher
from utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_teacher(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Teacher:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise _credentials_exception from exc

    email = payload.get("sub")
    if email is None:
        raise _credentials_exception

    teacher = TeacherRepository(db).get_by_email(email)
    if teacher is None:
        raise _credentials_exception

    return teacher

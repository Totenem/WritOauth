from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.connection import get_db
from models.teacher import Teacher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_teacher(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Teacher:
    raise NotImplementedError

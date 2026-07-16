from datetime import timedelta
from passlib.hash import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    raise NotImplementedError


def decode_access_token(token: str) -> dict:
    raise NotImplementedError

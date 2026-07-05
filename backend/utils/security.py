from datetime import datetime, timedelta


def hash_password(password: str) -> str:
    raise NotImplementedError


def verify_password(plain: str, hashed: str) -> bool:
    raise NotImplementedError


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    raise NotImplementedError


def decode_access_token(token: str) -> dict:
    raise NotImplementedError

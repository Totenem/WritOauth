from sqlalchemy.orm import Session

from schemas.auth import LoginRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def login(self, credentials: LoginRequest) -> TokenResponse:
        raise NotImplementedError

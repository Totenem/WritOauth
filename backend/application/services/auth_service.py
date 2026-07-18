from sqlalchemy.orm import Session

from application.repositories.teacher_repository import TeacherRepository
from schemas.auth import LoginRequest, TokenResponse
from schemas.teacher import TeacherCreate, TeacherResponse
from utils.security import create_access_token, verify_password

# A valid bcrypt hash with no matching password, used to keep login's
# runtime constant whether or not the email exists (avoids user enumeration).
_DUMMY_PASSWORD_HASH = "$2b$12$CiWK5qb9y6WQmS9wzS7dueO2hxlqxNhs1zpcvo1i2sGewkNa2iN.2"


class InvalidCredentialsError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.teacher_repository = TeacherRepository(db)

    def register(self, data: TeacherCreate) -> TeacherResponse:
        teacher = self.teacher_repository.create(data)
        return TeacherResponse.model_validate(teacher)

    def login(self, credentials: LoginRequest) -> TokenResponse:
        teacher = self.teacher_repository.get_by_email(credentials.email)
        password_hash = teacher.password if teacher else _DUMMY_PASSWORD_HASH
        password_ok = verify_password(credentials.password, password_hash)

        if teacher is None or not password_ok:
            raise InvalidCredentialsError()

        access_token = create_access_token({"sub": teacher.email})
        return TokenResponse(access_token=access_token)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.teacher import Teacher
from schemas.teacher import TeacherCreate
from utils.security import hash_password


class TeacherEmailAlreadyExistsError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"A teacher with email '{email}' already exists")


class TeacherRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> Teacher | None:
        return self.db.query(Teacher).filter(Teacher.email == email).first()

    def get_by_id(self, teacher_id: int) -> Teacher | None:
        return self.db.get(Teacher, teacher_id)

    def create(self, data: TeacherCreate) -> Teacher:
        teacher = Teacher(
            name=data.name,
            email=data.email,
            password=hash_password(data.password),
        )
        self.db.add(teacher)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise TeacherEmailAlreadyExistsError(data.email) from exc
        self.db.refresh(teacher)
        return teacher

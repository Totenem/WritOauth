from sqlalchemy.orm import Session

from models.subject import Subject
from schemas.subject import SubjectCreate, SubjectUpdate


class SubjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self, teacher_id: int) -> list[Subject]:
        return self.db.query(Subject).filter(Subject.teacher_id == teacher_id).all()

    def get_by_id(self, subject_id: int) -> Subject | None:
        return self.db.get(Subject, subject_id)

    def create(self, teacher_id: int, data: SubjectCreate) -> Subject:
        subject = Subject(teacher_id=teacher_id, name=data.name)
        self.db.add(subject)
        self.db.commit()
        self.db.refresh(subject)
        return subject

    def update(self, subject_id: int, data: SubjectUpdate) -> Subject | None:
        subject = self.get_by_id(subject_id)
        if subject is None:
            return None
        subject.name = data.name
        self.db.commit()
        self.db.refresh(subject)
        return subject

    def delete(self, subject_id: int) -> bool:
        subject = self.get_by_id(subject_id)
        if subject is None:
            return False
        self.db.delete(subject)
        self.db.commit()
        return True

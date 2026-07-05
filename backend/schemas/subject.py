from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubjectCreate(BaseModel):
    name: str


class SubjectUpdate(BaseModel):
    name: str


class SubjectResponse(BaseModel):
    id: int
    teacher_id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

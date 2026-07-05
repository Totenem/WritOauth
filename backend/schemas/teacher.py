from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TeacherCreate(BaseModel):
    name: str
    email: str
    password: str


class TeacherResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

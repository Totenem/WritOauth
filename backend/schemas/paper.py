from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaselinePaperCreate(BaseModel):
    student_id: int
    subject_id: int
    content: str


class AnalysisPaperCreate(BaseModel):
    student_id: int
    subject_id: int
    content: str


class PaperResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

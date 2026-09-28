from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubjectSummary(BaseModel):
    id: int
    name: str
    course_code: str

    model_config = ConfigDict(from_attributes=True)


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    # At least one subject is required - this is the concrete mechanism
    # behind "a brand-new account can't add a student": with zero subjects
    # to choose from, there is no valid list to submit.
    subject_ids: list[int] = Field(min_length=1)


class StudentUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None


class StudentResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str | None
    # Kept for every existing consumer that just displays a student as one
    # string (dashboard leaderboards, recent activity, cards).
    name: str
    subjects: list[SubjectSummary]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

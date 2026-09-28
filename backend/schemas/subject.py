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
    course_code: str
    # How many students are enrolled, and how many of those already have a
    # complete (>= MIN_BASELINE_PAPERS) baseline - the roster progress bar.
    student_count: int
    baseline_ready_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RosterStudent(BaseModel):
    id: int
    name: str
    email: str | None
    status: str
    baseline_paper_count: int
    baseline_ready: bool

    model_config = ConfigDict(from_attributes=True)


class RosterResponse(BaseModel):
    subject_id: int
    subject_name: str
    course_code: str
    students: list[RosterStudent]


class BatchUploadSkip(BaseModel):
    row: int
    reason: str


class BatchUploadResult(BaseModel):
    # New student records created by this upload.
    created_count: int
    # Students the teacher already had (matched by name) who were enrolled
    # into this course instead of being duplicated.
    linked_count: int = 0
    skipped: list[BatchUploadSkip]

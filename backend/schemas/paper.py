from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

SourceFormat = Literal["paste", "pdf", "docx", "txt"]


class BaselinePaperCreate(BaseModel):
    student_id: int
    subject_id: int
    content: str
    # Where the text came from. The scoring layer suppresses typography
    # features when a submission's format differs from the baselines', so a
    # student isn't flagged for switching from a textarea to a PDF.
    source_format: SourceFormat = "paste"


class AnalysisPaperCreate(BaseModel):
    student_id: int
    subject_id: int
    content: str
    source_format: SourceFormat = "paste"


class PaperResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    type: str
    source_format: str
    created_at: datetime
    analysis_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ExtractionResponse(BaseModel):
    """Text pulled out of an uploaded document, for the teacher to review.

    Deliberately not a paper: the teacher confirms (and can correct) the
    extracted text before it is submitted through the normal upload
    endpoints. A bad extraction should never silently become a baseline.
    """

    filename: str
    source_format: str
    text: str
    word_count: int
    page_count: int | None = None
    warnings: list[str] = []

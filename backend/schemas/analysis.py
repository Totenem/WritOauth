from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BreakdownScore(BaseModel):
    vocabulary: float
    sentence_structure: float
    grammar: float
    readability: float
    style: float


class AnalysisResultResponse(BaseModel):
    id: int
    paper_id: int
    consistency_score: float
    confidence_level: float
    breakdown: BreakdownScore
    explanation: str

    model_config = ConfigDict(from_attributes=True)


class FeedbackCreate(BaseModel):
    decision: str  # "genuine" or "flagged"
    remarks: str | None = None


class FeedbackResponse(BaseModel):
    id: int
    paper_id: int
    decision: str
    remarks: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

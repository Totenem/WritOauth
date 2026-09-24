from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Every model here sets extra="forbid". The previous version relied on
# Pydantic's default extra="ignore" and unpacked the stored JSON with
# `BreakdownScore(**data)`, which silently swallowed three keys. That worked
# by accident: any future key rename would have failed silently rather than
# loudly. Shape drift should break the boundary, not pass through it.
_STRICT = ConfigDict(extra="forbid")


class FeatureBreakdown(BaseModel):
    """One measured feature, with the evidence behind its score."""

    key: str
    label: str
    kind: str
    measurement: str
    weight: float
    note: str = ""
    available: bool
    suppressed_reason: str | None = None
    z: float
    score: float | None = None
    submission: float | None = None
    baseline_mean: float | None = None
    baseline_stdev: float | None = None
    baseline_n: int | None = None

    model_config = _STRICT


class ProfileBreakdown(BaseModel):
    """One of the six authorship profiles."""

    label: str
    score: float | None
    z: float | None
    weight: float
    available: bool
    suppressed_reason: str | None = None
    features: list[FeatureBreakdown] = Field(default_factory=list)

    model_config = _STRICT


class OverallScore(BaseModel):
    z: float
    score: float

    model_config = _STRICT


class Reliability(BaseModel):
    """How much weight this particular comparison can bear.

    Distinct from `confidence_level`, which describes the baseline. Keeping
    them apart is what stops a 92% on a 120-word paragraph from looking as
    solid as a 92% on a 900-word essay.
    """

    confidence_level: float
    n_baseline_papers: int
    total_baseline_words: int
    submission_word_count: int
    paragraphs_reliable: bool

    model_config = _STRICT


class AnalysisBreakdown(BaseModel):
    schema_version: int
    extractor_version: str
    overall: OverallScore
    profiles: dict[str, ProfileBreakdown]
    reliability: Reliability
    threshold: float
    # Computed server-side so the client never has to infer a verdict by
    # comparing a score against a threshold itself.
    flagged: bool
    explanation: str

    model_config = _STRICT


class AnalysisResultResponse(BaseModel):
    id: int
    paper_id: int
    consistency_score: float
    confidence_level: float
    flagged: bool
    breakdown: AnalysisBreakdown
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

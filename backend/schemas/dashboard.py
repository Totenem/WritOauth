from datetime import datetime

from pydantic import BaseModel, ConfigDict

_STRICT = ConfigDict(extra="forbid")


class Counts(BaseModel):
    students: int
    subjects: int
    baseline_papers: int
    submissions: int
    # Not equal to `submissions`: a submission from a student with no
    # baseline produces no analysis at all, so counting papers here would
    # silently overstate how much has actually been checked.
    analyses: int

    model_config = _STRICT


class BaselineReadiness(BaseModel):
    """Which students can actually be checked.

    The most actionable tile on the dashboard: a submission from a student
    with no baseline is never analysed, and nothing else on the page makes
    that visible.
    """

    ready: int
    no_baseline: int
    needs_more_samples: int

    model_config = _STRICT


class Verdicts(BaseModel):
    """Two separate notions of "flagged", deliberately not merged.

    `ai_*` is the engine's score against the threshold. `teacher_*` is what
    a human actually decided. They answer different questions and a teacher
    must be able to tell them apart.
    """

    threshold: float
    ai_flagged: int
    ai_consistent: int
    teacher_flagged: int
    teacher_genuine: int
    awaiting_review: int

    model_config = _STRICT


class StudentStat(BaseModel):
    student_id: int
    name: str
    submissions: int
    flagged: int
    genuine: int
    average_score: float | None

    model_config = _STRICT


class SubjectStat(BaseModel):
    subject_id: int
    name: str
    submissions: int
    flagged: int

    model_config = _STRICT


class RecentAnalysis(BaseModel):
    analysis_id: int
    paper_id: int
    student_id: int
    student_name: str
    subject_id: int
    subject_name: str
    consistency_score: float
    flagged: bool
    teacher_decision: str | None
    created_at: datetime

    model_config = _STRICT


class ScoreBucket(BaseModel):
    label: str
    lower: int
    upper: int
    count: int

    model_config = _STRICT


class DashboardStats(BaseModel):
    counts: Counts
    baseline_readiness: BaselineReadiness
    verdicts: Verdicts
    students_needing_attention: list[StudentStat]
    most_consistent_students: list[StudentStat]
    subjects: list[SubjectStat]
    recent_activity: list[RecentAnalysis]
    score_distribution: list[ScoreBucket]

    model_config = _STRICT

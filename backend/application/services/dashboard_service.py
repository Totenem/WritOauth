"""Shapes the dashboard payload for one teacher."""

from __future__ import annotations

from sqlalchemy.orm import Session

from application.repositories.dashboard_repository import DashboardRepository
from config.settings import get_settings
from schemas.dashboard import (
    BaselineReadiness,
    Counts,
    DashboardStats,
    RecentAnalysis,
    ScoreBucket,
    StudentStat,
    SubjectStat,
    Verdicts,
)

_LEADERBOARD_SIZE = 5
_BUCKET_LABELS = ("0-19", "20-39", "40-59", "60-79", "80-100")


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = DashboardRepository(db)

    def stats(self, teacher_id: int) -> DashboardStats:
        threshold = get_settings().analysis_flag_threshold

        counts = self.repository.counts(teacher_id)
        readiness = self.repository.baseline_readiness(teacher_id)
        verdicts = self.repository.verdicts(teacher_id, threshold)
        students = self.repository.student_stats(teacher_id, threshold)
        subjects = self.repository.subject_stats(teacher_id, threshold)
        recent = self.repository.recent_analyses(teacher_id, threshold)
        distribution = self.repository.score_distribution(teacher_id)

        return DashboardStats(
            counts=Counts(**counts),
            baseline_readiness=BaselineReadiness(**readiness),
            verdicts=Verdicts(threshold=threshold, **verdicts),
            students_needing_attention=_needing_attention(students),
            most_consistent_students=_most_consistent(students),
            subjects=[SubjectStat(**row) for row in _by_flagged(subjects)],
            recent_activity=[RecentAnalysis(**row) for row in recent],
            score_distribution=_buckets(distribution),
        )


def _needing_attention(rows: list[dict]) -> list[StudentStat]:
    """Most flagged first, then lowest average - so a student with one
    flagged submission doesn't outrank one with five."""
    ranked = sorted(
        rows,
        key=lambda r: (
            -r["flagged"],
            r["average_score"] if r["average_score"] is not None else 101,
        ),
    )
    return [StudentStat(**row) for row in ranked[:_LEADERBOARD_SIZE] if row["flagged"]]


def _most_consistent(rows: list[dict]) -> list[StudentStat]:
    eligible = [r for r in rows if r["flagged"] == 0 and r["submissions"] > 0]
    ranked = sorted(
        eligible,
        key=lambda r: (-(r["average_score"] or 0.0), -r["submissions"]),
    )
    return [StudentStat(**row) for row in ranked[:_LEADERBOARD_SIZE]]


def _by_flagged(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (-r["flagged"], -r["submissions"], r["name"]))


def _buckets(counts: list[int]) -> list[ScoreBucket]:
    buckets = []
    for index, label in enumerate(_BUCKET_LABELS):
        buckets.append(
            ScoreBucket(
                label=label,
                lower=index * 20,
                upper=(index * 20 + 19) if index < 4 else 100,
                count=counts[index] if index < len(counts) else 0,
            )
        )
    return buckets

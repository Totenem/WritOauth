"""Aggregate queries behind the teacher dashboard.

Every query here is scoped to one teacher from its first line. Ownership
runs through `subjects.teacher_id` for anything paper-shaped and
`students.teacher_id` for students - there is no unscoped variant of any of
these, deliberately.

The one trap worth stating plainly: papers of type "submission" and rows in
`analysis_results` are NOT one-to-one. `AIOrchestrator.analyze_submission`
returns None when the student has no baseline profile, so no analysis row
is written. Anything counting "how much has been checked" must LEFT JOIN
rather than count papers.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Float, case, cast, func, literal_column, select
from sqlalchemy.orm import Session

from application.constants import MIN_BASELINE_PAPERS
from models.analysis_result import AnalysisResult
from models.feedback import Feedback
from models.paper import Paper
from models.student import Student
from models.subject import Subject

_MIN_BASELINES = MIN_BASELINE_PAPERS

# Students are displayed as one string everywhere outside their own CRUD
# path - this expression is the single place that decides how first/last
# combine.
# `||` rather than concat(): SQLite (used in tests) only gained concat() in 3.44.
_full_name = func.trim(Student.first_name + " " + Student.last_name)


class DashboardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- scoping helpers -------------------------------------------------

    def _papers(self, teacher_id: int):
        """All papers belonging to this teacher, via their subjects."""
        return (
            select(Paper)
            .join(Subject, Subject.id == Paper.subject_id)
            .where(Subject.teacher_id == teacher_id)
        )

    # -- counts ----------------------------------------------------------

    def counts(self, teacher_id: int) -> dict[str, int]:
        students = self.db.scalar(
            select(func.count(Student.id)).where(Student.teacher_id == teacher_id)
        )
        subjects = self.db.scalar(
            select(func.count(Subject.id)).where(Subject.teacher_id == teacher_id)
        )
        by_type: dict[str, int] = {
            str(row[0]): int(row[1])
            for row in self.db.execute(
                select(Paper.type, func.count(Paper.id))
                .join(Subject, Subject.id == Paper.subject_id)
                .where(Subject.teacher_id == teacher_id)
                .group_by(Paper.type)
            ).all()
        }
        analyses = self.db.scalar(
            select(func.count(AnalysisResult.id))
            .join(Paper, Paper.id == AnalysisResult.paper_id)
            .join(Subject, Subject.id == Paper.subject_id)
            .where(Subject.teacher_id == teacher_id)
        )
        return {
            "students": int(students or 0),
            "subjects": int(subjects or 0),
            "baseline_papers": int(by_type.get("baseline", 0)),
            "submissions": int(by_type.get("submission", 0)),
            "analyses": int(analyses or 0),
        }

    # -- baseline readiness ----------------------------------------------

    def baseline_readiness(self, teacher_id: int) -> dict[str, int]:
        baseline_counts = (
            select(
                Paper.student_id.label("student_id"),
                func.count(Paper.id).label("n"),
            )
            .join(Subject, Subject.id == Paper.subject_id)
            .where(Subject.teacher_id == teacher_id, Paper.type == "baseline")
            .group_by(Paper.student_id)
            .subquery()
        )

        rows = self.db.execute(
            select(Student.id, func.coalesce(baseline_counts.c.n, 0))
            .outerjoin(baseline_counts, baseline_counts.c.student_id == Student.id)
            .where(Student.teacher_id == teacher_id)
        ).all()

        ready = sum(1 for _, n in rows if n >= _MIN_BASELINES)
        none_yet = sum(1 for _, n in rows if n == 0)
        partial = sum(1 for _, n in rows if 0 < n < _MIN_BASELINES)
        return {
            "ready": ready,
            "no_baseline": none_yet,
            "needs_more_samples": partial,
        }

    # -- verdicts --------------------------------------------------------

    def verdicts(self, teacher_id: int, threshold: float) -> dict[str, int]:
        ai_rows = self.db.execute(
            select(
                func.sum(
                    case((AnalysisResult.consistency_score < threshold, 1), else_=0)
                ),
                func.sum(
                    case((AnalysisResult.consistency_score >= threshold, 1), else_=0)
                ),
                func.count(AnalysisResult.id),
            )
            .join(Paper, Paper.id == AnalysisResult.paper_id)
            .join(Subject, Subject.id == Paper.subject_id)
            .where(Subject.teacher_id == teacher_id)
        ).one()

        decisions: dict[str, int] = {
            str(row[0]): int(row[1])
            for row in self.db.execute(
                select(Feedback.decision, func.count(Feedback.id))
                .join(Paper, Paper.id == Feedback.paper_id)
                .join(Subject, Subject.id == Paper.subject_id)
                .where(Subject.teacher_id == teacher_id)
                .group_by(Feedback.decision)
            ).all()
        }

        analysed = int(ai_rows[2] or 0)
        reviewed = sum(decisions.values())
        return {
            "ai_flagged": int(ai_rows[0] or 0),
            "ai_consistent": int(ai_rows[1] or 0),
            "teacher_flagged": int(decisions.get("flagged", 0)),
            "teacher_genuine": int(decisions.get("genuine", 0)),
            "awaiting_review": max(0, analysed - reviewed),
        }

    # -- leaderboards ----------------------------------------------------

    def student_stats(self, teacher_id: int, threshold: float) -> list[dict[str, Any]]:
        rows = self.db.execute(
            select(
                Student.id,
                _full_name,
                func.count(AnalysisResult.id),
                func.sum(
                    case((AnalysisResult.consistency_score < threshold, 1), else_=0)
                ),
                func.sum(
                    case((AnalysisResult.consistency_score >= threshold, 1), else_=0)
                ),
                func.avg(cast(AnalysisResult.consistency_score, Float)),
            )
            .join(Paper, Paper.student_id == Student.id)
            .join(Subject, Subject.id == Paper.subject_id)
            .join(AnalysisResult, AnalysisResult.paper_id == Paper.id)
            .where(Student.teacher_id == teacher_id, Subject.teacher_id == teacher_id)
            .group_by(Student.id, Student.first_name, Student.last_name)
        ).all()

        return [
            {
                "student_id": int(sid),
                "name": str(name),
                "submissions": int(total or 0),
                "flagged": int(flagged or 0),
                "genuine": int(genuine or 0),
                "average_score": float(average) if average is not None else None,
            }
            for sid, name, total, flagged, genuine, average in rows
        ]

    def subject_stats(self, teacher_id: int, threshold: float) -> list[dict[str, Any]]:
        rows = self.db.execute(
            select(
                Subject.id,
                Subject.name,
                func.count(AnalysisResult.id),
                func.sum(
                    case((AnalysisResult.consistency_score < threshold, 1), else_=0)
                ),
            )
            .join(Paper, Paper.subject_id == Subject.id)
            .join(AnalysisResult, AnalysisResult.paper_id == Paper.id)
            .where(Subject.teacher_id == teacher_id)
            .group_by(Subject.id, Subject.name)
        ).all()

        return [
            {
                "subject_id": int(sid),
                "name": str(name),
                "submissions": int(total or 0),
                "flagged": int(flagged or 0),
            }
            for sid, name, total, flagged in rows
        ]

    # -- activity + distribution ----------------------------------------

    def recent_analyses(
        self, teacher_id: int, threshold: float, limit: int = 10
    ) -> list[dict[str, Any]]:
        rows = self.db.execute(
            select(
                AnalysisResult.id,
                Paper.id,
                Student.id,
                _full_name,
                Subject.id,
                Subject.name,
                AnalysisResult.consistency_score,
                Paper.created_at,
                Feedback.decision,
            )
            .join(Paper, Paper.id == AnalysisResult.paper_id)
            .join(Subject, Subject.id == Paper.subject_id)
            .join(Student, Student.id == Paper.student_id)
            .outerjoin(Feedback, Feedback.paper_id == Paper.id)
            .where(Subject.teacher_id == teacher_id)
            .order_by(AnalysisResult.id.desc())
            .limit(limit)
        ).all()

        return [
            {
                "analysis_id": int(aid),
                "paper_id": int(pid),
                "student_id": int(sid),
                "student_name": str(sname),
                "subject_id": int(subid),
                "subject_name": str(subname),
                "consistency_score": float(score),
                "flagged": float(score) < threshold,
                "teacher_decision": decision,
                "created_at": created_at,
            }
            for (
                aid,
                pid,
                sid,
                sname,
                subid,
                subname,
                score,
                created_at,
                decision,
            ) in rows
        ]

    def score_distribution(self, teacher_id: int) -> list[int]:
        """Counts per 20-point bucket: 0-19, 20-39, 40-59, 60-79, 80-100.

        Bucketed with an explicit CASE grouped by ordinal position rather
        than by a computed expression. Postgres requires the GROUP BY
        expression to match the SELECT expression exactly, and SQLAlchemy
        emits a *separate* bind parameter for each occurrence of a division
        - so `GROUP BY CAST(score / $2 ...)` does not match
        `SELECT CAST(score / $1 ...)` and Postgres rejects it. SQLite accepts
        it happily, which is why this only failed against a real database.
        """
        bucket = case(
            (AnalysisResult.consistency_score < 20, 0),
            (AnalysisResult.consistency_score < 40, 1),
            (AnalysisResult.consistency_score < 60, 2),
            (AnalysisResult.consistency_score < 80, 3),
            else_=4,
        )
        rows = self.db.execute(
            select(bucket.label("bucket"), func.count(AnalysisResult.id))
            .join(Paper, Paper.id == AnalysisResult.paper_id)
            .join(Subject, Subject.id == Paper.subject_id)
            .where(Subject.teacher_id == teacher_id)
            .group_by(literal_column("1"))
        ).all()

        counts = [0, 0, 0, 0, 0]
        for index, total in rows:
            counts[min(int(index), 4)] += int(total)
        return counts

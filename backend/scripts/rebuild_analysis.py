"""Regenerate all derived authorship data from `papers.content`.

`feature_vectors`, `baseline_profiles` and `analysis_results` are caches:
everything in them can be recomputed from the papers they were derived from.
The v2 migration clears all three rather than trying to translate v1 blobs
into the new shape, so this script is what repopulates them.

It deliberately lives outside the Alembic migration. Running it there would
import application code into the migration environment and load the spaCy
model during a deploy step, which is slow and fragile.

Usage:

    python -m scripts.rebuild_analysis            # rebuild everything
    python -m scripts.rebuild_analysis --student 7
    python -m scripts.rebuild_analysis --dry-run

Idempotent and safe to re-run: analysis rows are upserted per paper, and
profiles are rebuilt from scratch for each student.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.explanation_service import ExplanationService
from ai.fingerprint_service import FingerprintService
from ai.orchestrator import AIOrchestrator
from ai.profile_engine import NoBaselinePapersError, ProfileEngine
from ai.retrieval_service import RetrievalService
from ai.scoring_service import ScoringService
from database.connection import SessionLocal
from models.paper import Paper


def build_orchestrator() -> AIOrchestrator:
    return AIOrchestrator(
        fingerprint=FingerprintService(),
        retrieval=RetrievalService(),
        scoring=ScoringService(),
        explanation=ExplanationService(),
        profile=ProfileEngine(),
    )


def rebuild(db: Session, student_id: int | None = None, dry_run: bool = False) -> dict:
    orchestrator = build_orchestrator()

    student_query = select(Paper.student_id).distinct()
    if student_id is not None:
        student_query = student_query.where(Paper.student_id == student_id)
    student_ids = [row[0] for row in db.execute(student_query).all()]

    stats = {"students": 0, "baselines": 0, "submissions": 0, "skipped": 0}

    for sid in student_ids:
        papers = (
            db.execute(select(Paper).where(Paper.student_id == sid).order_by(Paper.id))
            .scalars()
            .all()
        )
        baselines = [p for p in papers if p.type == "baseline"]
        submissions = [p for p in papers if p.type == "submission"]

        print(
            f"student {sid}: {len(baselines)} baseline(s), "
            f"{len(submissions)} submission(s)"
        )
        if dry_run:
            stats["students"] += 1
            continue

        # Baselines first: a submission can only be scored once the profile
        # it compares against exists.
        for paper in baselines:
            orchestrator.process_baseline(paper, db)
            stats["baselines"] += 1

        for paper in submissions:
            try:
                result = orchestrator.analyze_submission(paper, db)
            except NoBaselinePapersError:
                result = None
            if result is None:
                # No baseline on file - the paper is fingerprinted but left
                # unscored, which is the same state a fresh upload reaches.
                stats["skipped"] += 1
            else:
                stats["submissions"] += 1

        stats["students"] += 1

    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student", type=int, help="rebuild one student only")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be rebuilt without writing",
    )
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        stats = rebuild(db, student_id=args.student, dry_run=args.dry_run)
    finally:
        db.close()

    print(
        "\n{students} student(s): {baselines} baseline(s) fingerprinted, "
        "{submissions} submission(s) analysed, {skipped} left unscored "
        "(no baseline)".format(**stats)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

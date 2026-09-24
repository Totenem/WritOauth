"""Coordinates the authorship pipeline: fingerprint, profile, score, explain.

No LLM and no vector database - see the individual service docstrings for
why. The document-level embedding that previously drove `consistency_score`
has been removed entirely: `BAAI/bge-small-en-v1.5` is a *semantic* model, so
that score rewarded topic overlap. A whole class writing on one prompt all
scored highly against each other, which is a systematic false negative
across exactly the population being screened.

`consistency_score` is now the weighted aggregate of the six stylometric
profiles, which are topic-robust by construction.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ai.explanation_service import ExplanationService
from ai.features import pipeline, stylistic
from ai.features.registry import EXTRACTOR_VERSION, SCHEMA_VERSION
from ai.fingerprint_service import FingerprintService
from ai.profile_engine import ProfileEngine
from ai.retrieval_service import RetrievalService
from ai.scoring_service import ScoringService
from application.repositories.analysis_repository import AnalysisRepository
from config.settings import get_settings
from models.analysis_result import AnalysisResult
from models.baseline_profile import BaselineProfile
from models.feature_vector import FeatureVector
from models.paper import Paper


class AIOrchestrator:
    def __init__(
        self,
        fingerprint: FingerprintService,
        retrieval: RetrievalService,
        scoring: ScoringService,
        explanation: ExplanationService,
        profile: ProfileEngine,
    ) -> None:
        self.fingerprint = fingerprint
        self.retrieval = retrieval
        self.scoring = scoring
        self.explanation = explanation
        self.profile = profile

    def process_baseline(self, paper: Paper, db: Session) -> BaselineProfile:
        """Fingerprint this baseline paper, then rebuild the student's profile."""
        self._extract_and_store_features(paper, db)
        return self.profile.update_profile(paper.student_id, db)

    def analyze_submission(self, paper: Paper, db: Session) -> AnalysisResult | None:
        """Score a submission against the student's latest baseline profile.

        Returns None when the student has no baseline yet - there is nothing
        to compare against, and persisting a zeroed-out score would look like
        a finding rather than an absence of one.
        """
        baseline = self.retrieval.retrieve(paper.student_id, db)
        if baseline is None:
            # Still fingerprint it, so the paper is ready to score the
            # moment a baseline exists.
            self._extract_and_store_features(paper, db)
            return None

        aggregated = baseline.aggregated_features
        baseline_papers = self._baseline_papers(paper.student_id, db)
        vocabulary = _vocabulary(baseline_papers)

        feature_vector = self._extract_and_store_features(
            paper, db, baseline_vocabulary=vocabulary
        )
        submission_features = feature_vector.features

        coverage = _habitual_coverage(paper.content, baseline_papers)

        breakdown = self.scoring.score(
            submission_features,
            aggregated,
            same_source_format=_same_source_format(paper, baseline_papers),
            habitual_coverage=coverage,
        )

        threshold = get_settings().analysis_flag_threshold
        overall_score = float(breakdown["overall"]["score"])
        meta = submission_features.get("meta", {})

        reliability = {
            "confidence_level": baseline.confidence_level,
            "n_baseline_papers": int(aggregated.get("num_baseline_papers", 0)),
            "total_baseline_words": int(aggregated.get("total_baseline_words", 0)),
            "submission_word_count": int(meta.get("word_count", 0)),
            "paragraphs_reliable": bool(meta.get("paragraphs_reliable", False)),
        }

        explanation_text = self.explanation.explain(breakdown, threshold, reliability)

        stored = {
            "schema_version": SCHEMA_VERSION,
            "extractor_version": EXTRACTOR_VERSION,
            "overall": breakdown["overall"],
            "profiles": breakdown["profiles"],
            "reliability": reliability,
            "threshold": threshold,
            # The backend owns the verdict: the client must never have to
            # infer one by comparing a score to a threshold itself.
            "flagged": overall_score < threshold,
            "explanation": explanation_text,
        }

        return AnalysisRepository(db).save(
            paper.id,
            {
                "consistency_score": overall_score,
                "confidence_level": baseline.confidence_level,
                "breakdown": stored,
            },
        )

    # ------------------------------------------------------------------

    def _extract_and_store_features(
        self,
        paper: Paper,
        db: Session,
        baseline_vocabulary: set[str] | None = None,
    ) -> FeatureVector:
        features = self.fingerprint.extract(
            paper.content, baseline_vocabulary=baseline_vocabulary
        )

        existing = (
            db.query(FeatureVector).filter(FeatureVector.paper_id == paper.id).first()
        )
        if existing is not None:
            existing.features = features
        else:
            existing = FeatureVector(paper_id=paper.id, features=features)
            db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    @staticmethod
    def _baseline_papers(student_id: int, db: Session) -> list[Paper]:
        return (
            db.query(Paper)
            .filter(Paper.student_id == student_id, Paper.type == "baseline")
            .order_by(Paper.id)
            .all()
        )


def _vocabulary(papers: list[Paper]) -> set[str]:
    """Words the student has already used, so recurring names and technical
    terms aren't counted as fresh spelling errors on every submission."""
    words: set[str] = set()
    for paper in papers:
        words |= set(pipeline.parse(paper.content).words_lower)
    return words


def _habitual_coverage(content: str, baseline_papers: list[Paper]) -> float | None:
    if len(baseline_papers) < 2:
        return None
    documents = [pipeline.parse(p.content) for p in baseline_papers]
    ngrams = stylistic.habitual_ngrams(documents)
    if not ngrams:
        return None
    return stylistic.habitual_coverage(pipeline.parse(content), ngrams)


def _same_source_format(paper: Paper, baseline_papers: list[Paper]) -> bool:
    """Whether the submission and baselines came through the same route.

    `papers.source_format` lands with the file-upload work; until then every
    paper is a paste, so the typography features stay comparable.
    """
    submission_format = getattr(paper, "source_format", None)
    if submission_format is None:
        return True
    baseline_formats = {getattr(p, "source_format", None) for p in baseline_papers}
    baseline_formats.discard(None)
    if not baseline_formats:
        return True
    return baseline_formats == {submission_format}

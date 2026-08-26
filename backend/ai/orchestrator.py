from sqlalchemy.orm import Session

from ai.embedding_service import EmbeddingService
from ai.explanation_service import ExplanationService
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

# Stylometric fingerprint keys reported as submission-vs-baseline deltas.
_DELTA_FEATURE_KEYS = (
    "sentence_count",
    "avg_sentence_length",
    "avg_word_length",
    "type_token_ratio",
)


class AIOrchestrator:
    """Coordinates the AI pipeline: fingerprinting, embedding, retrieval,
    scoring, and explanation. No LLM call and no vector database - see
    module docstrings on the individual services for why.
    """

    def __init__(
        self,
        fingerprint: FingerprintService,
        embedding: EmbeddingService,
        retrieval: RetrievalService,
        scoring: ScoringService,
        explanation: ExplanationService,
        profile: ProfileEngine,
    ) -> None:
        self.fingerprint = fingerprint
        self.embedding = embedding
        self.retrieval = retrieval
        self.scoring = scoring
        self.explanation = explanation
        self.profile = profile

    def process_baseline(self, paper: Paper, db: Session) -> BaselineProfile:
        """Extract + store this baseline paper's features, then rebuild the
        student's aggregated baseline profile from all their baseline papers."""
        self._extract_and_store_features(paper, db)
        return self.profile.update_profile(paper.student_id, db)

    def analyze_submission(self, paper: Paper, db: Session) -> AnalysisResult | None:
        """Extract + store this submission's features, then score it against
        the student's latest baseline profile.

        Returns None if the student has no baseline profile yet - there is
        nothing to compare against, so no analysis_results row is created
        rather than persisting a meaningless zeroed-out score.
        """
        feature_vector = self._extract_and_store_features(paper, db)
        baseline = self.retrieval.retrieve(paper.student_id, db)
        if baseline is None:
            return None

        submission_features = feature_vector.features
        baseline_features = baseline.aggregated_features

        style_score = self.scoring.score(
            submission_features["embedding"], baseline_features["embedding"]
        )
        breakdown_scores = self.scoring.score_breakdown(
            submission_features, baseline_features, style_score
        )
        deltas = {
            key: {
                "submission": submission_features.get(key, 0.0),
                "baseline": baseline_features.get(key, 0.0),
            }
            for key in _DELTA_FEATURE_KEYS
        }
        threshold = get_settings().analysis_flag_threshold
        explanation_text = self.explanation.explain(style_score, threshold, deltas)

        breakdown = {
            **breakdown_scores,
            "threshold": threshold,
            "deltas": deltas,
            "explanation": explanation_text,
        }

        return AnalysisRepository(db).save(
            paper.id,
            {
                "consistency_score": style_score,
                "confidence_level": baseline.confidence_level,
                "breakdown": breakdown,
            },
        )

    def _extract_and_store_features(self, paper: Paper, db: Session) -> FeatureVector:
        fingerprint = self.fingerprint.extract(paper.content)
        vector = self.embedding.embed(paper.content)
        features = {"embedding": vector, **fingerprint}

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

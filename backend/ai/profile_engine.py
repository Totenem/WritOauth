from collections.abc import Iterable

from sqlalchemy.orm import Session

from models.baseline_profile import BaselineProfile
from models.feature_vector import FeatureVector
from models.paper import Paper

# Stylometric fingerprint keys averaged into a baseline profile.
_STYLE_FEATURE_KEYS = (
    "sentence_count",
    "avg_sentence_length",
    "avg_word_length",
    "type_token_ratio",
)


class NoBaselinePapersError(Exception):
    def __init__(self, student_id: int) -> None:
        self.student_id = student_id
        super().__init__(f"Student {student_id} has no baseline feature vectors yet")


class ProfileEngine:
    """Builds and reads a student's baseline writing profile.

    A profile is a centroid embedding plus averaged stylometrics, stored
    directly as JSON on `baseline_profiles.aggregated_features` - no vector
    database involved.
    """

    def update_profile(self, student_id: int, db: Session) -> BaselineProfile:
        feature_vectors = (
            db.query(FeatureVector)
            .join(Paper, FeatureVector.paper_id == Paper.id)
            .filter(Paper.student_id == student_id, Paper.type == "baseline")
            .all()
        )
        if not feature_vectors:
            raise NoBaselinePapersError(student_id)

        centroid = _mean_vector(fv.features["embedding"] for fv in feature_vectors)
        aggregated_features: dict = {
            key: _mean(fv.features[key] for fv in feature_vectors)
            for key in _STYLE_FEATURE_KEYS
        }
        aggregated_features["embedding"] = centroid
        aggregated_features["num_baseline_papers"] = len(feature_vectors)

        latest = (
            db.query(BaselineProfile)
            .filter(BaselineProfile.student_id == student_id)
            .order_by(BaselineProfile.version.desc())
            .first()
        )
        next_version = (latest.version + 1) if latest is not None else 1

        profile = BaselineProfile(
            student_id=student_id,
            version=next_version,
            confidence_level=min(1.0, len(feature_vectors) / 3),
            aggregated_features=aggregated_features,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    def get_profile(self, student_id: int, db: Session) -> BaselineProfile | None:
        return (
            db.query(BaselineProfile)
            .filter(BaselineProfile.student_id == student_id)
            .order_by(BaselineProfile.version.desc())
            .first()
        )


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _mean_vector(vectors: Iterable[list[float]]) -> list[float]:
    vectors = list(vectors)
    if not vectors:
        return []
    length = len(vectors[0])
    sums = [0.0] * length
    for vector in vectors:
        for index, value in enumerate(vector):
            sums[index] += value
    return [total / len(vectors) for total in sums]

import pytest
from sqlalchemy.orm import Session

from ai.profile_engine import (
    NoBaselinePapersError,
    ProfileEngine,
    aggregate,
    confidence,
)
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from models.feature_vector import FeatureVector
from models.paper import Paper
from schemas.subject import SubjectCreate
from schemas.teacher import TeacherCreate
from tests.helpers import db_student


def _make_student_and_subject(db_session: Session) -> tuple[int, int]:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )
    student = db_student(db_session, teacher.id)
    subject = SubjectRepository(db_session).create(
        teacher.id, SubjectCreate(name="Algebra")
    )
    return student.id, subject.id


def _fingerprint(
    sentence_length: float, spelling_errors: int, words: int = 200
) -> dict:
    return {
        "schema_version": 2,
        "extractor_version": "2.0.0",
        "meta": {"word_count": words, "sentence_count": 10, "paragraph_count": 2},
        "scalars": {"mean_sentence_length": sentence_length},
        "counts": {"spelling_errors": spelling_errors},
        "distributions": {"punctuation_profile": {"comma": 0.6, "semicolon": 0.4}},
    }


def _add_baseline(
    db_session: Session, student_id: int, subject_id: int, features: dict
) -> None:
    paper = Paper(
        student_id=student_id, subject_id=subject_id, type="baseline", content="x"
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)
    db_session.add(FeatureVector(paper_id=paper.id, features=features))
    db_session.commit()


class TestAggregate:
    def test_scalars_carry_mean_stdev_and_raw_values(self) -> None:
        """Storing only the mean made a highly variable writer look identical
        to a metronomic one - both were scored against a single number."""
        profile = aggregate([_fingerprint(10.0, 1), _fingerprint(20.0, 3)])

        stats = profile["scalars"]["mean_sentence_length"]
        assert stats["mean"] == pytest.approx(15.0)
        assert stats["stdev"] == pytest.approx(7.0710678, abs=1e-4)
        assert stats["n"] == 2
        assert stats["values"] == [10.0, 20.0]

    def test_single_paper_leaves_stdev_undefined(self) -> None:
        profile = aggregate([_fingerprint(10.0, 1)])

        assert profile["scalars"]["mean_sentence_length"]["stdev"] is None

    def test_counts_are_pooled_not_averaged(self) -> None:
        """Pooling is materially more stable than a mean of per-paper rates
        when events are sparse."""
        profile = aggregate(
            [_fingerprint(10.0, 2, words=100), _fingerprint(10.0, 4, words=300)]
        )

        stats = profile["counts"]["spelling_errors"]
        assert stats["total"] == 6
        assert stats["total_words"] == 400
        assert stats["rate_per_word"] == pytest.approx(6 / 400)
        assert stats["per_paper"] == [2, 4]

    def test_distributions_record_within_author_spread(self) -> None:
        """The student's own paper-to-paper divergence is the natural scale
        for judging a submission - available from just two papers."""
        profile = aggregate(
            [
                _fingerprint(10.0, 1),
                {
                    **_fingerprint(12.0, 1),
                    "distributions": {
                        "punctuation_profile": {"comma": 0.9, "semicolon": 0.1}
                    },
                },
            ]
        )

        stats = profile["distributions"]["punctuation_profile"]
        assert stats["n"] == 2
        assert stats["mean_pairwise_jsd"] > 0.0

    def test_single_paper_has_no_measurable_spread(self) -> None:
        profile = aggregate([_fingerprint(10.0, 1)])

        assert (
            profile["distributions"]["punctuation_profile"]["mean_pairwise_jsd"] is None
        )

    def test_records_totals_and_version(self) -> None:
        profile = aggregate(
            [_fingerprint(10.0, 1, words=150), _fingerprint(11.0, 2, words=250)]
        )

        assert profile["num_baseline_papers"] == 2
        assert profile["total_baseline_words"] == 400
        assert profile["schema_version"] == 2


class TestConfidence:
    def test_grows_with_papers_and_words(self) -> None:
        assert confidence(1, 400) < confidence(3, 1200) < confidence(5, 2000)

    def test_saturates_at_one(self) -> None:
        assert confidence(20, 20000) == pytest.approx(1.0)

    def test_many_tiny_papers_are_not_a_strong_baseline(self) -> None:
        """The old formula was `min(1, n/3)`, which called three forty-word
        fragments a complete profile."""
        assert confidence(5, 120) < 0.2


class TestUpdateProfile:
    def test_builds_a_profile_from_every_baseline_paper(
        self, db_session: Session
    ) -> None:
        student_id, subject_id = _make_student_and_subject(db_session)
        _add_baseline(db_session, student_id, subject_id, _fingerprint(10.0, 1))
        _add_baseline(db_session, student_id, subject_id, _fingerprint(20.0, 3))

        profile = ProfileEngine().update_profile(student_id, db_session)

        assert profile.version == 1
        assert profile.aggregated_features["num_baseline_papers"] == 2
        assert profile.aggregated_features["scalars"]["mean_sentence_length"][
            "mean"
        ] == pytest.approx(15.0)

    def test_versions_each_rebuild(self, db_session: Session) -> None:
        student_id, subject_id = _make_student_and_subject(db_session)
        _add_baseline(db_session, student_id, subject_id, _fingerprint(10.0, 1))

        first = ProfileEngine().update_profile(student_id, db_session)
        _add_baseline(db_session, student_id, subject_id, _fingerprint(20.0, 2))
        second = ProfileEngine().update_profile(student_id, db_session)

        assert (first.version, second.version) == (1, 2)
        assert second.aggregated_features["num_baseline_papers"] == 2

    def test_raises_when_the_student_has_no_baselines(
        self, db_session: Session
    ) -> None:
        student_id, _ = _make_student_and_subject(db_session)

        with pytest.raises(NoBaselinePapersError):
            ProfileEngine().update_profile(student_id, db_session)

    def test_get_profile_returns_the_latest_version(self, db_session: Session) -> None:
        student_id, subject_id = _make_student_and_subject(db_session)
        _add_baseline(db_session, student_id, subject_id, _fingerprint(10.0, 1))
        ProfileEngine().update_profile(student_id, db_session)
        _add_baseline(db_session, student_id, subject_id, _fingerprint(20.0, 2))
        ProfileEngine().update_profile(student_id, db_session)

        latest = ProfileEngine().get_profile(student_id, db_session)

        assert latest is not None
        assert latest.version == 2

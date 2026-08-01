import pytest
from sqlalchemy.orm import Session

from ai.profile_engine import NoBaselinePapersError, ProfileEngine
from application.repositories.student_repository import StudentRepository
from application.repositories.subject_repository import SubjectRepository
from application.repositories.teacher_repository import TeacherRepository
from models.feature_vector import FeatureVector
from models.paper import Paper
from schemas.student import StudentCreate
from schemas.subject import SubjectCreate
from schemas.teacher import TeacherCreate

_FEATURES_A = {
    "embedding": [1.0, 1.0],
    "sentence_count": 2,
    "avg_sentence_length": 10.0,
    "avg_word_length": 4.0,
    "type_token_ratio": 0.5,
}
_FEATURES_B = {
    "embedding": [3.0, 3.0],
    "sentence_count": 4,
    "avg_sentence_length": 20.0,
    "avg_word_length": 6.0,
    "type_token_ratio": 0.7,
}


def _make_student_and_subject(db_session: Session) -> tuple[int, int]:
    teacher = TeacherRepository(db_session).create(
        TeacherCreate(
            name="Ada Lovelace", email="ada@example.com", password="secret123"
        )
    )
    student = StudentRepository(db_session).create(StudentCreate(name="Grace Hopper"))
    subject = SubjectRepository(db_session).create(
        teacher.id, SubjectCreate(name="Algebra")
    )
    return student.id, subject.id


def _add_baseline_feature_vector(
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


def test_update_profile_averages_embeddings_and_stylometrics(
    db_session: Session,
) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    _add_baseline_feature_vector(db_session, student_id, subject_id, _FEATURES_A)
    _add_baseline_feature_vector(db_session, student_id, subject_id, _FEATURES_B)

    profile = ProfileEngine().update_profile(student_id, db_session)

    assert profile.version == 1
    assert profile.aggregated_features["embedding"] == [2.0, 2.0]
    assert profile.aggregated_features["avg_sentence_length"] == 15.0
    assert profile.aggregated_features["avg_word_length"] == 5.0
    assert profile.aggregated_features["num_baseline_papers"] == 2


def test_update_profile_sets_confidence_from_paper_count(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    _add_baseline_feature_vector(db_session, student_id, subject_id, _FEATURES_A)

    profile = ProfileEngine().update_profile(student_id, db_session)

    assert profile.confidence_level == pytest.approx(1 / 3)


def test_update_profile_caps_confidence_at_one(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    for _ in range(5):
        _add_baseline_feature_vector(db_session, student_id, subject_id, _FEATURES_A)

    profile = ProfileEngine().update_profile(student_id, db_session)

    assert profile.confidence_level == 1.0


def test_update_profile_increments_version_on_rebuild(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    _add_baseline_feature_vector(db_session, student_id, subject_id, _FEATURES_A)
    ProfileEngine().update_profile(student_id, db_session)

    _add_baseline_feature_vector(db_session, student_id, subject_id, _FEATURES_B)
    profile = ProfileEngine().update_profile(student_id, db_session)

    assert profile.version == 2


def test_update_profile_raises_when_student_has_no_baseline_papers(
    db_session: Session,
) -> None:
    student_id, _ = _make_student_and_subject(db_session)

    with pytest.raises(NoBaselinePapersError):
        ProfileEngine().update_profile(student_id, db_session)


def test_get_profile_returns_latest_version(db_session: Session) -> None:
    student_id, subject_id = _make_student_and_subject(db_session)
    _add_baseline_feature_vector(db_session, student_id, subject_id, _FEATURES_A)
    engine = ProfileEngine()
    engine.update_profile(student_id, db_session)
    _add_baseline_feature_vector(db_session, student_id, subject_id, _FEATURES_B)
    latest = engine.update_profile(student_id, db_session)

    fetched = engine.get_profile(student_id, db_session)

    assert fetched is not None
    assert fetched.id == latest.id
    assert fetched.version == 2


def test_get_profile_returns_none_when_no_profile_exists(db_session: Session) -> None:
    student_id, _ = _make_student_and_subject(db_session)

    assert ProfileEngine().get_profile(student_id, db_session) is None

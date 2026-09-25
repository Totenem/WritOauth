"""Course codes, per-course rosters, and CSV batch enrollment."""

import pytest
from sqlalchemy.orm import Session

from application.services.subject_service import (
    BATCH_HEADERS,
    BatchUploadFormatError,
    SubjectForbiddenError,
    SubjectService,
)
from models.paper import Paper
from models.teacher import Teacher
from schemas.subject import SubjectCreate


def _csv(*rows: tuple[str, ...], header: tuple[str, ...] = BATCH_HEADERS) -> bytes:
    lines = [",".join(header)] + [",".join(row) for row in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _subject(db_session: Session, teacher_id: int, name: str = "English 301"):
    return SubjectService(db_session).create_subject(
        teacher_id, SubjectCreate(name=name)
    )


def test_every_subject_gets_a_unique_course_code(
    db_session: Session, teacher: Teacher
) -> None:
    first = _subject(db_session, teacher.id)
    second = _subject(db_session, teacher.id)

    assert first.course_code
    assert first.course_code != second.course_code
    assert first.student_count == 0
    assert first.baseline_ready_count == 0


def test_batch_upload_enrolls_valid_rows(db_session: Session, teacher: Teacher) -> None:
    service = SubjectService(db_session)
    subject = _subject(db_session, teacher.id)
    code = subject.course_code

    result = service.batch_upload(
        subject.id,
        teacher.id,
        _csv(
            (code, "Hopper", "Grace", "grace@navy.mil", "Active"),
            (code, "Lovelace", "Ada", "", "inactive"),
        ),
    )

    assert result.created_count == 2
    assert result.skipped == []

    roster = service.get_roster(subject.id, teacher.id)
    by_name = {s.name: s for s in roster.students}
    assert set(by_name) == {"Grace Hopper", "Ada Lovelace"}
    assert by_name["Grace Hopper"].email == "grace@navy.mil"
    assert by_name["Grace Hopper"].status == "active"
    assert by_name["Ada Lovelace"].email is None
    assert by_name["Ada Lovelace"].status == "inactive"


def test_batch_upload_skips_rows_for_another_course(
    db_session: Session, teacher: Teacher
) -> None:
    service = SubjectService(db_session)
    subject = _subject(db_session, teacher.id)

    result = service.batch_upload(
        subject.id,
        teacher.id,
        _csv(
            (subject.course_code, "Hopper", "Grace", "", "active"),
            ("WRONG-CODE", "Lovelace", "Ada", "", "active"),
        ),
    )

    assert result.created_count == 1
    assert [s.row for s in result.skipped] == [3]
    assert "doesn't match this course" in result.skipped[0].reason


def test_batch_upload_reports_blank_names_and_bad_status(
    db_session: Session, teacher: Teacher
) -> None:
    service = SubjectService(db_session)
    subject = _subject(db_session, teacher.id)
    code = subject.course_code

    result = service.batch_upload(
        subject.id,
        teacher.id,
        _csv(
            (code, "", "Grace", "", "active"),
            (code, "Lovelace", "Ada", "", "graduated"),
        ),
    )

    assert result.created_count == 0
    assert [(s.row, s.reason.split(",")[0]) for s in result.skipped] == [
        (2, "First and last name are required"),
        (3, "Status must be 'active' or 'inactive'"),
    ]


def test_blank_status_defaults_to_active_and_blank_lines_are_ignored(
    db_session: Session, teacher: Teacher
) -> None:
    service = SubjectService(db_session)
    subject = _subject(db_session, teacher.id)

    result = service.batch_upload(
        subject.id,
        teacher.id,
        _csv((subject.course_code, "Hopper", "Grace", "", ""), (",,,,",)),
    )

    assert result.created_count == 1
    assert result.skipped == []
    assert service.get_roster(subject.id, teacher.id).students[0].status == "active"


def test_batch_upload_rejects_a_file_without_the_template_header(
    db_session: Session, teacher: Teacher
) -> None:
    service = SubjectService(db_session)
    subject = _subject(db_session, teacher.id)

    with pytest.raises(BatchUploadFormatError, match="Missing column"):
        service.batch_upload(
            subject.id, teacher.id, _csv(("Grace Hopper",), header=("name",))
        )


def test_batch_upload_accepts_an_excel_bom(
    db_session: Session, teacher: Teacher
) -> None:
    service = SubjectService(db_session)
    subject = _subject(db_session, teacher.id)

    data = "﻿".encode("utf-8") + _csv(
        (subject.course_code, "Hopper", "Grace", "", "active")
    )

    assert service.batch_upload(subject.id, teacher.id, data).created_count == 1


def test_batch_upload_into_another_teachers_course_is_refused(
    db_session: Session, teacher: Teacher, other_teacher: Teacher
) -> None:
    subject = _subject(db_session, other_teacher.id)

    with pytest.raises(SubjectForbiddenError):
        SubjectService(db_session).batch_upload(
            subject.id,
            teacher.id,
            _csv((subject.course_code, "Hopper", "Grace", "", "active")),
        )


def test_roster_counts_only_active_students_with_full_baselines(
    db_session: Session, teacher: Teacher
) -> None:
    service = SubjectService(db_session)
    subject = _subject(db_session, teacher.id)
    code = subject.course_code
    service.batch_upload(
        subject.id,
        teacher.id,
        _csv(
            (code, "Ready", "Rita", "", "active"),
            (code, "Partial", "Pat", "", "active"),
            (code, "Gone", "Gil", "", "inactive"),
        ),
    )
    roster = {s.name: s for s in service.get_roster(subject.id, teacher.id).students}

    def add_baselines(student_id: int, n: int) -> None:
        for _ in range(n):
            db_session.add(
                Paper(
                    student_id=student_id,
                    subject_id=subject.id,
                    type="baseline",
                    content="x",
                )
            )
        db_session.commit()

    add_baselines(roster["Rita Ready"].id, 3)
    add_baselines(roster["Pat Partial"].id, 1)
    add_baselines(roster["Gil Gone"].id, 3)

    refreshed = service.get_subject(subject.id, teacher.id)
    assert refreshed.student_count == 2  # the inactive student isn't counted
    assert refreshed.baseline_ready_count == 1

    ready = {
        s.name: s.baseline_ready
        for s in service.get_roster(subject.id, teacher.id).students
    }
    assert ready == {"Rita Ready": True, "Pat Partial": False, "Gil Gone": True}

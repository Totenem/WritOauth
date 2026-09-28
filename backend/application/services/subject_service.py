import csv
import io

from sqlalchemy.orm import Session

from application.constants import MIN_BASELINE_PAPERS
from application.repositories.enrollment_repository import (
    EnrollmentRepository,
    NewEnrollee,
)
from application.repositories.subject_repository import SubjectRepository
from models.subject import Subject
from schemas.subject import (
    BatchUploadResult,
    BatchUploadSkip,
    RosterResponse,
    RosterStudent,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)

# The template a teacher downloads - also the header this parser requires.
BATCH_HEADERS = ("Subject Code", "Last Name", "First Name", "Email", "Status")
_VALID_STATUSES = {"active", "inactive"}


class SubjectNotFoundError(Exception):
    def __init__(self, subject_id: int) -> None:
        self.subject_id = subject_id
        super().__init__(f"Subject {subject_id} not found")


class SubjectForbiddenError(Exception):
    def __init__(self, subject_id: int) -> None:
        self.subject_id = subject_id
        super().__init__(f"Subject {subject_id} does not belong to this teacher")


class BatchUploadFormatError(Exception):
    """The file itself is unusable - not a single bad row."""


class SubjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.subject_repository = SubjectRepository(db)
        self.enrollment_repository = EnrollmentRepository(db)

    def list_subjects(self, teacher_id: int) -> list[SubjectResponse]:
        subjects = self.subject_repository.get_all(teacher_id)
        stats = self.subject_repository.roster_stats([s.id for s in subjects])
        return [self._to_response(subject, stats[subject.id]) for subject in subjects]

    def get_subject(self, subject_id: int, teacher_id: int) -> SubjectResponse:
        subject = self._get_owned(subject_id, teacher_id)
        return self._to_response(subject, self._stats_for(subject.id))

    def create_subject(self, teacher_id: int, data: SubjectCreate) -> SubjectResponse:
        subject = self.subject_repository.create(teacher_id, data)
        return self._to_response(subject, (0, 0))

    def update_subject(
        self, subject_id: int, teacher_id: int, data: SubjectUpdate
    ) -> SubjectResponse:
        self._get_owned(subject_id, teacher_id)
        subject = self.subject_repository.update(subject_id, data)
        assert subject is not None  # ownership check above guarantees it exists
        return self._to_response(subject, self._stats_for(subject.id))

    def delete_subject(self, subject_id: int, teacher_id: int) -> None:
        self._get_owned(subject_id, teacher_id)
        self.subject_repository.delete(subject_id)

    def get_roster(self, subject_id: int, teacher_id: int) -> RosterResponse:
        subject = self._get_owned(subject_id, teacher_id)
        rows = self.enrollment_repository.list_for_subject(subject.id)
        return RosterResponse(
            subject_id=subject.id,
            subject_name=subject.name,
            course_code=subject.course_code,
            students=[
                RosterStudent(
                    id=row.student.id,
                    name=row.student.name,
                    email=row.student.email,
                    status=row.status,
                    baseline_paper_count=row.baseline_paper_count,
                    baseline_ready=row.baseline_paper_count >= MIN_BASELINE_PAPERS,
                )
                for row in rows
            ],
        )

    def batch_upload(
        self, subject_id: int, teacher_id: int, csv_bytes: bytes
    ) -> BatchUploadResult:
        subject = self._get_owned(subject_id, teacher_id)

        try:
            text = csv_bytes.decode("utf-8-sig")  # tolerate Excel's BOM
        except UnicodeDecodeError as exc:
            raise BatchUploadFormatError("File must be a UTF-8 encoded CSV") from exc

        reader = csv.DictReader(io.StringIO(text))
        headers = [h.strip() for h in (reader.fieldnames or [])]
        missing = [h for h in BATCH_HEADERS if h not in headers]
        if missing:
            raise BatchUploadFormatError(
                f"Missing column(s): {', '.join(missing)}. "
                "Download the template to get the expected header row."
            )

        to_create: list[NewEnrollee] = []
        skipped: list[BatchUploadSkip] = []

        # Row numbers are 1-based and count the header as row 1, matching
        # what a teacher sees when they open the file in a spreadsheet.
        for index, raw in enumerate(reader, start=2):
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
            if not any(row.values()):
                continue  # blank trailing line - not worth reporting

            code = row.get("Subject Code", "")
            first = row.get("First Name", "")
            last = row.get("Last Name", "")
            email = row.get("Email", "") or None
            status = row.get("Status", "").lower() or "active"

            if code.upper() != subject.course_code.upper():
                skipped.append(
                    BatchUploadSkip(
                        row=index,
                        reason=f"Subject code '{code}' doesn't match this course "
                        f"({subject.course_code})",
                    )
                )
            elif not first or not last:
                skipped.append(
                    BatchUploadSkip(
                        row=index, reason="First and last name are required"
                    )
                )
            elif status not in _VALID_STATUSES:
                skipped.append(
                    BatchUploadSkip(
                        row=index,
                        reason=f"Status must be 'active' or 'inactive', got '{status}'",
                    )
                )
            else:
                to_create.append(
                    NewEnrollee(
                        first_name=first,
                        last_name=last,
                        email=email,
                        status=status,
                        teacher_id=teacher_id,
                    )
                )

        created = (
            self.enrollment_repository.batch_create_students(subject.id, to_create)
            if to_create
            else 0
        )
        return BatchUploadResult(created_count=created, skipped=skipped)

    def _stats_for(self, subject_id: int) -> tuple[int, int]:
        return self.subject_repository.roster_stats([subject_id])[subject_id]

    @staticmethod
    def _to_response(subject: Subject, stats: tuple[int, int]) -> SubjectResponse:
        student_count, ready_count = stats
        return SubjectResponse(
            id=subject.id,
            teacher_id=subject.teacher_id,
            name=subject.name,
            course_code=subject.course_code,
            student_count=student_count,
            baseline_ready_count=ready_count,
            created_at=subject.created_at,
        )

    def _get_owned(self, subject_id: int, teacher_id: int) -> Subject:
        subject = self.subject_repository.get_by_id(subject_id)
        if subject is None:
            raise SubjectNotFoundError(subject_id)
        if subject.teacher_id != teacher_id:
            raise SubjectForbiddenError(subject_id)
        return subject

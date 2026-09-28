"""course codes, enrollments, and split student names

Revision ID: d4e2a9f71c63
Revises: c3f8e1d47b92
Create Date: 2026-09-25

Three related changes behind the "Courses & Baseline Setup" redesign:

* `subjects.course_code` - a unique, human-shareable code per course. It is
  what a teacher puts in the batch-enrollment CSV so the system can confirm
  the file belongs to the course it's being uploaded into.
* `enrollments` - students were owned by a teacher but linked to no course
  at all (only papers referenced both). This is the many-to-many edge, with
  a per-course `status` (active/inactive).
* `students.name` -> `first_name` + `last_name`, plus a nullable `email`,
  to match the roster CSV columns.

BACKFILL CAVEATS - review before running against real data:
* Course codes for existing subjects are generated here, randomly suffixed.
* Names are split on the FIRST space: "Mary Ann Smith" becomes first_name
  "Mary", last_name "Ann Smith". A single-word name goes entirely into
  first_name with an empty last_name. Best-effort only.
* Existing students get no enrollments (there was nothing to derive them
  from). They stay visible on /students until enrolled into a course.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from utils.course_code import generate_course_code

# revision identifiers, used by Alembic.
revision: str = "d4e2a9f71c63"
down_revision: Union[str, None] = "c3f8e1d47b92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # -- subjects.course_code -------------------------------------------
    op.add_column(
        "subjects", sa.Column("course_code", sa.String(length=12), nullable=True)
    )

    taken: set[str] = set()
    for subject_id, name in bind.execute(
        sa.text("SELECT id, name FROM subjects")
    ).all():
        code = generate_course_code(name, lambda c: c in taken)
        taken.add(code)
        bind.execute(
            sa.text("UPDATE subjects SET course_code = :code WHERE id = :id"),
            {"code": code, "id": subject_id},
        )

    op.alter_column("subjects", "course_code", nullable=False)
    op.create_unique_constraint("uq_subjects_course_code", "subjects", ["course_code"])

    # -- students: name -> first_name / last_name, + email ----------------
    op.add_column(
        "students", sa.Column("first_name", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "students", sa.Column("last_name", sa.String(length=255), nullable=True)
    )
    op.add_column("students", sa.Column("email", sa.String(length=255), nullable=True))

    op.execute("""
        UPDATE students
        SET first_name = split_part(btrim(name), ' ', 1),
            last_name = CASE
                WHEN position(' ' IN btrim(name)) > 0
                THEN btrim(substring(btrim(name) FROM position(' ' IN btrim(name)) + 1))
                ELSE ''
            END
    """)

    op.alter_column("students", "first_name", nullable=False)
    op.alter_column("students", "last_name", nullable=False)
    op.drop_column("students", "name")

    # -- enrollments ------------------------------------------------------
    op.create_table(
        "enrollments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", name="enrollment_status"),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "subject_id"),
    )
    op.create_index(op.f("ix_enrollments_student_id"), "enrollments", ["student_id"])
    op.create_index(op.f("ix_enrollments_subject_id"), "enrollments", ["subject_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_enrollments_subject_id"), table_name="enrollments")
    op.drop_index(op.f("ix_enrollments_student_id"), table_name="enrollments")
    op.drop_table("enrollments")
    sa.Enum(name="enrollment_status").drop(op.get_bind(), checkfirst=True)

    op.add_column("students", sa.Column("name", sa.String(length=255), nullable=True))
    op.execute("UPDATE students SET name = btrim(first_name || ' ' || last_name)")
    op.alter_column("students", "name", nullable=False)
    op.drop_column("students", "email")
    op.drop_column("students", "last_name")
    op.drop_column("students", "first_name")

    op.drop_constraint("uq_subjects_course_code", "subjects", type_="unique")
    op.drop_column("subjects", "course_code")

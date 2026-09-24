"""add students.teacher_id ownership column

Revision ID: b1a7c4d92e30
Revises: 97c81dfca646
Create Date: 2026-09-24

Students were previously a globally shared table with no link to a teacher,
so every teacher could read, rename and delete every other teacher's
students. This adds the missing ownership edge.

The column is added nullable, backfilled, then made NOT NULL so the migration
works against a database that already holds rows.

BACKFILL CAVEAT: ownership of an existing student is inferred from the papers
they already have (papers -> subjects.teacher_id, most frequent wins).
Students with no papers have no inferable owner and are assigned to the
lowest teachers.id. That is a convenience for pre-production data, not a
general-purpose backfill - review the result before running this anywhere
real.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1a7c4d92e30"
down_revision: Union[str, None] = "97c81dfca646"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("students", sa.Column("teacher_id", sa.Integer(), nullable=True))

    # 1. Infer the owner from the student's existing papers.
    op.execute("""
        UPDATE students AS s
        SET teacher_id = ranked.teacher_id
        FROM (
            SELECT DISTINCT ON (p.student_id)
                   p.student_id,
                   sub.teacher_id,
                   COUNT(*) AS paper_count
            FROM papers AS p
            JOIN subjects AS sub ON sub.id = p.subject_id
            GROUP BY p.student_id, sub.teacher_id
            ORDER BY p.student_id, paper_count DESC, sub.teacher_id ASC
        ) AS ranked
        WHERE s.id = ranked.student_id
        """)

    # 2. Orphans (no papers) fall back to the lowest teacher id.
    op.execute("""
        UPDATE students
        SET teacher_id = (SELECT MIN(id) FROM teachers)
        WHERE teacher_id IS NULL
          AND EXISTS (SELECT 1 FROM teachers)
        """)

    # 3. Any student still unassigned means there are no teachers at all, so
    #    there are no students either - safe to enforce the constraint.
    op.alter_column("students", "teacher_id", nullable=False)
    op.create_index(
        op.f("ix_students_teacher_id"), "students", ["teacher_id"], unique=False
    )
    op.create_foreign_key(
        "fk_students_teacher_id_teachers",
        "students",
        "teachers",
        ["teacher_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_students_teacher_id_teachers", "students", type_="foreignkey"
    )
    op.drop_index(op.f("ix_students_teacher_id"), table_name="students")
    op.drop_column("students", "teacher_id")

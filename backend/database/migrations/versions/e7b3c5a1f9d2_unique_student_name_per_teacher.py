"""unique student name per teacher

Revision ID: e7b3c5a1f9d2
Revises: d4e2a9f71c63
Create Date: 2026-09-28

Batch roster uploads created a brand-new Student for every CSV row, so
re-uploading a roster (or enrolling one student into a second course)
produced duplicate students. The application now matches rows by name; this
migration makes the database enforce the same identity:

    one student per (teacher_id, lower(first_name), lower(last_name))

Before the index can be created, existing duplicates are MERGED:

* Stored names are whitespace-collapsed first ("John  Smith" -> "John
  Smith"), matching utils/names.normalize_name.
* In each duplicate group the lowest id is kept.
* The other records' papers are re-pointed at the keeper, and their course
  enrollments are copied over (skipping courses the keeper is already in).
* The other records are then deleted; their enrollments and baseline
  profiles cascade with them.

AFTER RUNNING: the kept students' baseline profiles don't yet include the
papers moved onto them. Rebuild the derived data:

    python -m scripts.rebuild_analysis

The merge is NOT reversible - downgrade only drops the index.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7b3c5a1f9d2"
down_revision: Union[str, None] = "d4e2a9f71c63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.execute(r"""
        UPDATE students
        SET first_name = regexp_replace(btrim(first_name), '\s+', ' ', 'g'),
            last_name = regexp_replace(btrim(last_name), '\s+', ' ', 'g')
    """)

    op.execute("""
        CREATE TEMPORARY TABLE student_merge ON COMMIT DROP AS
        SELECT id AS loser, keeper
        FROM (
            SELECT id,
                   min(id) OVER (
                       PARTITION BY teacher_id, lower(first_name), lower(last_name)
                   ) AS keeper
            FROM students
        ) grouped
        WHERE id <> keeper
    """)

    merged = bind.execute(
        sa.text("SELECT keeper, count(*) FROM student_merge GROUP BY keeper")
    ).all()

    op.execute("""
        UPDATE papers
        SET student_id = m.keeper
        FROM student_merge m
        WHERE papers.student_id = m.loser
    """)

    op.execute("""
        INSERT INTO enrollments (student_id, subject_id, status)
        SELECT DISTINCT ON (m.keeper, e.subject_id) m.keeper, e.subject_id, e.status
        FROM enrollments e
        JOIN student_merge m ON e.student_id = m.loser
        WHERE NOT EXISTS (
            SELECT 1 FROM enrollments k
            WHERE k.student_id = m.keeper AND k.subject_id = e.subject_id
        )
        ORDER BY m.keeper, e.subject_id, e.id
    """)

    op.execute("DELETE FROM students WHERE id IN (SELECT loser FROM student_merge)")

    if merged:
        summary = ", ".join(f"{keeper} (+{n})" for keeper, n in merged)
        print(
            f"Merged duplicate students into: {summary}. "
            "Run `python -m scripts.rebuild_analysis` to refresh their profiles."
        )

    op.create_index(
        "uq_students_teacher_name",
        "students",
        ["teacher_id", sa.text("lower(first_name)"), sa.text("lower(last_name)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_students_teacher_name", table_name="students")

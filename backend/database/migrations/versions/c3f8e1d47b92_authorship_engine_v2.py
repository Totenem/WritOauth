"""authorship engine v2: six profiles, versioned derived data

Revision ID: c3f8e1d47b92
Revises: b1a7c4d92e30
Create Date: 2026-09-24

The engine moved from four regex features scored by relative deviation to
six linguistically-grounded profiles scored by z-score. Nothing about the
old stored JSON translates into the new shape, so the three derived tables
are cleared rather than migrated.

That is safe because `feature_vectors`, `baseline_profiles` and
`analysis_results` are 100% derived from `papers.content` - no source data
lives in them. `backend/scripts/rebuild_analysis.py` regenerates all three.

The rebuild deliberately does NOT run inside this migration: it would import
application code into Alembic and load the spaCy model during a deploy step.

Also adds:
* `schema_version` on all three derived tables, so stale rows are findable
  with plain SQL and the rebuild script can resume.
* `papers.source_format`, which the scoring layer needs in order to suppress
  typography features when a baseline was pasted and a submission came from
  a PDF (otherwise a student is flagged for changing tools).

`feedback` is keyed on paper_id, not analysis_id, so teacher decisions
survive this migration untouched.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3f8e1d47b92"
down_revision: Union[str, None] = "b1a7c4d92e30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DERIVED_TABLES = ("analysis_results", "baseline_profiles", "feature_vectors")


def upgrade() -> None:
    for table in _DERIVED_TABLES:
        op.add_column(
            table,
            sa.Column(
                "schema_version",
                sa.SmallInteger(),
                nullable=False,
                server_default="2",
            ),
        )

    op.add_column(
        "papers",
        sa.Column(
            "source_format",
            sa.String(length=16),
            nullable=False,
            server_default="paste",
        ),
    )

    # Order matters: analysis_results -> feature_vectors have FKs onto
    # papers, and baseline_profiles onto students, but they reference each
    # other only through papers, so clearing children first is enough.
    for table in _DERIVED_TABLES:
        op.execute(f"DELETE FROM {table}")  # noqa: S608 - fixed table names


def downgrade() -> None:
    # v1 blobs are not reconstructible from v2 data (and vice versa), so a
    # downgrade clears the derived tables too. Re-run the v1 engine to
    # repopulate.
    for table in _DERIVED_TABLES:
        op.execute(f"DELETE FROM {table}")  # noqa: S608 - fixed table names

    op.drop_column("papers", "source_format")
    for table in _DERIVED_TABLES:
        op.drop_column(table, "schema_version")

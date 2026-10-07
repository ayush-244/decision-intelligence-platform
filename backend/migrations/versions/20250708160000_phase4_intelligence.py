"""Phase 4 dataset intelligence reports table."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20250708160000"
down_revision: str | None = "20250706160000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dataset_intelligence_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("health_score", sa.Float(), nullable=True),
        sa.Column("rows_sampled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_rows", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "report_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_id", name="uq_intelligence_reports_version"),
    )
    op.create_index(
        "ix_intelligence_reports_dataset_id",
        "dataset_intelligence_reports",
        ["dataset_id"],
    )
    op.create_index(
        "ix_intelligence_reports_organization_id",
        "dataset_intelligence_reports",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_intelligence_reports_organization_id", table_name="dataset_intelligence_reports")
    op.drop_index("ix_intelligence_reports_dataset_id", table_name="dataset_intelligence_reports")
    op.drop_table("dataset_intelligence_reports")

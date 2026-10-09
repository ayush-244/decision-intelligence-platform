"""Phase 5 statistical analysis runs table."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20250709160000"
down_revision: str | None = "20250708160000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "statistical_analysis_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("goal", sa.String(length=64), nullable=False),
        sa.Column("test_type", sa.String(length=64), nullable=True),
        sa.Column(
            "configuration_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "result_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_statistical_analysis_runs_dataset_id",
        "statistical_analysis_runs",
        ["dataset_id"],
    )
    op.create_index(
        "ix_statistical_analysis_runs_organization_id",
        "statistical_analysis_runs",
        ["organization_id"],
    )
    op.create_index(
        "ix_statistical_analysis_runs_version_id",
        "statistical_analysis_runs",
        ["version_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_statistical_analysis_runs_version_id", table_name="statistical_analysis_runs")
    op.drop_index("ix_statistical_analysis_runs_organization_id", table_name="statistical_analysis_runs")
    op.drop_index("ix_statistical_analysis_runs_dataset_id", table_name="statistical_analysis_runs")
    op.drop_table("statistical_analysis_runs")

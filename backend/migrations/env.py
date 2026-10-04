"""Alembic migration environment (async).

Drives migrations against the same async engine configuration the application
uses, pulling the URL from ``app.core.config`` so there is one source of truth.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.infrastructure.database.base import Base

# Import ORM model modules here so their tables register on ``Base.metadata``.
from app.infrastructure.database.models import (  # noqa: F401
    AnalyticsJobModel,
    AuditLogModel,
    DatasetFileModel,
    DatasetModel,
    DatasetStatisticsModel,
    DatasetVersionModel,
    MembershipModel,
    OrganizationModel,
    ProjectModel,
    RefreshTokenModel,
    IntelligenceReportModel,
    StatisticalAnalysisRunModel,
    CausalAnalysisRunModel,
    DAGVersionModel,
    SimulationRunModel,
    SimulationScenarioModel,
    DecisionRunModel,
    SchemaSnapshotModel,
    UploadJobModel,
    UserModel,
    ValidationReportModel,
    WorkspaceModel,
    CopilotConversationModel,
    CopilotMessageModel,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the runtime DSN so credentials are never stored in alembic.ini.
config.set_main_option("sqlalchemy.url", get_settings().database_url_str)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DBAPI connection)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: object) -> None:
    context.configure(
        connection=connection,  # type: ignore[arg-type]
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

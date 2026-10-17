"""Simulation run ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.mixins import TimestampMixin


class SimulationRunModel(Base, TimestampMixin):
    __tablename__ = "simulation_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    causal_analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("causal_analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    statistical_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("statistical_analysis_runs.id", ondelete="SET NULL"), nullable=True
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("simulation_scenarios.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration_json: Mapped[dict] = mapped_column(JSONB(), nullable=False, server_default="{}")
    result_json: Mapped[dict] = mapped_column(JSONB(), nullable=False, server_default="{}")
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

"""Simulation scenario ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.mixins import TimestampMixin


class SimulationScenarioModel(Base, TimestampMixin):
    __tablename__ = "simulation_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    objective: Mapped[str | None] = mapped_column(Text(), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_baseline: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default="false")
    interventions_json: Mapped[list] = mapped_column(JSONB(), nullable=False, server_default="[]")
    constraints_json: Mapped[list] = mapped_column(JSONB(), nullable=False, server_default="[]")
    version_number: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="1")
    parent_scenario_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("simulation_scenarios.id", ondelete="SET NULL"), nullable=True
    )

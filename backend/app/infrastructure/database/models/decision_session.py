"""Decision session ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.mixins import TimestampMixin


class DecisionSessionModel(Base, TimestampMixin):
    __tablename__ = "decision_sessions"

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
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="1")
    current_step: Mapped[str] = mapped_column(String(64), nullable=False)
    statistical_analysis_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    dag_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    causal_analysis_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    simulation_run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    decision_run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    executive_report_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    workspace_state_json: Mapped[dict] = mapped_column(JSONB(), nullable=False, server_default="{}")
    configuration_json: Mapped[dict] = mapped_column(JSONB(), nullable=False, server_default="{}")
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SessionActivityModel(Base, TimestampMixin):
    __tablename__ = "session_activities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("decision_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB(), nullable=False, server_default="{}")

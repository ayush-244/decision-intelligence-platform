"""Analytics background job ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.mixins import TimestampMixin


class AnalyticsJobModel(Base, TimestampMixin):
    __tablename__ = "analytics_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True
    )
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration_json: Mapped[dict] = mapped_column(JSONB(), nullable=False, server_default="{}")
    result_json: Mapped[dict] = mapped_column(JSONB(), nullable=False, server_default="{}")
    progress: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="0")
    max_retries: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="3")
    logs_json: Mapped[list[str]] = mapped_column(
        ARRAY(Text()), nullable=False, server_default="{}"
    )
    estimated_duration_ms: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

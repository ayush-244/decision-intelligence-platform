"""Validation report ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.mixins import TimestampMixin


class ValidationReportModel(Base, TimestampMixin):
    __tablename__ = "validation_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    checks_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    errors_json: Mapped[list[str]] = mapped_column(JSONB, default=list)
    warnings_json: Mapped[list[str]] = mapped_column(JSONB, default=list)

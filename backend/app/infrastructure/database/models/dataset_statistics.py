"""Dataset statistics placeholder ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.mixins import TimestampMixin


class DatasetStatisticsModel(Base, TimestampMixin):
    __tablename__ = "dataset_statistics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    metrics_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)

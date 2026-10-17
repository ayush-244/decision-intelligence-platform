"""Schema snapshot ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.mixins import TimestampMixin


class SchemaSnapshotModel(Base, TimestampMixin):
    __tablename__ = "schema_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    schema_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    columns_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)

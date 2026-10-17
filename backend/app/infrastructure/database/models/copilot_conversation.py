"""Copilot conversation ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.mixins import TimestampMixin


class CopilotConversationModel(Base, TimestampMixin):
    __tablename__ = "copilot_conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("decision_sessions.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    context_snapshot_json: Mapped[dict] = mapped_column(JSONB(), nullable=False, server_default="{}")
    referenced_resources_json: Mapped[dict] = mapped_column(
        JSONB(), nullable=False, server_default="{}"
    )
    pinned_insights_json: Mapped[list] = mapped_column(JSONB(), nullable=False, server_default="[]")

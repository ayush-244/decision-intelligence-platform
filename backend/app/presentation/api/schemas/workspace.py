"""Workspace API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreateSessionRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class UpdateSessionRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    current_step: str | None = None
    workspace_state: dict[str, Any] | None = None
    statistical_analysis_id: str | None = None
    dag_version_id: str | None = None
    causal_analysis_id: str | None = None
    simulation_run_id: str | None = None
    decision_run_id: str | None = None
    executive_report_id: str | None = None
    action: str | None = Field(default=None, pattern="^(pause|resume|complete)$")


class SessionCommentRequest(BaseModel):
    body: str = Field(..., min_length=1)
    mentions: list[str] = Field(default_factory=list)


class CompareSessionsRequest(BaseModel):
    session_a_id: str
    session_b_id: str


class DecisionSessionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    dataset_id: str
    version_id: str
    name: str
    description: str | None = None
    status: str
    version_number: int
    current_step: str
    workspace_state: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    progress: dict[str, Any] | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> DecisionSessionResponse:
        return cls(
            id=str(payload["id"]),
            dataset_id=str(payload["dataset_id"]),
            version_id=str(payload["version_id"]),
            name=payload["name"],
            description=payload.get("description"),
            status=payload["status"],
            version_number=payload["version_number"],
            current_step=payload["current_step"],
            workspace_state=payload.get("workspace_state", {}),
            created_at=payload["created_at"],
            progress=payload.get("progress"),
        )


class SessionHistoryItem(BaseModel):
    id: str
    name: str
    status: str
    version_number: int
    current_step: str
    created_at: str

    @classmethod
    def from_entity(cls, session: Any) -> SessionHistoryItem:
        return cls(
            id=str(session.id),
            name=session.name,
            status=session.status.value if hasattr(session.status, "value") else session.status,
            version_number=session.version_number,
            current_step=(
                session.current_step.value
                if hasattr(session.current_step, "value")
                else session.current_step
            ),
            created_at=session.created_at.isoformat(),
        )

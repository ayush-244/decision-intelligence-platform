"""Decision session endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import (
    AddSessionCommentDep,
    CreateDecisionSessionDep,
    GetDecisionSessionDep,
    GetSessionTimelineDep,
    ListDecisionSessionsDep,
    TenantContextDep,
    UpdateDecisionSessionDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.workspace import (
    CreateSessionRequest,
    DecisionSessionResponse,
    SessionCommentRequest,
    SessionHistoryItem,
    UpdateSessionRequest,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=DataResponse[SessionHistoryItem],
    status_code=HTTPStatus.CREATED,
    summary="Create a decision session",
)
async def create_session(
    tenant: TenantContextDep,
    use_case: CreateDecisionSessionDep,
    body: CreateSessionRequest,
) -> DataResponse[SessionHistoryItem]:
    session = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        name=body.name,
        description=body.description,
        version_id=UUID(body.version_id) if body.version_id else None,
    )
    return DataResponse(data=SessionHistoryItem.from_entity(session))


@router.get(
    "",
    response_model=DataResponse[list[SessionHistoryItem]],
    summary="List decision sessions for a dataset",
)
async def list_sessions(
    tenant: TenantContextDep,
    use_case: ListDecisionSessionsDep,
    dataset_id: UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
) -> DataResponse[list[SessionHistoryItem]]:
    sessions = await use_case.execute(tenant=tenant, dataset_id=dataset_id, limit=limit)
    return DataResponse(data=[SessionHistoryItem.from_entity(s) for s in sessions])


@router.get(
    "/{session_id}",
    response_model=DataResponse[DecisionSessionResponse],
    summary="Get decision session with workflow progress",
)
async def get_session(
    tenant: TenantContextDep,
    use_case: GetDecisionSessionDep,
    session_id: UUID,
) -> DataResponse[DecisionSessionResponse]:
    payload = await use_case.execute(tenant=tenant, session_id=session_id)
    return DataResponse(data=DecisionSessionResponse.from_payload(payload))


@router.patch(
    "/{session_id}",
    response_model=DataResponse[SessionHistoryItem],
    summary="Update decision session state or lifecycle",
)
async def update_session(
    tenant: TenantContextDep,
    use_case: UpdateDecisionSessionDep,
    session_id: UUID,
    body: UpdateSessionRequest,
) -> DataResponse[SessionHistoryItem]:
    session = await use_case.execute(
        tenant=tenant,
        session_id=session_id,
        name=body.name,
        description=body.description,
        current_step=body.current_step,
        workspace_state=body.workspace_state,
        statistical_analysis_id=(
            UUID(body.statistical_analysis_id) if body.statistical_analysis_id else None
        ),
        dag_version_id=UUID(body.dag_version_id) if body.dag_version_id else None,
        causal_analysis_id=UUID(body.causal_analysis_id) if body.causal_analysis_id else None,
        simulation_run_id=UUID(body.simulation_run_id) if body.simulation_run_id else None,
        decision_run_id=UUID(body.decision_run_id) if body.decision_run_id else None,
        executive_report_id=(
            UUID(body.executive_report_id) if body.executive_report_id else None
        ),
        action=body.action,
    )
    return DataResponse(data=SessionHistoryItem.from_entity(session))


@router.get(
    "/{session_id}/timeline",
    response_model=DataResponse[list[dict]],
    summary="Knowledge timeline for a decision session",
)
async def session_timeline(
    tenant: TenantContextDep,
    use_case: GetSessionTimelineDep,
    session_id: UUID,
) -> DataResponse[list[dict]]:
    events = await use_case.execute(tenant=tenant, session_id=session_id)
    return DataResponse(data=events)


@router.post(
    "/{session_id}/comments",
    response_model=DataResponse[dict],
    status_code=HTTPStatus.CREATED,
    summary="Add a comment to a session (collaboration foundation)",
)
async def add_comment(
    tenant: TenantContextDep,
    use_case: AddSessionCommentDep,
    session_id: UUID,
    body: SessionCommentRequest,
) -> DataResponse[dict]:
    activity = await use_case.execute(
        tenant=tenant,
        session_id=session_id,
        body=body.body,
        mentions=tuple(body.mentions),
    )
    return DataResponse(data=activity)

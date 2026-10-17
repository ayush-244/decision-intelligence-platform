"""Unified workspace use cases."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.services.workspace.comparison import ComparisonEngine
from app.application.services.workspace.search import WorkspaceSearchEngine
from app.application.services.workspace.serialization import to_jsonable
from app.application.services.workspace.session_engine import DecisionSessionEngine
from app.application.services.workspace.timeline import TimelineEngine
from app.domain.entities.decision_session import DecisionSession
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.decision_session_repository import DecisionSessionRepository
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.role import Permission
from app.domain.value_objects.tenant import TenantContext
from app.domain.value_objects.workspace import WorkflowStep
from app.shared.exceptions import BusinessValidationError, NotFoundError


class _DatasetAccessGuard:
    def __init__(
        self,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._projects = projects
        self._workspaces = workspaces

    async def resolve_version(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None,
    ) -> tuple[Any, Any]:
        dataset = await self._datasets.get_by_id(
            dataset_id=dataset_id, organization_id=tenant.organization_id
        )
        if dataset is None:
            raise NotFoundError("Dataset not found.")
        workspace_id = await self._projects.get_workspace_id(dataset.project_id)
        if workspace_id is None:
            raise NotFoundError("Dataset not found.")
        workspace = await self._workspaces.get_by_id(
            workspace_id=workspace_id, organization_id=tenant.organization_id
        )
        if workspace is None:
            raise NotFoundError("Dataset not found.")
        target_version_id = version_id or dataset.current_version_id
        if target_version_id is None:
            raise NotFoundError("Dataset has no versions.")
        version = await self._versions.get_by_id(version_id=target_version_id)
        if version is None or version.dataset_id != dataset_id:
            raise NotFoundError("Dataset version not found.")
        return dataset, version

    async def get_session(
        self,
        *,
        tenant: TenantContext,
        session_id: UUID,
        sessions: DecisionSessionRepository,
    ) -> DecisionSession:
        session = await sessions.get_by_id(
            session_id=session_id, organization_id=tenant.organization_id
        )
        if session is None:
            raise NotFoundError("Decision session not found.")
        await self.resolve_version(
            tenant=tenant, dataset_id=session.dataset_id, version_id=session.version_id
        )
        return session


class CreateDecisionSessionUseCase:
    def __init__(
        self,
        engine: DecisionSessionEngine,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._engine = engine
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        name: str,
        description: str | None = None,
        version_id: UUID | None = None,
    ) -> DecisionSession:
        self._authorization.require_permission(tenant.role, Permission.SESSION_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        return await self._engine.create(
            dataset=dataset,
            version=version,
            name=name,
            description=description,
            created_by=tenant.user_id,
        )


class GetDecisionSessionUseCase:
    def __init__(
        self,
        sessions: DecisionSessionRepository,
        engine: DecisionSessionEngine,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._sessions = sessions
        self._engine = engine
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, session_id: UUID) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.SESSION_READ)
        session = await self._guard.get_session(
            tenant=tenant, session_id=session_id, sessions=self._sessions
        )
        progress = self._engine.progress(session)
        payload = to_jsonable(session)
        payload["progress"] = to_jsonable(progress)
        return payload


class ListDecisionSessionsUseCase:
    def __init__(
        self,
        sessions: DecisionSessionRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._sessions = sessions
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self, *, tenant: TenantContext, dataset_id: UUID, limit: int = 50
    ) -> list[DecisionSession]:
        self._authorization.require_permission(tenant.role, Permission.SESSION_READ)
        await self._guard.resolve_version(tenant=tenant, dataset_id=dataset_id, version_id=None)
        return await self._sessions.list_for_dataset(
            dataset_id=dataset_id, organization_id=tenant.organization_id, limit=limit
        )


class UpdateDecisionSessionUseCase:
    def __init__(
        self,
        sessions: DecisionSessionRepository,
        engine: DecisionSessionEngine,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._sessions = sessions
        self._engine = engine
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        session_id: UUID,
        name: str | None = None,
        description: str | None = None,
        current_step: str | None = None,
        workspace_state: dict[str, Any] | None = None,
        statistical_analysis_id: UUID | None = None,
        dag_version_id: UUID | None = None,
        causal_analysis_id: UUID | None = None,
        simulation_run_id: UUID | None = None,
        decision_run_id: UUID | None = None,
        executive_report_id: UUID | None = None,
        action: str | None = None,
    ) -> DecisionSession:
        self._authorization.require_permission(tenant.role, Permission.SESSION_UPDATE)
        session = await self._guard.get_session(
            tenant=tenant, session_id=session_id, sessions=self._sessions
        )
        if action == "pause":
            return await self._engine.pause(session=session, user_id=tenant.user_id)
        if action == "resume":
            return await self._engine.resume(session=session, user_id=tenant.user_id)
        if action == "complete":
            return await self._engine.complete(session=session, user_id=tenant.user_id)
        step = WorkflowStep(current_step) if current_step else None
        return await self._engine.update(
            session=session,
            user_id=tenant.user_id,
            name=name,
            description=description,
            current_step=step,
            workspace_state=workspace_state,
            statistical_analysis_id=statistical_analysis_id,
            dag_version_id=dag_version_id,
            causal_analysis_id=causal_analysis_id,
            simulation_run_id=simulation_run_id,
            decision_run_id=decision_run_id,
            executive_report_id=executive_report_id,
        )


class AddSessionCommentUseCase:
    def __init__(
        self,
        sessions: DecisionSessionRepository,
        engine: DecisionSessionEngine,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._engine = engine
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization
        self._sessions = sessions

    async def execute(
        self,
        *,
        tenant: TenantContext,
        session_id: UUID,
        body: str,
        mentions: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.SESSION_UPDATE)
        if not body.strip():
            raise BusinessValidationError("Comment cannot be empty.", code="empty_comment")
        session = await self._guard.get_session(
            tenant=tenant, session_id=session_id, sessions=self._sessions
        )
        activity = await self._engine.add_comment(
            session=session, user_id=tenant.user_id, body=body, mentions=mentions
        )
        return to_jsonable(activity)


class GetSessionTimelineUseCase:
    def __init__(
        self,
        sessions: DecisionSessionRepository,
        timeline: TimelineEngine,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._sessions = sessions
        self._timeline = timeline
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, session_id: UUID) -> list[dict[str, Any]]:
        self._authorization.require_permission(tenant.role, Permission.SESSION_READ)
        session = await self._guard.get_session(
            tenant=tenant, session_id=session_id, sessions=self._sessions
        )
        events = await self._timeline.for_session(
            session=session, organization_id=tenant.organization_id
        )
        return [to_jsonable(e) for e in events]


class WorkspaceSearchUseCase:
    def __init__(
        self,
        search: WorkspaceSearchEngine,
        authorization: AuthorizationService,
    ) -> None:
        self._search = search
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        query: str,
        dataset_id: UUID | None = None,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        self._authorization.require_permission(tenant.role, Permission.WORKSPACE_SEARCH)
        results = await self._search.search(
            organization_id=tenant.organization_id,
            query=query,
            limit=limit,
            dataset_id=dataset_id,
        )
        return [to_jsonable(r) for r in results]


class CompareSessionsUseCase:
    def __init__(
        self,
        sessions: DecisionSessionRepository,
        comparison: ComparisonEngine,
        simulations: SimulationRunRepository,
        decisions: DecisionRunRepository,
        reports: ExecutiveReportRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._sessions = sessions
        self._comparison = comparison
        self._simulations = simulations
        self._decisions = decisions
        self._reports = reports
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        session_a_id: UUID,
        session_b_id: UUID,
    ) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.SESSION_READ)
        session_a = await self._guard.get_session(
            tenant=tenant, session_id=session_a_id, sessions=self._sessions
        )
        session_b = await self._guard.get_session(
            tenant=tenant, session_id=session_b_id, sessions=self._sessions
        )
        result = await self._comparison.compare_sessions(
            session_a=session_a,
            session_b=session_b,
            simulations=self._simulations,
            decisions=self._decisions,
            reports=self._reports,
            organization_id=tenant.organization_id,
        )
        return to_jsonable(result)


class ListWorkspaceActivityUseCase:
    def __init__(
        self,
        audit_logs: AuditLogRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._audit_logs = audit_logs
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        limit: int = 50,
        resource_type: str | None = None,
    ) -> list[dict[str, Any]]:
        self._authorization.require_permission(tenant.role, Permission.WORKSPACE_READ)
        logs = await self._audit_logs.list_for_organization(
            organization_id=tenant.organization_id,
            limit=limit,
            resource_type=resource_type,
        )
        return [to_jsonable(log) for log in logs]

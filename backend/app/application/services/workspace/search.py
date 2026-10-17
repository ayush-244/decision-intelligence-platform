"""Global workspace search across platform resources."""

from __future__ import annotations

from uuid import UUID

from app.application.dto.workspace import SearchResultDTO
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.decision_session_repository import DecisionSessionRepository
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.statistical_analysis_repository import StatisticalAnalysisRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.workspace import SearchResourceType


class WorkspaceSearchEngine:
    """Scalable search facade — queries repositories with tenant isolation."""

    def __init__(
        self,
        workspaces: WorkspaceRepository,
        projects: ProjectRepository,
        datasets: DatasetRepository,
        statistics: StatisticalAnalysisRepository,
        causal: CausalAnalysisRepository,
        simulations: SimulationRunRepository,
        decisions: DecisionRunRepository,
        reports: ExecutiveReportRepository,
        sessions: DecisionSessionRepository,
    ) -> None:
        self._workspaces = workspaces
        self._projects = projects
        self._datasets = datasets
        self._statistics = statistics
        self._causal = causal
        self._simulations = simulations
        self._decisions = decisions
        self._reports = reports
        self._sessions = sessions

    async def search(
        self,
        *,
        organization_id: UUID,
        query: str,
        limit: int = 30,
        dataset_id: UUID | None = None,
    ) -> tuple[SearchResultDTO, ...]:
        q = query.strip().lower()
        if not q:
            return ()

        results: list[SearchResultDTO] = []
        per_type = max(5, limit // 7)

        for workspace in await self._workspaces.list_for_organization(organization_id):
            for project in await self._projects.list_for_workspace(workspace.id):
                if q in project.name.lower():
                    results.append(
                        SearchResultDTO(
                            resource_type=SearchResourceType.PROJECT.value,
                            resource_id=str(project.id),
                            title=project.name,
                            subtitle=project.description,
                            dataset_id=None,
                            created_at=project.created_at.isoformat(),
                        )
                    )
                project_datasets = await self._datasets.list_for_project(
                    project_id=project.id, organization_id=organization_id
                )
                for ds in project_datasets:
                    if dataset_id and ds.id != dataset_id:
                        continue
                    if q in ds.name.lower():
                        results.append(
                            SearchResultDTO(
                                resource_type=SearchResourceType.DATASET.value,
                                resource_id=str(ds.id),
                                title=ds.name,
                                subtitle=ds.description,
                                dataset_id=str(ds.id),
                                created_at=ds.created_at.isoformat(),
                            )
                        )
                    if not dataset_id:
                        await self._search_dataset_scoped(
                            organization_id=organization_id,
                            dataset_id=ds.id,
                            q=q,
                            results=results,
                            per_type=2,
                        )

        if dataset_id:
            await self._search_dataset_scoped(
                organization_id=organization_id,
                dataset_id=dataset_id,
                q=q,
                results=results,
                per_type=per_type,
            )

        session_matches = await self._sessions.search_by_name(
            organization_id=organization_id, query=q, limit=per_type
        )
        for session in session_matches:
            if dataset_id and session.dataset_id != dataset_id:
                continue
            results.append(
                SearchResultDTO(
                    resource_type=SearchResourceType.SESSION.value,
                    resource_id=str(session.id),
                    title=session.name,
                    subtitle=session.status.value,
                    dataset_id=str(session.dataset_id),
                    created_at=session.created_at.isoformat(),
                )
            )

        results.sort(key=lambda r: r.created_at or "", reverse=True)
        return tuple(results[:limit])

    async def _search_dataset_scoped(
        self,
        *,
        organization_id: UUID,
        dataset_id: UUID,
        q: str,
        results: list[SearchResultDTO],
        per_type: int,
    ) -> None:
        for stat in await self._statistics.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=20
        ):
            if q in stat.goal.lower():
                results.append(
                    SearchResultDTO(
                        resource_type=SearchResourceType.STATISTICAL_ANALYSIS.value,
                        resource_id=str(stat.id),
                        title=stat.goal,
                        subtitle="Statistical analysis",
                        dataset_id=str(dataset_id),
                        created_at=stat.created_at.isoformat(),
                    )
                )

        for causal in await self._causal.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=20
        ):
            question = causal.configuration.get("business_question", "")
            label = f"{causal.treatment} → {causal.outcome}"
            if q in label.lower() or q in str(question).lower():
                results.append(
                    SearchResultDTO(
                        resource_type=SearchResourceType.CAUSAL_ANALYSIS.value,
                        resource_id=str(causal.id),
                        title=label,
                        subtitle=str(question) if question else None,
                        dataset_id=str(dataset_id),
                        created_at=causal.created_at.isoformat(),
                    )
                )

        for sim in await self._simulations.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=20
        ):
            if q in sim.name.lower():
                results.append(
                    SearchResultDTO(
                        resource_type=SearchResourceType.SIMULATION.value,
                        resource_id=str(sim.id),
                        title=sim.name,
                        subtitle="Simulation",
                        dataset_id=str(dataset_id),
                        created_at=sim.created_at.isoformat(),
                    )
                )

        for decision in await self._decisions.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=20
        ):
            if q in decision.name.lower():
                results.append(
                    SearchResultDTO(
                        resource_type=SearchResourceType.DECISION.value,
                        resource_id=str(decision.id),
                        title=decision.name,
                        subtitle=decision.primary_objective,
                        dataset_id=str(dataset_id),
                        created_at=decision.created_at.isoformat(),
                    )
                )

        for report in await self._reports.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=20
        ):
            if q in report.name.lower():
                results.append(
                    SearchResultDTO(
                        resource_type=SearchResourceType.REPORT.value,
                        resource_id=str(report.id),
                        title=report.name,
                        subtitle=report.business_objective,
                        dataset_id=str(dataset_id),
                        created_at=report.created_at.isoformat(),
                    )
                )

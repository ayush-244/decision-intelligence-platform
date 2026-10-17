"""SQLAlchemy causal analysis and DAG repositories."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.entities.dag_version import DAGVersion
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.dag_version_repository import DAGVersionRepository
from app.infrastructure.database.mappers.causal import to_causal_analysis_run
from app.infrastructure.database.models.causal_analysis import CausalAnalysisRunModel
from app.infrastructure.database.models.dag_version import DAGVersionModel


def to_dag_version(model: DAGVersionModel) -> DAGVersion:
    return DAGVersion(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        project_id=model.project_id,
        created_by=model.created_by,
        name=model.name,
        description=model.description,
        nodes=tuple(model.nodes_json),
        edges=tuple(model.edges_json),
        variable_roles=dict(model.variable_roles_json),
        version_number=model.version_number,
        is_valid=model.is_valid,
        validation_errors=tuple(model.validation_errors_json),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyCausalAnalysisRepository(CausalAnalysisRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: CausalAnalysisRun) -> CausalAnalysisRun:
        model = CausalAnalysisRunModel(
            id=run.id,
            dataset_id=run.dataset_id,
            version_id=run.version_id,
            organization_id=run.organization_id,
            project_id=run.project_id,
            dag_version_id=run.dag_version_id,
            created_by=run.created_by,
            status=run.status.value,
            treatment=run.treatment,
            outcome=run.outcome,
            estimator=run.estimator.value if run.estimator else None,
            configuration_json=run.configuration,
            result_json=run.result,
            error_message=run.error_message,
            executed_at=run.executed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return to_causal_analysis_run(model)

    async def update(self, run: CausalAnalysisRun) -> CausalAnalysisRun:
        result = await self._session.execute(
            select(CausalAnalysisRunModel).where(CausalAnalysisRunModel.id == run.id)
        )
        model = result.scalar_one()
        model.status = run.status.value
        model.estimator = run.estimator.value if run.estimator else None
        model.configuration_json = run.configuration
        model.result_json = run.result
        model.error_message = run.error_message
        model.executed_at = run.executed_at
        model.dag_version_id = run.dag_version_id
        await self._session.flush()
        return to_causal_analysis_run(model)

    async def get_by_id(
        self, *, analysis_id: UUID, organization_id: UUID
    ) -> CausalAnalysisRun | None:
        result = await self._session.execute(
            select(CausalAnalysisRunModel).where(
                CausalAnalysisRunModel.id == analysis_id,
                CausalAnalysisRunModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_causal_analysis_run(model) if model else None

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[CausalAnalysisRun]:
        result = await self._session.execute(
            select(CausalAnalysisRunModel)
            .where(
                CausalAnalysisRunModel.dataset_id == dataset_id,
                CausalAnalysisRunModel.organization_id == organization_id,
            )
            .order_by(CausalAnalysisRunModel.created_at.desc())
            .limit(limit)
        )
        return [to_causal_analysis_run(m) for m in result.scalars().all()]

    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[CausalAnalysisRun]:
        result = await self._session.execute(
            select(CausalAnalysisRunModel)
            .where(
                CausalAnalysisRunModel.version_id == version_id,
                CausalAnalysisRunModel.organization_id == organization_id,
            )
            .order_by(CausalAnalysisRunModel.created_at.desc())
            .limit(limit)
        )
        return [to_causal_analysis_run(m) for m in result.scalars().all()]


class SqlAlchemyDAGVersionRepository(DAGVersionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, dag: DAGVersion) -> DAGVersion:
        model = DAGVersionModel(
            id=dag.id,
            dataset_id=dag.dataset_id,
            version_id=dag.version_id,
            organization_id=dag.organization_id,
            project_id=dag.project_id,
            created_by=dag.created_by,
            name=dag.name,
            description=dag.description,
            nodes_json=list(dag.nodes),
            edges_json=list(dag.edges),
            variable_roles_json=dag.variable_roles,
            version_number=dag.version_number,
            is_valid=dag.is_valid,
            validation_errors_json=list(dag.validation_errors),
        )
        self._session.add(model)
        await self._session.flush()
        return to_dag_version(model)

    async def update(self, dag: DAGVersion) -> DAGVersion:
        result = await self._session.execute(
            select(DAGVersionModel).where(DAGVersionModel.id == dag.id)
        )
        model = result.scalar_one()
        model.name = dag.name
        model.description = dag.description
        model.nodes_json = list(dag.nodes)
        model.edges_json = list(dag.edges)
        model.variable_roles_json = dag.variable_roles
        model.is_valid = dag.is_valid
        model.validation_errors_json = list(dag.validation_errors)
        await self._session.flush()
        return to_dag_version(model)

    async def get_by_id(self, *, dag_id: UUID, organization_id: UUID) -> DAGVersion | None:
        result = await self._session.execute(
            select(DAGVersionModel).where(
                DAGVersionModel.id == dag_id,
                DAGVersionModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_dag_version(model) if model else None

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DAGVersion]:
        result = await self._session.execute(
            select(DAGVersionModel)
            .where(
                DAGVersionModel.dataset_id == dataset_id,
                DAGVersionModel.organization_id == organization_id,
            )
            .order_by(DAGVersionModel.version_number.desc())
            .limit(limit)
        )
        return [to_dag_version(m) for m in result.scalars().all()]

    async def next_version_number(self, *, dataset_id: UUID) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.max(DAGVersionModel.version_number), 0)).where(
                DAGVersionModel.dataset_id == dataset_id
            )
        )
        current = result.scalar_one()
        return int(current) + 1

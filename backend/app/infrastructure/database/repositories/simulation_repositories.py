"""SQLAlchemy simulation repositories."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.simulation_run import SimulationRun
from app.domain.entities.simulation_scenario import SimulationScenario
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.simulation_scenario_repository import SimulationScenarioRepository
from app.infrastructure.database.mappers.simulation import to_simulation_run, to_simulation_scenario
from app.infrastructure.database.models.simulation_run import SimulationRunModel
from app.infrastructure.database.models.simulation_scenario import SimulationScenarioModel


class SqlAlchemySimulationScenarioRepository(SimulationScenarioRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, scenario: SimulationScenario) -> SimulationScenario:
        model = SimulationScenarioModel(
            id=scenario.id,
            dataset_id=scenario.dataset_id,
            version_id=scenario.version_id,
            organization_id=scenario.organization_id,
            project_id=scenario.project_id,
            created_by=scenario.created_by,
            name=scenario.name,
            description=scenario.description,
            objective=scenario.objective,
            notes=scenario.notes,
            is_baseline=scenario.is_baseline,
            interventions_json=scenario.interventions,
            constraints_json=scenario.constraints,
            version_number=scenario.version_number,
            parent_scenario_id=scenario.parent_scenario_id,
        )
        self._session.add(model)
        await self._session.flush()
        return to_simulation_scenario(model)

    async def update(self, scenario: SimulationScenario) -> SimulationScenario:
        result = await self._session.execute(
            select(SimulationScenarioModel).where(SimulationScenarioModel.id == scenario.id)
        )
        model = result.scalar_one()
        model.name = scenario.name
        model.description = scenario.description
        model.objective = scenario.objective
        model.notes = scenario.notes
        model.is_baseline = scenario.is_baseline
        model.interventions_json = scenario.interventions
        model.constraints_json = scenario.constraints
        model.version_number = scenario.version_number
        await self._session.flush()
        return to_simulation_scenario(model)

    async def get_by_id(
        self, *, scenario_id: UUID, organization_id: UUID
    ) -> SimulationScenario | None:
        result = await self._session.execute(
            select(SimulationScenarioModel).where(
                SimulationScenarioModel.id == scenario_id,
                SimulationScenarioModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_simulation_scenario(model) if model else None

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[SimulationScenario]:
        result = await self._session.execute(
            select(SimulationScenarioModel)
            .where(
                SimulationScenarioModel.dataset_id == dataset_id,
                SimulationScenarioModel.organization_id == organization_id,
            )
            .order_by(SimulationScenarioModel.created_at.desc())
            .limit(limit)
        )
        return [to_simulation_scenario(m) for m in result.scalars()]

    async def next_version_number(self, *, dataset_id: UUID, name: str) -> int:
        result = await self._session.execute(
            select(func.max(SimulationScenarioModel.version_number)).where(
                SimulationScenarioModel.dataset_id == dataset_id,
                SimulationScenarioModel.name == name,
            )
        )
        current = result.scalar()
        return (current or 0) + 1


class SqlAlchemySimulationRunRepository(SimulationRunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: SimulationRun) -> SimulationRun:
        model = SimulationRunModel(
            id=run.id,
            dataset_id=run.dataset_id,
            version_id=run.version_id,
            organization_id=run.organization_id,
            project_id=run.project_id,
            causal_analysis_id=run.causal_analysis_id,
            statistical_analysis_id=run.statistical_analysis_id,
            scenario_id=run.scenario_id,
            created_by=run.created_by,
            status=run.status.value,
            name=run.name,
            configuration_json=run.configuration,
            result_json=run.result,
            error_message=run.error_message,
            executed_at=run.executed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return to_simulation_run(model)

    async def update(self, run: SimulationRun) -> SimulationRun:
        result = await self._session.execute(
            select(SimulationRunModel).where(SimulationRunModel.id == run.id)
        )
        model = result.scalar_one()
        model.status = run.status.value
        model.configuration_json = run.configuration
        model.result_json = run.result
        model.error_message = run.error_message
        model.executed_at = run.executed_at
        await self._session.flush()
        return to_simulation_run(model)

    async def get_by_id(
        self, *, simulation_id: UUID, organization_id: UUID
    ) -> SimulationRun | None:
        result = await self._session.execute(
            select(SimulationRunModel).where(
                SimulationRunModel.id == simulation_id,
                SimulationRunModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_simulation_run(model) if model else None

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[SimulationRun]:
        result = await self._session.execute(
            select(SimulationRunModel)
            .where(
                SimulationRunModel.dataset_id == dataset_id,
                SimulationRunModel.organization_id == organization_id,
            )
            .order_by(SimulationRunModel.created_at.desc())
            .limit(limit)
        )
        return [to_simulation_run(m) for m in result.scalars()]

    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[SimulationRun]:
        result = await self._session.execute(
            select(SimulationRunModel)
            .where(
                SimulationRunModel.version_id == version_id,
                SimulationRunModel.organization_id == organization_id,
            )
            .order_by(SimulationRunModel.created_at.desc())
            .limit(limit)
        )
        return [to_simulation_run(m) for m in result.scalars()]

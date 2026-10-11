"""Scenario lifecycle management — create, version, clone."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from app.domain.entities.simulation_scenario import SimulationScenario
from app.domain.repositories.simulation_scenario_repository import SimulationScenarioRepository
from app.shared.utils.datetime import utc_now


class ScenarioBuilder:
    """Persist and version business scenarios."""

    async def save_scenario(
        self,
        *,
        repo: SimulationScenarioRepository,
        dataset_id: UUID,
        version_id: UUID,
        organization_id: UUID,
        project_id: UUID,
        created_by: UUID,
        name: str,
        interventions: list[dict[str, Any]],
        constraints: list[dict[str, Any]],
        description: str | None = None,
        objective: str | None = None,
        notes: str | None = None,
        is_baseline: bool = False,
        scenario_id: UUID | None = None,
        parent_scenario_id: UUID | None = None,
    ) -> SimulationScenario:
        now = utc_now()
        version_number = await repo.next_version_number(dataset_id=dataset_id, name=name)
        scenario = SimulationScenario(
            id=scenario_id or uuid4(),
            dataset_id=dataset_id,
            version_id=version_id,
            organization_id=organization_id,
            project_id=project_id,
            created_by=created_by,
            name=name,
            description=description,
            objective=objective,
            notes=notes,
            is_baseline=is_baseline,
            interventions=interventions,
            constraints=constraints,
            version_number=version_number,
            parent_scenario_id=parent_scenario_id,
            created_at=now,
            updated_at=now,
        )
        if scenario_id:
            return await repo.update(scenario)
        return await repo.create(scenario)

    async def clone_scenario(
        self,
        *,
        repo: SimulationScenarioRepository,
        source: SimulationScenario,
        created_by: UUID,
        new_name: str | None = None,
    ) -> SimulationScenario:
        return await self.save_scenario(
            repo=repo,
            dataset_id=source.dataset_id,
            version_id=source.version_id,
            organization_id=source.organization_id,
            project_id=source.project_id,
            created_by=created_by,
            name=new_name or f"{source.name} (copy)",
            interventions=list(source.interventions),
            constraints=list(source.constraints),
            description=source.description,
            objective=source.objective,
            notes=source.notes,
            is_baseline=False,
            parent_scenario_id=source.id,
        )

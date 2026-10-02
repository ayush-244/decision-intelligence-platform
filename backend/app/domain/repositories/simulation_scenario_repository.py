"""Simulation scenario repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.simulation_scenario import SimulationScenario


class SimulationScenarioRepository(ABC):
    @abstractmethod
    async def create(self, scenario: SimulationScenario) -> SimulationScenario: ...

    @abstractmethod
    async def update(self, scenario: SimulationScenario) -> SimulationScenario: ...

    @abstractmethod
    async def get_by_id(
        self, *, scenario_id: UUID, organization_id: UUID
    ) -> SimulationScenario | None: ...

    @abstractmethod
    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[SimulationScenario]: ...

    @abstractmethod
    async def next_version_number(self, *, dataset_id: UUID, name: str) -> int: ...

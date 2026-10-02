"""Simulation run repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.simulation_run import SimulationRun


class SimulationRunRepository(ABC):
    @abstractmethod
    async def create(self, run: SimulationRun) -> SimulationRun: ...

    @abstractmethod
    async def update(self, run: SimulationRun) -> SimulationRun: ...

    @abstractmethod
    async def get_by_id(
        self, *, simulation_id: UUID, organization_id: UUID
    ) -> SimulationRun | None: ...

    @abstractmethod
    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[SimulationRun]: ...

    @abstractmethod
    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[SimulationRun]: ...

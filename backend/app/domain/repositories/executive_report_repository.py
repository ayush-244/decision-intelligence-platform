"""Executive report repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.executive_report import ExecutiveReport


class ExecutiveReportRepository(ABC):
    @abstractmethod
    async def create(self, report: ExecutiveReport) -> ExecutiveReport: ...

    @abstractmethod
    async def update(self, report: ExecutiveReport) -> ExecutiveReport: ...

    @abstractmethod
    async def get_by_id(
        self, *, report_id: UUID, organization_id: UUID
    ) -> ExecutiveReport | None: ...

    @abstractmethod
    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[ExecutiveReport]: ...

    @abstractmethod
    async def next_version_number(self, *, dataset_id: UUID, name: str) -> int: ...

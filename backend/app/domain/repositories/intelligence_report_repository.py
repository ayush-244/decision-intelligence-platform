"""Intelligence report repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.intelligence_report import IntelligenceReport


class IntelligenceReportRepository(ABC):
    @abstractmethod
    async def get_by_version(self, *, version_id: UUID) -> IntelligenceReport | None: ...

    @abstractmethod
    async def get_by_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, version_id: UUID | None = None
    ) -> IntelligenceReport | None: ...

    @abstractmethod
    async def upsert(self, report: IntelligenceReport) -> IntelligenceReport: ...

    @abstractmethod
    async def delete_for_version(self, *, version_id: UUID) -> None: ...

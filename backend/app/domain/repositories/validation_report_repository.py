"""Validation report repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.validation_report import ValidationReport


class ValidationReportRepository(ABC):
    @abstractmethod
    async def create(self, report: ValidationReport) -> ValidationReport: ...

    @abstractmethod
    async def get_by_version(self, *, version_id: UUID) -> ValidationReport | None: ...

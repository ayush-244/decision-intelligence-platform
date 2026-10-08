"""Orchestrates the full data intelligence pipeline for a dataset version."""

from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

import polars as pl

from app.application.dto.intelligence import IntelligenceOverviewDTO, IntelligenceReportDTO
from app.application.services.intelligence.analyzers import (
    analyze_columns,
    analyze_correlations,
    analyze_data_quality,
    analyze_distributions,
    analyze_duplicates,
    analyze_feature_relationships,
    analyze_missing_data,
    analyze_outliers,
    schema_summary,
)
from app.application.services.intelligence.frame_loader import DatasetFrameLoader
from app.application.services.intelligence.scoring import (
    assess_analytical_readiness,
    build_recommendations,
    compute_health_score,
)
from app.application.services.intelligence.serialization import to_jsonable
from app.core.config import Settings
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.intelligence_report import IntelligenceReport
from app.domain.repositories.intelligence_report_repository import IntelligenceReportRepository
from app.domain.value_objects.intelligence_status import IntelligenceReportStatus
from app.shared.utils.datetime import utc_now


class IntelligenceEngine:
    """Compute, persist, and retrieve version-scoped intelligence reports."""

    def __init__(
        self,
        settings: Settings,
        frame_loader: DatasetFrameLoader,
        reports: IntelligenceReportRepository,
    ) -> None:
        self._settings = settings
        self._frame_loader = frame_loader
        self._reports = reports

    async def analyze(
        self,
        *,
        dataset: Dataset,
        version: DatasetVersion,
    ) -> IntelligenceReport:
        now = utc_now()
        pending = IntelligenceReport(
            id=uuid4(),
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            status=IntelligenceReportStatus.COMPUTING,
            quality_score=None,
            health_score=None,
            rows_sampled=0,
            total_rows=version.row_count,
            report={},
            error_message=None,
            computed_at=None,
            created_at=now,
            updated_at=now,
        )
        await self._reports.upsert(pending)

        try:
            sampled = await self._frame_loader.load(version=version)
            report_dto = self._compute_report(
                dataset=dataset,
                version=version,
                frame=sampled.frame,
                total_rows=sampled.total_rows,
                sampled_rows=sampled.sampled_rows,
            )
            report_dict = to_jsonable(report_dto)
            completed = IntelligenceReport(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                status=IntelligenceReportStatus.COMPLETED,
                quality_score=report_dto.data_quality.overall_score,
                health_score=report_dto.data_health.overall_score,
                rows_sampled=sampled.sampled_rows,
                total_rows=sampled.total_rows,
                report=report_dict,
                error_message=None,
                computed_at=utc_now(),
                created_at=now,
                updated_at=utc_now(),
            )
            return await self._reports.upsert(completed)
        except Exception as exc:  # noqa: BLE001 — persist failure for observability
            failed = IntelligenceReport(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                status=IntelligenceReportStatus.FAILED,
                quality_score=None,
                health_score=None,
                rows_sampled=0,
                total_rows=version.row_count,
                report={},
                error_message=str(exc),
                computed_at=None,
                created_at=now,
                updated_at=utc_now(),
            )
            await self._reports.upsert(failed)
            raise

    def _compute_report(
        self,
        *,
        dataset: Dataset,
        version: DatasetVersion,
        frame: pl.DataFrame,
        total_rows: int,
        sampled_rows: int,
    ) -> IntelligenceReportDTO:
        quality = analyze_data_quality(frame, self._settings)
        columns = analyze_columns(frame)
        missing = analyze_missing_data(frame)
        outliers = analyze_outliers(frame, self._settings)
        distributions = analyze_distributions(frame)
        correlations = analyze_correlations(frame, self._settings)
        relationships = analyze_feature_relationships(frame, correlations)
        duplicates = analyze_duplicates(frame)
        health = compute_health_score(
            quality=quality,
            missing=missing,
            outliers=outliers,
            columns=columns,
            settings=self._settings,
        )
        readiness = assess_analytical_readiness(
            quality=quality,
            missing=missing,
            columns=columns,
            health=health,
        )
        recommendations = build_recommendations(
            quality=quality,
            missing=missing,
            health=health,
            readiness=readiness,
        )

        trust = "high" if health.overall_score >= 80 else "moderate" if health.overall_score >= 60 else "low"
        findings: list[str] = []
        if quality.constant_columns:
            findings.append(f"{len(quality.constant_columns)} constant column(s) detected.")
        if missing.overall_missing_percentage > 20:
            findings.append(f"Missing data is elevated ({missing.overall_missing_percentage:.1f}%).")
        if duplicates.duplicate_percentage > 5:
            findings.append(f"Duplicate rows: {duplicates.duplicate_percentage:.1f}%.")
        if correlations.multicollinearity_warnings:
            findings.append("Multicollinearity warnings present.")
        if not findings:
            findings.append("No critical issues detected in the sampled data.")

        overview = IntelligenceOverviewDTO(
            dataset_id=dataset.id,
            version_id=version.id,
            version_number=version.version_number,
            row_count=total_rows,
            column_count=frame.width,
            rows_sampled=sampled_rows,
            quality_score=quality.overall_score,
            health_score=health.overall_score,
            trust_level=trust,
            headline_findings=tuple(findings[:8]),
            computed_at=utc_now(),
        )

        return IntelligenceReportDTO(
            overview=overview,
            data_quality=quality,
            schema_summary=schema_summary(frame),
            columns=columns,
            distributions=distributions,
            missing_data=missing,
            outliers=outliers,
            correlations=correlations,
            feature_relationships=relationships,
            duplicates=duplicates,
            data_health=health,
            analytical_readiness=readiness,
            recommendations=recommendations,
        )

    @staticmethod
    def section(report: IntelligenceReport, key: str) -> object:
        if report.status is not IntelligenceReportStatus.COMPLETED:
            return {}
        return report.report.get(key, {})

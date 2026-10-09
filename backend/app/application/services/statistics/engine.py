"""Statistical Analysis Engine — orchestrates the full analysis pipeline."""

from __future__ import annotations

from uuid import uuid4, UUID

import polars as pl

from app.application.dto.statistics import (
    AnalysisRequestDTO,
    AnalysisResultDTO,
    TestRecommendationDTO,
)
from app.application.services.intelligence.frame_loader import DatasetFrameLoader
from app.application.services.statistics.assumptions import AssumptionValidator
from app.application.services.statistics.confidence_intervals import ConfidenceIntervalEngine
from app.application.services.statistics.data_extractor import AnalysisDataExtractor
from app.application.services.statistics.descriptive import DescriptiveStatistics
from app.application.services.statistics.effect_sizes import EffectSizeCalculator
from app.application.services.statistics.executors import StatisticalExecutor
from app.application.services.statistics.interpreter import ResultInterpreter
from app.application.services.statistics.regression import RegressionEngine
from app.application.services.statistics.serialization import to_jsonable
from app.application.services.statistics.test_selector import StatisticalTestSelector
from app.core.config import Settings
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.statistical_analysis import StatisticalAnalysisRun
from app.domain.repositories.statistical_analysis_repository import StatisticalAnalysisRepository
from app.domain.value_objects.statistics import AnalysisRunStatus, StatisticalTestType
from app.shared.utils.datetime import utc_now


class StatisticsEngine:
    """Compute, persist, and retrieve version-scoped statistical analyses."""

    def __init__(
        self,
        settings: Settings,
        frame_loader: DatasetFrameLoader,
        analyses: StatisticalAnalysisRepository,
    ) -> None:
        self._settings = settings
        self._frame_loader = frame_loader
        self._analyses = analyses
        self._selector = StatisticalTestSelector()
        self._assumptions = AssumptionValidator()
        self._executor = StatisticalExecutor()
        self._effect_sizes = EffectSizeCalculator()
        self._confidence = ConfidenceIntervalEngine()
        self._descriptive = DescriptiveStatistics()
        self._regression = RegressionEngine()
        self._interpreter = ResultInterpreter()
        self._extractor = AnalysisDataExtractor()

    async def recommend(
        self,
        *,
        request: AnalysisRequestDTO,
        frame: pl.DataFrame,
    ) -> TestRecommendationDTO:
        return self._selector.recommend(request=request, frame=frame)

    async def analyze(
        self,
        *,
        dataset: Dataset,
        version: DatasetVersion,
        request: AnalysisRequestDTO,
        created_by: UUID,
    ) -> StatisticalAnalysisRun:
        now = utc_now()
        config = to_jsonable(request)
        pending = StatisticalAnalysisRun(
            id=uuid4(),
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            created_by=created_by,
            status=AnalysisRunStatus.RUNNING,
            goal=request.goal,
            test_type=None,
            configuration=config,
            result={},
            error_message=None,
            executed_at=None,
            created_at=now,
            updated_at=now,
        )
        await self._analyses.create(pending)

        try:
            sampled = await self._frame_loader.load(version=version)
            frame = sampled.frame
            result_dto = self._run_pipeline(request=request, frame=frame)
            result_dict = to_jsonable(result_dto)
            completed = StatisticalAnalysisRun(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                created_by=pending.created_by,
                status=AnalysisRunStatus.COMPLETED,
                goal=request.goal,
                test_type=result_dto.test_result.test_type if result_dto.test_result else StatisticalTestType.DESCRIPTIVE,
                configuration=config,
                result=result_dict,
                error_message=None,
                executed_at=utc_now(),
                created_at=now,
                updated_at=utc_now(),
            )
            return await self._analyses.update(completed)
        except Exception as exc:  # noqa: BLE001
            failed = StatisticalAnalysisRun(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                created_by=pending.created_by,
                status=AnalysisRunStatus.FAILED,
                goal=request.goal,
                test_type=request.test_type,
                configuration=config,
                result={},
                error_message=str(exc),
                executed_at=None,
                created_at=now,
                updated_at=utc_now(),
            )
            await self._analyses.update(failed)
            raise

    def _run_pipeline(self, *, request: AnalysisRequestDTO, frame: pl.DataFrame) -> AnalysisResultDTO:
        alpha = self._settings.statistics_significance_level
        confidence_level = request.confidence_level

        recommendation = self._selector.recommend(request=request, frame=frame)
        test_type = request.test_type or recommendation.recommended_test

        extracted = self._extractor.extract(frame, request.variables)
        assumption_report = self._assumptions.validate(
            test_type=test_type, frame=frame, extracted=extracted, alpha=alpha
        )

        # Auto-switch to robust alternative when key assumptions fail
        test_type = self._maybe_switch_test(test_type, assumption_report.alternatives)

        col_names = [v.name for v in request.variables]
        descriptive = self._descriptive.compute(frame, col_names)

        test_result = None
        execution_details: dict = {}
        if test_type is not StatisticalTestType.DESCRIPTIVE:
            test_result, execution_details = self._executor.execute(
                test_type=test_type,
                frame=frame,
                extracted=extracted,
                alpha=alpha,
                reference_value=request.reference_value,
            )

        effect_sizes = self._effect_sizes.compute(
            test_type=test_type,
            extracted=extracted,
            test_statistic=test_result.statistic if test_result else None,
            p_value=test_result.p_value if test_result else None,
            details=execution_details,
        )

        confidence_intervals = self._confidence.compute(
            test_type=test_type,
            extracted=extracted,
            confidence_level=confidence_level,
            details=execution_details,
        )

        regression = self._regression.build_diagnostics(
            test_type=test_type,
            frame=frame,
            extracted=extracted,
            execution_details=execution_details,
        )

        interpretation = self._interpreter.interpret(
            recommendation=recommendation,
            assumption_report=assumption_report,
            test_result=test_result,
            effect_sizes=effect_sizes,
            research_question=request.research_question,
        )

        return AnalysisResultDTO(
            assumption_report=assumption_report,
            test_result=test_result,
            effect_sizes=effect_sizes,
            confidence_intervals=confidence_intervals,
            regression=regression,
            interpretation=interpretation,
            descriptive=descriptive,
        )

    @staticmethod
    def _maybe_switch_test(
        test_type: StatisticalTestType, alternatives: tuple[str, ...]
    ) -> StatisticalTestType:
        alt_set = set(alternatives)
        mapping = {
            StatisticalTestType.INDEPENDENT_TTEST: [
                (StatisticalTestType.WELCH_TTEST.value, StatisticalTestType.WELCH_TTEST),
                (StatisticalTestType.MANN_WHITNEY_U.value, StatisticalTestType.MANN_WHITNEY_U),
            ],
            StatisticalTestType.PAIRED_TTEST: [
                (StatisticalTestType.WILCOXON_SIGNED_RANK.value, StatisticalTestType.WILCOXON_SIGNED_RANK),
            ],
            StatisticalTestType.CHI_SQUARE: [
                (StatisticalTestType.FISHER_EXACT.value, StatisticalTestType.FISHER_EXACT),
            ],
            StatisticalTestType.PEARSON_CORRELATION: [
                (StatisticalTestType.SPEARMAN_CORRELATION.value, StatisticalTestType.SPEARMAN_CORRELATION),
            ],
        }
        for alt_value, alt_type in mapping.get(test_type, []):
            if alt_value in alt_set:
                return alt_type
        return test_type

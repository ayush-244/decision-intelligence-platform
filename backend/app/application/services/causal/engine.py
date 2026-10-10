"""Causal Analysis Engine — orchestrates the full causal inference pipeline."""

from __future__ import annotations

from uuid import UUID, uuid4

import polars as pl

from app.application.dto.causal import CausalAnalysisRequestDTO, CausalAnalysisResultDTO
from app.application.services.causal.assumptions import CausalAssumptionValidator
from app.application.services.causal.dag_manager import DAGManager
from app.application.services.causal.estimator_selector import EstimatorSelector
from app.application.services.causal.identification import IdentificationEngine
from app.application.services.causal.interpreter import CausalInterpreter
from app.application.services.causal.refutation import RefutationEngine
from app.application.services.causal.sensitivity import SensitivityEngine
from app.application.services.causal.serialization import to_jsonable
from app.application.services.causal.treatment_effects import TreatmentEffectEngine
from app.application.services.causal.variable_roles import VariableRoleAnalyzer
from app.application.services.intelligence.frame_loader import DatasetFrameLoader
from app.core.config import Settings
from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.entities.dag_version import DAGVersion
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.dag_version_repository import DAGVersionRepository
from app.domain.value_objects.causal import CausalRunStatus
from app.infrastructure.causal.networkx_graph import NetworkXCausalGraph
from app.shared.utils.datetime import utc_now


class CausalEngine:
    """Discover, identify, estimate, validate, and explain causal effects."""

    def __init__(
        self,
        settings: Settings,
        frame_loader: DatasetFrameLoader,
        analyses: CausalAnalysisRepository,
        dags: DAGVersionRepository,
    ) -> None:
        self._settings = settings
        self._frame_loader = frame_loader
        self._analyses = analyses
        self._dags = dags
        self._dag_manager = DAGManager()
        self._roles = VariableRoleAnalyzer()
        self._identification = IdentificationEngine()
        self._assumptions = CausalAssumptionValidator()
        self._selector = EstimatorSelector()
        self._effects = TreatmentEffectEngine()
        self._refutation = RefutationEngine()
        self._sensitivity = SensitivityEngine()
        self._interpreter = CausalInterpreter()

    async def analyze(
        self,
        *,
        dataset: Dataset,
        version: DatasetVersion,
        request: CausalAnalysisRequestDTO,
        created_by: UUID,
        dag: DAGVersion | None = None,
    ) -> CausalAnalysisRun:
        now = utc_now()
        config = to_jsonable(request)
        pending = CausalAnalysisRun(
            id=uuid4(),
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            dag_version_id=dag.id if dag else None,
            created_by=created_by,
            status=CausalRunStatus.RUNNING,
            treatment=request.treatment,
            outcome=request.outcome,
            estimator=request.estimator,
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
            result_dto = self._run_pipeline(
                frame=sampled.frame,
                request=request,
                dag=dag,
            )
            result_dict = to_jsonable(result_dto)
            completed = CausalAnalysisRun(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                dag_version_id=dag.id if dag else None,
                created_by=created_by,
                status=CausalRunStatus.COMPLETED,
                treatment=request.treatment,
                outcome=request.outcome,
                estimator=result_dto.treatment_effect.estimator,
                configuration=config,
                result=result_dict,
                error_message=None,
                executed_at=utc_now(),
                created_at=now,
                updated_at=utc_now(),
            )
            return await self._analyses.update(completed)
        except Exception as exc:  # noqa: BLE001
            failed = CausalAnalysisRun(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                dag_version_id=dag.id if dag else None,
                created_by=created_by,
                status=CausalRunStatus.FAILED,
                treatment=request.treatment,
                outcome=request.outcome,
                estimator=request.estimator,
                configuration=config,
                result={},
                error_message=str(exc),
                executed_at=None,
                created_at=now,
                updated_at=utc_now(),
            )
            await self._analyses.update(failed)
            raise

    def _run_pipeline(
        self,
        *,
        frame: pl.DataFrame,
        request: CausalAnalysisRequestDTO,
        dag: DAGVersion | None,
    ) -> CausalAnalysisResultDTO:
        variable_roles = self._roles.analyze(
            frame=frame, treatment=request.treatment, outcome=request.outcome,
        )
        roles_dict = self._roles.roles_dict(variable_roles)

        if dag:
            graph = self._dag_manager.build_graph(list(dag.nodes), list(dag.edges))
            dag_dto = self._dag_manager.to_dag_dto(dag)
        else:
            dag_dto = self._dag_manager.suggest_dag(
                frame=frame,
                treatment=request.treatment,
                outcome=request.outcome,
                variable_roles=roles_dict,
            )
            graph = NetworkXCausalGraph.from_dict({
                "nodes": [{"id": n.id, "label": n.label, "role": n.role} for n in dag_dto.nodes],
                "edges": [{"source": e.source, "target": e.target} for e in dag_dto.edges],
            })

        identification = self._identification.identify(
            graph=graph, treatment=request.treatment, outcome=request.outcome,
        )
        adjustment_set = request.adjustment_set or identification.adjustment_set

        assumptions = self._assumptions.validate(
            frame=frame,
            treatment=request.treatment,
            outcome=request.outcome,
            dag_valid=dag_dto.is_valid,
            identified=identification.identified,
            adjustment_set=adjustment_set,
        )

        estimator, selection_reason = self._selector.select(
            frame=frame,
            treatment=request.treatment,
            identification=identification,
            preferred=request.estimator,
        )

        treatment_effect = self._effects.estimate(
            frame=frame,
            treatment=request.treatment,
            outcome=request.outcome,
            estimator=estimator,
            adjustment_set=adjustment_set,
            confidence_level=request.confidence_level,
        )
        treatment_effect = type(treatment_effect)(
            estimator=treatment_effect.estimator,
            ate=treatment_effect.ate,
            att=treatment_effect.att,
            atc=treatment_effect.atc,
            std_error=treatment_effect.std_error,
            confidence_level=treatment_effect.confidence_level,
            ci_lower=treatment_effect.ci_lower,
            ci_upper=treatment_effect.ci_upper,
            p_value=treatment_effect.p_value,
            details={**treatment_effect.details, "selection_reason": selection_reason},
        )

        refutation_results: tuple = ()
        if request.run_refutation:
            refutation_results = self._refutation.refute(
                frame=frame,
                treatment=request.treatment,
                outcome=request.outcome,
                original=treatment_effect,
                adjustment_set=adjustment_set,
            )

        sensitivity = None
        if request.run_sensitivity:
            sensitivity = self._sensitivity.analyze(
                treatment_effect=treatment_effect,
                refutation_results=refutation_results,
                identified=identification.identified,
            )

        interpretation = self._interpreter.interpret(
            business_question=request.business_question,
            treatment=request.treatment,
            outcome=request.outcome,
            identification=identification,
            assumptions=assumptions,
            treatment_effect=treatment_effect,
            refutation_results=refutation_results,
            sensitivity=sensitivity,
        )

        return CausalAnalysisResultDTO(
            variable_roles=variable_roles,
            dag=dag_dto,
            assumption_report=assumptions,
            identification=identification,
            treatment_effect=treatment_effect,
            refutation_results=refutation_results,
            sensitivity=sensitivity,
            interpretation=interpretation,
        )

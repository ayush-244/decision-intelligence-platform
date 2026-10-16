"""In-memory dataset repositories and storage for API integration tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import replace
from uuid import UUID, uuid4

from app.domain.entities.dataset import Dataset
from app.domain.entities.decision_run import DecisionRun
from app.domain.entities.decision_session import DecisionSession
from app.domain.entities.executive_report import ExecutiveReport
from app.domain.entities.session_activity import SessionActivity
from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.entities.dag_version import DAGVersion
from app.domain.entities.simulation_run import SimulationRun
from app.domain.entities.simulation_scenario import SimulationScenario
from app.domain.entities.statistical_analysis import StatisticalAnalysisRun
from app.domain.entities.dataset_file import DatasetFile
from app.domain.entities.dataset_statistics import DatasetStatistics
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.schema_snapshot import SchemaSnapshot
from app.domain.entities.upload_job import UploadJob
from app.domain.entities.validation_report import ValidationReport
from app.domain.ports.storage_provider import StorageProvider, StoredObject
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.decision_session_repository import DecisionSessionRepository
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.domain.repositories.session_activity_repository import SessionActivityRepository
from app.domain.repositories.dataset_file_repository import DatasetFileRepository
from app.domain.entities.intelligence_report import IntelligenceReport
from app.domain.repositories.intelligence_report_repository import IntelligenceReportRepository
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.dag_version_repository import DAGVersionRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.simulation_scenario_repository import SimulationScenarioRepository
from app.domain.repositories.statistical_analysis_repository import StatisticalAnalysisRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_statistics_repository import DatasetStatisticsRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.schema_snapshot_repository import SchemaSnapshotRepository
from app.domain.repositories.upload_job_repository import UploadJobRepository
from app.domain.repositories.validation_report_repository import ValidationReportRepository
from app.domain.value_objects.dataset_status import UploadJobStatus
from app.shared.utils.datetime import utc_now


class InMemoryDatasetStore:
    """Process-local store backing fake dataset repository implementations."""

    def __init__(self) -> None:
        self.datasets: dict[UUID, Dataset] = {}
        self.versions: dict[UUID, DatasetVersion] = {}
        self.files: dict[UUID, DatasetFile] = {}
        self.jobs: dict[UUID, UploadJob] = {}
        self.schemas: dict[UUID, SchemaSnapshot] = {}
        self.validations: dict[UUID, ValidationReport] = {}
        self.statistics: dict[UUID, DatasetStatistics] = {}
        self.intelligence_reports: dict[UUID, IntelligenceReport] = {}
        self.statistical_analyses: dict[UUID, StatisticalAnalysisRun] = {}
        self.causal_analyses: dict[UUID, CausalAnalysisRun] = {}
        self.dag_versions: dict[UUID, DAGVersion] = {}
        self.simulation_scenarios: dict[UUID, SimulationScenario] = {}
        self.simulation_runs: dict[UUID, SimulationRun] = {}
        self.decision_runs: dict[UUID, DecisionRun] = {}
        self.executive_reports: dict[UUID, ExecutiveReport] = {}
        self.decision_sessions: dict[UUID, DecisionSession] = {}
        self.session_activities: dict[UUID, SessionActivity] = {}

    def dataset_repo(self) -> FakeDatasetRepository:
        return FakeDatasetRepository(self)

    def version_repo(self) -> FakeDatasetVersionRepository:
        return FakeDatasetVersionRepository(self)

    def file_repo(self) -> FakeDatasetFileRepository:
        return FakeDatasetFileRepository(self)

    def job_repo(self) -> FakeUploadJobRepository:
        return FakeUploadJobRepository(self)

    def schema_repo(self) -> FakeSchemaSnapshotRepository:
        return FakeSchemaSnapshotRepository(self)

    def validation_repo(self) -> FakeValidationReportRepository:
        return FakeValidationReportRepository(self)

    def statistics_repo(self) -> FakeDatasetStatisticsRepository:
        return FakeDatasetStatisticsRepository(self)

    def intelligence_repo(self) -> FakeIntelligenceReportRepository:
        return FakeIntelligenceReportRepository(self)

    def statistical_analysis_repo(self) -> FakeStatisticalAnalysisRepository:
        return FakeStatisticalAnalysisRepository(self)

    def causal_analysis_repo(self) -> FakeCausalAnalysisRepository:
        return FakeCausalAnalysisRepository(self)

    def dag_version_repo(self) -> FakeDAGVersionRepository:
        return FakeDAGVersionRepository(self)

    def simulation_scenario_repo(self) -> FakeSimulationScenarioRepository:
        return FakeSimulationScenarioRepository(self)

    def simulation_run_repo(self) -> FakeSimulationRunRepository:
        return FakeSimulationRunRepository(self)

    def decision_run_repo(self) -> FakeDecisionRunRepository:
        return FakeDecisionRunRepository(self)

    def executive_report_repo(self) -> FakeExecutiveReportRepository:
        return FakeExecutiveReportRepository(self)

    def decision_session_repo(self) -> FakeDecisionSessionRepository:
        return FakeDecisionSessionRepository(self)

    def session_activity_repo(self) -> FakeSessionActivityRepository:
        return FakeSessionActivityRepository(self)


class FakeDatasetRepository(DatasetRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def get_by_id(self, *, dataset_id: UUID, organization_id: UUID) -> Dataset | None:
        dataset = self._store.datasets.get(dataset_id)
        if dataset is None or dataset.is_deleted or dataset.organization_id != organization_id:
            return None
        return dataset

    async def list_for_project(
        self, *, project_id: UUID, organization_id: UUID
    ) -> list[Dataset]:
        return [
            dataset
            for dataset in self._store.datasets.values()
            if (
                dataset.project_id == project_id
                and dataset.organization_id == organization_id
                and not dataset.is_deleted
            )
        ]

    async def create(
        self,
        *,
        project_id: UUID,
        organization_id: UUID,
        name: str,
        slug: str,
        description: str | None,
        created_by: UUID,
    ) -> Dataset:
        now = utc_now()
        dataset = Dataset(
            id=uuid4(),
            project_id=project_id,
            organization_id=organization_id,
            name=name,
            slug=slug,
            description=description,
            created_by=created_by,
            current_version_id=None,
            created_at=now,
            updated_at=now,
        )
        self._store.datasets[dataset.id] = dataset
        return dataset

    async def update_current_version(self, *, dataset_id: UUID, version_id: UUID) -> None:
        dataset = self._store.datasets.get(dataset_id)
        if dataset is None:
            return
        self._store.datasets[dataset_id] = replace(
            dataset,
            current_version_id=version_id,
            updated_at=utc_now(),
        )

    async def soft_delete(self, *, dataset_id: UUID, organization_id: UUID) -> None:
        dataset = await self.get_by_id(dataset_id=dataset_id, organization_id=organization_id)
        if dataset is None:
            return
        self._store.datasets[dataset_id] = replace(
            dataset,
            deleted_at=utc_now(),
            updated_at=utc_now(),
        )

    async def exists_by_name(
        self, *, project_id: UUID, name: str, exclude_id: UUID | None = None
    ) -> bool:
        for dataset in self._store.datasets.values():
            if dataset.is_deleted or dataset.project_id != project_id:
                continue
            if dataset.name == name and dataset.id != exclude_id:
                return True
        return False


class FakeDatasetVersionRepository(DatasetVersionRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def get_by_id(self, *, version_id: UUID) -> DatasetVersion | None:
        return self._store.versions.get(version_id)

    async def list_for_dataset(self, *, dataset_id: UUID) -> list[DatasetVersion]:
        rows = [version for version in self._store.versions.values() if version.dataset_id == dataset_id]
        return sorted(rows, key=lambda version: version.version_number)

    async def get_latest(self, *, dataset_id: UUID) -> DatasetVersion | None:
        versions = await self.list_for_dataset(dataset_id=dataset_id)
        return versions[-1] if versions else None

    async def next_version_number(self, *, dataset_id: UUID) -> int:
        versions = await self.list_for_dataset(dataset_id=dataset_id)
        return len(versions) + 1

    async def create(self, version: DatasetVersion) -> DatasetVersion:
        self._store.versions[version.id] = version
        return version

    async def find_by_file_hash(
        self, *, organization_id: UUID, file_hash: str
    ) -> DatasetVersion | None:
        for version in self._store.versions.values():
            dataset = self._store.datasets.get(version.dataset_id)
            if dataset is None or dataset.organization_id != organization_id:
                continue
            if version.file_hash == file_hash:
                return version
        return None


class FakeDatasetFileRepository(DatasetFileRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, file: DatasetFile) -> DatasetFile:
        self._store.files[file.id] = file
        return file

    async def get_by_version(self, *, version_id: UUID) -> DatasetFile | None:
        for file in self._store.files.values():
            if file.version_id == version_id:
                return file
        return None


class FakeUploadJobRepository(UploadJobRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, job: UploadJob) -> UploadJob:
        self._store.jobs[job.id] = job
        return job

    async def update_status(
        self,
        *,
        job_id: UUID,
        status: UploadJobStatus,
        version_id: UUID | None = None,
        error_message: str | None = None,
    ) -> None:
        job = self._store.jobs.get(job_id)
        if job is None:
            return
        self._store.jobs[job_id] = replace(
            job,
            status=status,
            version_id=version_id if version_id is not None else job.version_id,
            error_message=error_message,
            updated_at=utc_now(),
        )

    async def get_by_id(self, *, job_id: UUID) -> UploadJob | None:
        return self._store.jobs.get(job_id)


class FakeSchemaSnapshotRepository(SchemaSnapshotRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, snapshot: SchemaSnapshot) -> SchemaSnapshot:
        self._store.schemas[snapshot.id] = snapshot
        return snapshot

    async def get_by_version(self, *, version_id: UUID) -> SchemaSnapshot | None:
        for snapshot in self._store.schemas.values():
            if snapshot.version_id == version_id:
                return snapshot
        return None


class FakeValidationReportRepository(ValidationReportRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, report: ValidationReport) -> ValidationReport:
        self._store.validations[report.id] = report
        return report

    async def get_by_version(self, *, version_id: UUID) -> ValidationReport | None:
        for report in self._store.validations.values():
            if report.version_id == version_id:
                return report
        return None


class FakeDatasetStatisticsRepository(DatasetStatisticsRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, statistics: DatasetStatistics) -> DatasetStatistics:
        self._store.statistics[statistics.id] = statistics
        return statistics

    async def get_by_version(self, *, version_id: UUID) -> DatasetStatistics | None:
        for stats in self._store.statistics.values():
            if stats.version_id == version_id:
                return stats
        return None


class InMemoryStorageProvider(StorageProvider):
    """Ephemeral blob store for tests."""

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    async def store(self, *, key: str, data: bytes, content_type: str) -> StoredObject:
        del content_type
        self._objects[key] = data
        return StoredObject(key=key, size_bytes=len(data))

    async def store_stream(
        self,
        *,
        key: str,
        stream: AsyncIterator[bytes],
        content_type: str,
        expected_size: int | None = None,
    ) -> StoredObject:
        del content_type, expected_size
        chunks: list[bytes] = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        self._objects[key] = data
        return StoredObject(key=key, size_bytes=len(data))

    async def read(self, *, key: str) -> bytes:
        return self._objects[key]

    async def open_stream(self, *, key: str) -> AsyncIterator[bytes]:
        yield self._objects[key]

    async def delete(self, *, key: str) -> None:
        self._objects.pop(key, None)

    async def exists(self, *, key: str) -> bool:
        return key in self._objects


class FakeIntelligenceReportRepository(IntelligenceReportRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def get_by_version(self, *, version_id: UUID) -> IntelligenceReport | None:
        return self._store.intelligence_reports.get(version_id)

    async def get_by_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, version_id: UUID | None = None
    ) -> IntelligenceReport | None:
        for report in self._store.intelligence_reports.values():
            if report.dataset_id != dataset_id or report.organization_id != organization_id:
                continue
            if version_id is None or report.version_id == version_id:
                return report
        return None

    async def upsert(self, report: IntelligenceReport) -> IntelligenceReport:
        self._store.intelligence_reports[report.version_id] = report
        return report

    async def delete_for_version(self, *, version_id: UUID) -> None:
        self._store.intelligence_reports.pop(version_id, None)


class FakeStatisticalAnalysisRepository(StatisticalAnalysisRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, run: StatisticalAnalysisRun) -> StatisticalAnalysisRun:
        self._store.statistical_analyses[run.id] = run
        return run

    async def update(self, run: StatisticalAnalysisRun) -> StatisticalAnalysisRun:
        self._store.statistical_analyses[run.id] = run
        return run

    async def get_by_id(
        self, *, analysis_id: UUID, organization_id: UUID
    ) -> StatisticalAnalysisRun | None:
        run = self._store.statistical_analyses.get(analysis_id)
        if run is None or run.organization_id != organization_id:
            return None
        return run

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[StatisticalAnalysisRun]:
        rows = [
            r
            for r in self._store.statistical_analyses.values()
            if r.dataset_id == dataset_id and r.organization_id == organization_id
        ]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]

    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[StatisticalAnalysisRun]:
        rows = [
            r
            for r in self._store.statistical_analyses.values()
            if r.version_id == version_id and r.organization_id == organization_id
        ]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]


class FakeCausalAnalysisRepository(CausalAnalysisRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, run: CausalAnalysisRun) -> CausalAnalysisRun:
        self._store.causal_analyses[run.id] = run
        return run

    async def update(self, run: CausalAnalysisRun) -> CausalAnalysisRun:
        self._store.causal_analyses[run.id] = run
        return run

    async def get_by_id(
        self, *, analysis_id: UUID, organization_id: UUID
    ) -> CausalAnalysisRun | None:
        run = self._store.causal_analyses.get(analysis_id)
        if run is None or run.organization_id != organization_id:
            return None
        return run

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[CausalAnalysisRun]:
        rows = [
            r for r in self._store.causal_analyses.values()
            if r.dataset_id == dataset_id and r.organization_id == organization_id
        ]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]

    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[CausalAnalysisRun]:
        rows = [
            r for r in self._store.causal_analyses.values()
            if r.version_id == version_id and r.organization_id == organization_id
        ]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]


class FakeDAGVersionRepository(DAGVersionRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, dag: DAGVersion) -> DAGVersion:
        self._store.dag_versions[dag.id] = dag
        return dag

    async def update(self, dag: DAGVersion) -> DAGVersion:
        self._store.dag_versions[dag.id] = dag
        return dag

    async def get_by_id(self, *, dag_id: UUID, organization_id: UUID) -> DAGVersion | None:
        dag = self._store.dag_versions.get(dag_id)
        if dag is None or dag.organization_id != organization_id:
            return None
        return dag

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DAGVersion]:
        rows = [
            d for d in self._store.dag_versions.values()
            if d.dataset_id == dataset_id and d.organization_id == organization_id
        ]
        rows.sort(key=lambda d: d.version_number, reverse=True)
        return rows[:limit]

    async def next_version_number(self, *, dataset_id: UUID) -> int:
        versions = [
            d.version_number for d in self._store.dag_versions.values() if d.dataset_id == dataset_id
        ]
        return (max(versions) if versions else 0) + 1


class FakeSimulationScenarioRepository(SimulationScenarioRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, scenario: SimulationScenario) -> SimulationScenario:
        self._store.simulation_scenarios[scenario.id] = scenario
        return scenario

    async def update(self, scenario: SimulationScenario) -> SimulationScenario:
        self._store.simulation_scenarios[scenario.id] = scenario
        return scenario

    async def get_by_id(
        self, *, scenario_id: UUID, organization_id: UUID
    ) -> SimulationScenario | None:
        scenario = self._store.simulation_scenarios.get(scenario_id)
        if scenario is None or scenario.organization_id != organization_id:
            return None
        return scenario

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[SimulationScenario]:
        rows = [
            s for s in self._store.simulation_scenarios.values()
            if s.dataset_id == dataset_id and s.organization_id == organization_id
        ]
        rows.sort(key=lambda s: s.created_at, reverse=True)
        return rows[:limit]

    async def next_version_number(self, *, dataset_id: UUID, name: str) -> int:
        versions = [
            s.version_number
            for s in self._store.simulation_scenarios.values()
            if s.dataset_id == dataset_id and s.name == name
        ]
        return (max(versions) if versions else 0) + 1


class FakeSimulationRunRepository(SimulationRunRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, run: SimulationRun) -> SimulationRun:
        self._store.simulation_runs[run.id] = run
        return run

    async def update(self, run: SimulationRun) -> SimulationRun:
        self._store.simulation_runs[run.id] = run
        return run

    async def get_by_id(
        self, *, simulation_id: UUID, organization_id: UUID
    ) -> SimulationRun | None:
        run = self._store.simulation_runs.get(simulation_id)
        if run is None or run.organization_id != organization_id:
            return None
        return run

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[SimulationRun]:
        rows = [
            r for r in self._store.simulation_runs.values()
            if r.dataset_id == dataset_id and r.organization_id == organization_id
        ]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]

    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[SimulationRun]:
        rows = [
            r for r in self._store.simulation_runs.values()
            if r.version_id == version_id and r.organization_id == organization_id
        ]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]


class FakeDecisionRunRepository(DecisionRunRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, run: DecisionRun) -> DecisionRun:
        self._store.decision_runs[run.id] = run
        return run

    async def update(self, run: DecisionRun) -> DecisionRun:
        self._store.decision_runs[run.id] = run
        return run

    async def get_by_id(
        self, *, decision_id: UUID, organization_id: UUID
    ) -> DecisionRun | None:
        run = self._store.decision_runs.get(decision_id)
        if run is None or run.organization_id != organization_id:
            return None
        return run

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DecisionRun]:
        rows = [
            r for r in self._store.decision_runs.values()
            if r.dataset_id == dataset_id and r.organization_id == organization_id
        ]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]

    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DecisionRun]:
        rows = [
            r for r in self._store.decision_runs.values()
            if r.version_id == version_id and r.organization_id == organization_id
        ]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]


class FakeExecutiveReportRepository(ExecutiveReportRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, report: ExecutiveReport) -> ExecutiveReport:
        self._store.executive_reports[report.id] = report
        return report

    async def update(self, report: ExecutiveReport) -> ExecutiveReport:
        self._store.executive_reports[report.id] = report
        return report

    async def get_by_id(
        self, *, report_id: UUID, organization_id: UUID
    ) -> ExecutiveReport | None:
        report = self._store.executive_reports.get(report_id)
        if report is None or report.organization_id != organization_id:
            return None
        return report

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[ExecutiveReport]:
        rows = [
            r
            for r in self._store.executive_reports.values()
            if r.dataset_id == dataset_id and r.organization_id == organization_id
        ]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]

    async def next_version_number(self, *, dataset_id: UUID, name: str) -> int:
        existing = [
            r
            for r in self._store.executive_reports.values()
            if r.dataset_id == dataset_id and r.name == name
        ]
        return len(existing) + 1


class FakeDecisionSessionRepository(DecisionSessionRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def create(self, session: DecisionSession) -> DecisionSession:
        self._store.decision_sessions[session.id] = session
        return session

    async def update(self, session: DecisionSession) -> DecisionSession:
        self._store.decision_sessions[session.id] = session
        return session

    async def get_by_id(
        self, *, session_id: UUID, organization_id: UUID
    ) -> DecisionSession | None:
        session = self._store.decision_sessions.get(session_id)
        if session is None or session.organization_id != organization_id:
            return None
        return session

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DecisionSession]:
        rows = [
            s
            for s in self._store.decision_sessions.values()
            if s.dataset_id == dataset_id and s.organization_id == organization_id
        ]
        rows.sort(key=lambda s: s.created_at, reverse=True)
        return rows[:limit]

    async def search_by_name(
        self, *, organization_id: UUID, query: str, limit: int = 20
    ) -> list[DecisionSession]:
        q = query.lower()
        rows = [
            s
            for s in self._store.decision_sessions.values()
            if s.organization_id == organization_id and q in s.name.lower()
        ]
        rows.sort(key=lambda s: s.created_at, reverse=True)
        return rows[:limit]

    async def next_version_number(self, *, dataset_id: UUID, name: str) -> int:
        existing = [
            s
            for s in self._store.decision_sessions.values()
            if s.dataset_id == dataset_id and s.name == name
        ]
        return len(existing) + 1


class FakeSessionActivityRepository(SessionActivityRepository):
    def __init__(self, store: InMemoryDatasetStore) -> None:
        self._store = store

    async def append(self, activity: SessionActivity) -> SessionActivity:
        self._store.session_activities[activity.id] = activity
        return activity

    async def list_for_session(
        self, *, session_id: UUID, organization_id: UUID, limit: int = 100
    ) -> list[SessionActivity]:
        rows = [
            a
            for a in self._store.session_activities.values()
            if a.session_id == session_id and a.organization_id == organization_id
        ]
        rows.sort(key=lambda a: a.created_at, reverse=True)
        return rows[:limit]

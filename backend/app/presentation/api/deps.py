"""Composition root — FastAPI dependency providers.

This module is where abstractions meet implementations. Infrastructure objects
created once at startup (``Database``, ``RedisClient``) live on ``app.state``;
these providers read them and assemble the concrete probes/use-cases/services
that routers depend on. Because routers depend only on the results of these
providers, swapping an implementation (or injecting a fake in tests) requires no
changes to the routers themselves.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.authorization.authorization_service import AuthorizationService
from app.application.services.datasets.file_validator import UploadFileValidator
from app.application.services.datasets.ingestion_pipeline import DatasetIngestionPipeline
from app.application.services.intelligence.engine import IntelligenceEngine
from app.application.services.intelligence.frame_loader import DatasetFrameLoader
from app.application.use_cases.auth import (
    GetCurrentUserUseCase,
    LoginUserUseCase,
    LogoutUserUseCase,
    RefreshAccessTokenUseCase,
    RegisterUserUseCase,
)
from app.application.services.system_info_service import SystemInfoService
from app.application.use_cases.tenancy import (
    CreateOrganizationUseCase,
    CreateProjectUseCase,
    CreateWorkspaceUseCase,
    ListOrganizationsUseCase,
    ListProjectsUseCase,
    ListWorkspacesUseCase,
)
from app.application.use_cases.check_system_health import CheckSystemHealthUseCase
from app.application.use_cases.datasets import (
    DeleteDatasetUseCase,
    GetDatasetPreviewUseCase,
    GetDatasetUseCase,
    ListDatasetVersionsUseCase,
    ListDatasetsUseCase,
    UploadDatasetUseCase,
    UploadDatasetVersionUseCase,
)
from app.application.use_cases.intelligence import (
    AnalyzeDatasetIntelligenceUseCase,
    GetDatasetColumnsIntelligenceUseCase,
    GetDatasetCorrelationsUseCase,
    GetDatasetIntelligenceSummaryUseCase,
    GetDatasetIntelligenceUseCase,
    GetDatasetMissingUseCase,
    GetDatasetOutliersUseCase,
    GetDatasetQualityUseCase,
)
from app.core.config import Settings
from app.domain.ports.health_probe import HealthProbe
from app.domain.ports.storage_provider import StorageProvider
from app.domain.repositories.dataset_file_repository import DatasetFileRepository
from app.domain.repositories.intelligence_report_repository import IntelligenceReportRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_statistics_repository import DatasetStatisticsRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.schema_snapshot_repository import SchemaSnapshotRepository
from app.domain.repositories.upload_job_repository import UploadJobRepository
from app.domain.repositories.validation_report_repository import ValidationReportRepository
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.membership_repository import MembershipRepository
from app.domain.repositories.organization_repository import OrganizationRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.tenant import TenantContext
from app.infrastructure.cache import RedisClient, RedisHealthProbe
from app.infrastructure.database import Database, DatabaseHealthProbe
from app.infrastructure.database.repositories.dataset_repositories import (
    SqlAlchemyDatasetFileRepository,
    SqlAlchemyDatasetRepository,
    SqlAlchemyDatasetStatisticsRepository,
    SqlAlchemyDatasetVersionRepository,
    SqlAlchemyIntelligenceReportRepository,
    SqlAlchemySchemaSnapshotRepository,
    SqlAlchemyUploadJobRepository,
    SqlAlchemyValidationReportRepository,
)
from app.infrastructure.database.repositories.identity_repositories import (
    SqlAlchemyAuditLogRepository,
    SqlAlchemyMembershipRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyWorkspaceRepository,
)
from app.infrastructure.database.session import session_scope
from app.infrastructure.processing.tabular_processor import TabularProcessor
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.storage import LocalStorageProvider
from app.infrastructure.security.password_service import PasswordService
from app.infrastructure.security.refresh_token_service import RefreshTokenService
from app.shared.exceptions import AuthenticationError, BusinessValidationError, ForbiddenError


def get_settings(request: Request) -> Settings:
    """Return the application settings stored on app state."""
    settings: Settings = request.app.state.settings
    return settings


def get_database(request: Request) -> Database:
    """Return the process-wide database manager."""
    database: Database = request.app.state.database
    return database


def get_redis(request: Request) -> RedisClient:
    """Return the process-wide Redis client manager."""
    redis: RedisClient = request.app.state.redis
    return redis


async def get_db_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped, transactional database session."""
    async with session_scope(database.session_factory) as session:
        yield session


def get_health_probes(
    database: Annotated[Database, Depends(get_database)],
    redis: Annotated[RedisClient, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[HealthProbe]:
    """Assemble the set of dependency probes to include in readiness checks."""
    from app.infrastructure.storage import LocalStorageProvider
    from app.infrastructure.storage.health import StorageHealthProbe

    return [
        DatabaseHealthProbe(database.engine),
        RedisHealthProbe(redis.client),
        StorageHealthProbe(LocalStorageProvider(settings)),
    ]


def get_check_system_health_use_case(
    probes: Annotated[list[HealthProbe], Depends(get_health_probes)],
) -> CheckSystemHealthUseCase:
    """Provide the system-health use-case wired with all probes."""
    return CheckSystemHealthUseCase(probes)


def get_system_info_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SystemInfoService:
    """Provide the service exposing static system metadata."""
    return SystemInfoService(settings)


# --- Identity repositories ---------------------------------------------------


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_organization_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrganizationRepository:
    return SqlAlchemyOrganizationRepository(session)


def get_membership_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MembershipRepository:
    return SqlAlchemyMembershipRepository(session)


def get_workspace_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkspaceRepository:
    return SqlAlchemyWorkspaceRepository(session)


def get_project_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProjectRepository:
    return SqlAlchemyProjectRepository(session)


def get_refresh_token_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(session)


def get_audit_log_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuditLogRepository:
    return SqlAlchemyAuditLogRepository(session)


# --- Security services -------------------------------------------------------


def get_password_service() -> PasswordService:
    return PasswordService()


def get_jwt_service(settings: Annotated[Settings, Depends(get_settings)]) -> JwtService:
    return JwtService(settings)


def get_refresh_token_service(
    settings: Annotated[Settings, Depends(get_settings)],
    repository: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> RefreshTokenService:
    return RefreshTokenService(settings, repository)


def get_authorization_service() -> AuthorizationService:
    return AuthorizationService()


# --- Auth use cases ----------------------------------------------------------


def get_register_user_use_case(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
    passwords: Annotated[PasswordService, Depends(get_password_service)],
) -> RegisterUserUseCase:
    return RegisterUserUseCase(users, audit_logs, passwords)


def get_login_user_use_case(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
    passwords: Annotated[PasswordService, Depends(get_password_service)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    refresh_tokens: Annotated[RefreshTokenService, Depends(get_refresh_token_service)],
) -> LoginUserUseCase:
    return LoginUserUseCase(users, audit_logs, passwords, jwt_service, refresh_tokens)


def get_refresh_access_token_use_case(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    refresh_tokens: Annotated[RefreshTokenService, Depends(get_refresh_token_service)],
) -> RefreshAccessTokenUseCase:
    return RefreshAccessTokenUseCase(users, jwt_service, refresh_tokens)


def get_logout_user_use_case(
    refresh_tokens: Annotated[RefreshTokenService, Depends(get_refresh_token_service)],
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> LogoutUserUseCase:
    return LogoutUserUseCase(refresh_tokens, audit_logs)


def get_current_user_use_case(
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> GetCurrentUserUseCase:
    return GetCurrentUserUseCase(users)


async def get_current_user_id(
    request: Request,
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
) -> UUID:
    """Extract and validate the bearer access token."""
    auth_header = request.headers.get("Authorization")
    if auth_header is None or not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid authorization header.")
    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("Missing or invalid authorization header.")
    payload = jwt_service.decode_access_token(token)
    return UUID(payload["sub"])


async def get_tenant_context(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    memberships: Annotated[MembershipRepository, Depends(get_membership_repository)],
    organization_id: Annotated[UUID | None, Header(alias="X-Organization-ID")] = None,
) -> TenantContext:
    """Resolve organization-scoped tenant context from the active org header."""
    if organization_id is None:
        raise BusinessValidationError("X-Organization-ID header is required.")
    membership = await memberships.get_membership(
        user_id=user_id,
        organization_id=organization_id,
    )
    if membership is None or not membership.is_active:
        raise ForbiddenError("You are not a member of this organization.")
    return TenantContext(
        user_id=user_id,
        organization_id=organization_id,
        role=membership.role,
    )


# --- Tenancy use cases -------------------------------------------------------


def get_create_organization_use_case(
    organizations: Annotated[OrganizationRepository, Depends(get_organization_repository)],
    memberships: Annotated[MembershipRepository, Depends(get_membership_repository)],
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> CreateOrganizationUseCase:
    return CreateOrganizationUseCase(organizations, memberships, audit_logs)


def get_list_organizations_use_case(
    organizations: Annotated[OrganizationRepository, Depends(get_organization_repository)],
    memberships: Annotated[MembershipRepository, Depends(get_membership_repository)],
) -> ListOrganizationsUseCase:
    return ListOrganizationsUseCase(organizations, memberships)


def get_create_workspace_use_case(
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> CreateWorkspaceUseCase:
    return CreateWorkspaceUseCase(workspaces, authorization, audit_logs)


def get_list_workspaces_use_case(
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListWorkspacesUseCase:
    return ListWorkspacesUseCase(workspaces, authorization)


def get_create_project_use_case(
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> CreateProjectUseCase:
    return CreateProjectUseCase(workspaces, projects, authorization, audit_logs)


def get_list_projects_use_case(
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListProjectsUseCase:
    return ListProjectsUseCase(workspaces, projects, authorization)


async def get_optional_current_user_id(
    request: Request,
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
) -> UUID | None:
    """Return the user id when a valid bearer token is present, else None."""
    auth_header = request.headers.get("Authorization")
    if auth_header is None or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return None
    try:
        payload = jwt_service.decode_access_token(token)
        return UUID(payload["sub"])
    except AuthenticationError:
        return None


OptionalCurrentUserIdDep = Annotated[UUID | None, Depends(get_optional_current_user_id)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CheckSystemHealthDep = Annotated[
    CheckSystemHealthUseCase, Depends(get_check_system_health_use_case)
]
SystemInfoServiceDep = Annotated[SystemInfoService, Depends(get_system_info_service)]
RegisterUserDep = Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)]
LoginUserDep = Annotated[LoginUserUseCase, Depends(get_login_user_use_case)]
RefreshAccessTokenDep = Annotated[
    RefreshAccessTokenUseCase, Depends(get_refresh_access_token_use_case)
]
LogoutUserDep = Annotated[LogoutUserUseCase, Depends(get_logout_user_use_case)]
GetCurrentUserDep = Annotated[GetCurrentUserUseCase, Depends(get_current_user_use_case)]
CurrentUserIdDep = Annotated[UUID, Depends(get_current_user_id)]
TenantContextDep = Annotated[TenantContext, Depends(get_tenant_context)]
CreateOrganizationDep = Annotated[
    CreateOrganizationUseCase, Depends(get_create_organization_use_case)
]
ListOrganizationsDep = Annotated[
    ListOrganizationsUseCase, Depends(get_list_organizations_use_case)
]
CreateWorkspaceDep = Annotated[CreateWorkspaceUseCase, Depends(get_create_workspace_use_case)]
ListWorkspacesDep = Annotated[ListWorkspacesUseCase, Depends(get_list_workspaces_use_case)]
CreateProjectDep = Annotated[CreateProjectUseCase, Depends(get_create_project_use_case)]
ListProjectsDep = Annotated[ListProjectsUseCase, Depends(get_list_projects_use_case)]


# --- Dataset repositories ----------------------------------------------------


def get_dataset_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DatasetRepository:
    return SqlAlchemyDatasetRepository(session)


def get_dataset_version_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DatasetVersionRepository:
    return SqlAlchemyDatasetVersionRepository(session)


def get_dataset_file_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DatasetFileRepository:
    return SqlAlchemyDatasetFileRepository(session)


def get_upload_job_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UploadJobRepository:
    return SqlAlchemyUploadJobRepository(session)


def get_schema_snapshot_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SchemaSnapshotRepository:
    return SqlAlchemySchemaSnapshotRepository(session)


def get_validation_report_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ValidationReportRepository:
    return SqlAlchemyValidationReportRepository(session)


def get_dataset_statistics_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DatasetStatisticsRepository:
    return SqlAlchemyDatasetStatisticsRepository(session)


def get_storage_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageProvider:
    return LocalStorageProvider(settings)


def get_upload_file_validator(
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadFileValidator:
    return UploadFileValidator(settings)


def get_tabular_processor(
    settings: Annotated[Settings, Depends(get_settings)],
) -> TabularProcessor:
    return TabularProcessor(settings)


def get_dataset_ingestion_pipeline(
    settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
    validator: Annotated[UploadFileValidator, Depends(get_upload_file_validator)],
    processor: Annotated[TabularProcessor, Depends(get_tabular_processor)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    file_repo: Annotated[DatasetFileRepository, Depends(get_dataset_file_repository)],
    jobs: Annotated[UploadJobRepository, Depends(get_upload_job_repository)],
    schemas: Annotated[SchemaSnapshotRepository, Depends(get_schema_snapshot_repository)],
    validations: Annotated[ValidationReportRepository, Depends(get_validation_report_repository)],
    statistics: Annotated[DatasetStatisticsRepository, Depends(get_dataset_statistics_repository)],
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> DatasetIngestionPipeline:
    return DatasetIngestionPipeline(
        settings,
        storage,
        validator,
        processor,
        datasets,
        versions,
        file_repo,
        jobs,
        schemas,
        validations,
        statistics,
        audit_logs,
    )


def get_upload_dataset_use_case(
    pipeline: Annotated[DatasetIngestionPipeline, Depends(get_dataset_ingestion_pipeline)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> UploadDatasetUseCase:
    return UploadDatasetUseCase(pipeline, projects, workspaces, authorization)


def get_upload_dataset_version_use_case(
    pipeline: Annotated[DatasetIngestionPipeline, Depends(get_dataset_ingestion_pipeline)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> UploadDatasetVersionUseCase:
    return UploadDatasetVersionUseCase(
        pipeline, datasets, projects, workspaces, authorization
    )


def get_list_datasets_use_case(
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListDatasetsUseCase:
    return ListDatasetsUseCase(datasets, versions, projects, workspaces, authorization)


def get_get_dataset_use_case(
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDatasetUseCase:
    return GetDatasetUseCase(datasets, versions, projects, workspaces, authorization)


def get_list_dataset_versions_use_case(
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListDatasetVersionsUseCase:
    return ListDatasetVersionsUseCase(
        datasets, versions, projects, workspaces, authorization
    )


def get_get_dataset_preview_use_case(
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    schemas: Annotated[SchemaSnapshotRepository, Depends(get_schema_snapshot_repository)],
    validations: Annotated[ValidationReportRepository, Depends(get_validation_report_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GetDatasetPreviewUseCase:
    return GetDatasetPreviewUseCase(
        datasets,
        versions,
        schemas,
        validations,
        projects,
        workspaces,
        authorization,
        settings,
    )


def get_delete_dataset_use_case(
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> DeleteDatasetUseCase:
    return DeleteDatasetUseCase(datasets, projects, workspaces, authorization)


UploadDatasetDep = Annotated[UploadDatasetUseCase, Depends(get_upload_dataset_use_case)]
UploadDatasetVersionDep = Annotated[
    UploadDatasetVersionUseCase, Depends(get_upload_dataset_version_use_case)
]
ListDatasetsDep = Annotated[ListDatasetsUseCase, Depends(get_list_datasets_use_case)]
GetDatasetDep = Annotated[GetDatasetUseCase, Depends(get_get_dataset_use_case)]
ListDatasetVersionsDep = Annotated[
    ListDatasetVersionsUseCase, Depends(get_list_dataset_versions_use_case)
]
GetDatasetPreviewDep = Annotated[
    GetDatasetPreviewUseCase, Depends(get_get_dataset_preview_use_case)
]
DeleteDatasetDep = Annotated[DeleteDatasetUseCase, Depends(get_delete_dataset_use_case)]


# --- Intelligence (Phase 4) --------------------------------------------------


def get_intelligence_report_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IntelligenceReportRepository:
    return SqlAlchemyIntelligenceReportRepository(session)


def get_dataset_frame_loader(
    settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> DatasetFrameLoader:
    return DatasetFrameLoader(settings, storage)


def get_intelligence_engine(
    settings: Annotated[Settings, Depends(get_settings)],
    frame_loader: Annotated[DatasetFrameLoader, Depends(get_dataset_frame_loader)],
    reports: Annotated[IntelligenceReportRepository, Depends(get_intelligence_report_repository)],
) -> IntelligenceEngine:
    return IntelligenceEngine(settings, frame_loader, reports)


def get_analyze_dataset_intelligence_use_case(
    engine: Annotated[IntelligenceEngine, Depends(get_intelligence_engine)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> AnalyzeDatasetIntelligenceUseCase:
    return AnalyzeDatasetIntelligenceUseCase(
        engine, datasets, versions, projects, workspaces, authorization
    )


def get_get_dataset_intelligence_use_case(
    reports: Annotated[IntelligenceReportRepository, Depends(get_intelligence_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDatasetIntelligenceUseCase:
    return GetDatasetIntelligenceUseCase(
        reports, datasets, versions, projects, workspaces, authorization
    )


def get_get_dataset_quality_use_case(
    reports: Annotated[IntelligenceReportRepository, Depends(get_intelligence_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDatasetQualityUseCase:
    return GetDatasetQualityUseCase(
        reports, datasets, versions, projects, workspaces, authorization
    )


def get_get_dataset_columns_intelligence_use_case(
    reports: Annotated[IntelligenceReportRepository, Depends(get_intelligence_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDatasetColumnsIntelligenceUseCase:
    return GetDatasetColumnsIntelligenceUseCase(
        reports, datasets, versions, projects, workspaces, authorization
    )


def get_get_dataset_correlations_use_case(
    reports: Annotated[IntelligenceReportRepository, Depends(get_intelligence_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDatasetCorrelationsUseCase:
    return GetDatasetCorrelationsUseCase(
        reports, datasets, versions, projects, workspaces, authorization
    )


def get_get_dataset_outliers_use_case(
    reports: Annotated[IntelligenceReportRepository, Depends(get_intelligence_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDatasetOutliersUseCase:
    return GetDatasetOutliersUseCase(
        reports, datasets, versions, projects, workspaces, authorization
    )


def get_get_dataset_missing_use_case(
    reports: Annotated[IntelligenceReportRepository, Depends(get_intelligence_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDatasetMissingUseCase:
    return GetDatasetMissingUseCase(
        reports, datasets, versions, projects, workspaces, authorization
    )


def get_get_dataset_intelligence_summary_use_case(
    reports: Annotated[IntelligenceReportRepository, Depends(get_intelligence_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDatasetIntelligenceSummaryUseCase:
    return GetDatasetIntelligenceSummaryUseCase(
        reports, datasets, versions, projects, workspaces, authorization
    )


AnalyzeDatasetIntelligenceDep = Annotated[
    AnalyzeDatasetIntelligenceUseCase, Depends(get_analyze_dataset_intelligence_use_case)
]
GetDatasetIntelligenceDep = Annotated[
    GetDatasetIntelligenceUseCase, Depends(get_get_dataset_intelligence_use_case)
]
GetDatasetQualityDep = Annotated[GetDatasetQualityUseCase, Depends(get_get_dataset_quality_use_case)]
GetDatasetColumnsIntelligenceDep = Annotated[
    GetDatasetColumnsIntelligenceUseCase, Depends(get_get_dataset_columns_intelligence_use_case)
]
GetDatasetCorrelationsDep = Annotated[
    GetDatasetCorrelationsUseCase, Depends(get_get_dataset_correlations_use_case)
]
GetDatasetOutliersDep = Annotated[
    GetDatasetOutliersUseCase, Depends(get_get_dataset_outliers_use_case)
]
GetDatasetMissingDep = Annotated[GetDatasetMissingUseCase, Depends(get_get_dataset_missing_use_case)]
GetDatasetIntelligenceSummaryDep = Annotated[
    GetDatasetIntelligenceSummaryUseCase, Depends(get_get_dataset_intelligence_summary_use_case)
]


# --- Statistics (Phase 5) ----------------------------------------------------


from app.application.services.statistics.engine import StatisticsEngine  # noqa: E402
from app.application.use_cases.statistics import (  # noqa: E402
    GetStatisticalAnalysisUseCase,
    GetStatisticalRecommendationsUseCase,
    ListStatisticalAnalysisHistoryUseCase,
    RunStatisticalAnalysisUseCase,
)
from app.domain.repositories.statistical_analysis_repository import (  # noqa: E402
    StatisticalAnalysisRepository,
)
from app.infrastructure.database.repositories.statistics_repositories import (  # noqa: E402
    SqlAlchemyStatisticalAnalysisRepository,
)


def get_statistical_analysis_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StatisticalAnalysisRepository:
    return SqlAlchemyStatisticalAnalysisRepository(session)


def get_statistics_engine(
    settings: Annotated[Settings, Depends(get_settings)],
    frame_loader: Annotated[DatasetFrameLoader, Depends(get_dataset_frame_loader)],
    analyses: Annotated[StatisticalAnalysisRepository, Depends(get_statistical_analysis_repository)],
) -> StatisticsEngine:
    return StatisticsEngine(settings, frame_loader, analyses)


def get_run_statistical_analysis_use_case(
    engine: Annotated[StatisticsEngine, Depends(get_statistics_engine)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> RunStatisticalAnalysisUseCase:
    return RunStatisticalAnalysisUseCase(
        engine, datasets, versions, projects, workspaces, authorization
    )


def get_get_statistical_analysis_use_case(
    analyses: Annotated[StatisticalAnalysisRepository, Depends(get_statistical_analysis_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetStatisticalAnalysisUseCase:
    return GetStatisticalAnalysisUseCase(analyses, authorization)


def get_list_statistical_analysis_history_use_case(
    analyses: Annotated[StatisticalAnalysisRepository, Depends(get_statistical_analysis_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListStatisticalAnalysisHistoryUseCase:
    return ListStatisticalAnalysisHistoryUseCase(
        analyses, datasets, versions, projects, workspaces, authorization
    )


def get_get_statistical_recommendations_use_case(
    engine: Annotated[StatisticsEngine, Depends(get_statistics_engine)],
    frame_loader: Annotated[DatasetFrameLoader, Depends(get_dataset_frame_loader)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetStatisticalRecommendationsUseCase:
    return GetStatisticalRecommendationsUseCase(
        engine, frame_loader, datasets, versions, projects, workspaces, authorization
    )


RunStatisticalAnalysisDep = Annotated[
    RunStatisticalAnalysisUseCase, Depends(get_run_statistical_analysis_use_case)
]
GetStatisticalAnalysisDep = Annotated[
    GetStatisticalAnalysisUseCase, Depends(get_get_statistical_analysis_use_case)
]
ListStatisticalAnalysisHistoryDep = Annotated[
    ListStatisticalAnalysisHistoryUseCase, Depends(get_list_statistical_analysis_history_use_case)
]
GetStatisticalRecommendationsDep = Annotated[
    GetStatisticalRecommendationsUseCase, Depends(get_get_statistical_recommendations_use_case)
]


# --- Causal inference (Phase 6) ----------------------------------------------


from app.application.services.causal.engine import CausalEngine  # noqa: E402
from app.application.use_cases.causal import (  # noqa: E402
    CreateDAGUseCase,
    GetCausalAnalysisUseCase,
    GetDAGUseCase,
    ListCausalAnalysisHistoryUseCase,
    RefuteCausalAnalysisUseCase,
    RunCausalAnalysisUseCase,
    UpdateDAGUseCase,
)
from app.domain.repositories.causal_analysis_repository import (  # noqa: E402
    CausalAnalysisRepository,
)
from app.domain.repositories.dag_version_repository import DAGVersionRepository  # noqa: E402
from app.infrastructure.database.repositories.causal_repositories import (  # noqa: E402
    SqlAlchemyCausalAnalysisRepository,
    SqlAlchemyDAGVersionRepository,
)


def get_causal_analysis_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CausalAnalysisRepository:
    return SqlAlchemyCausalAnalysisRepository(session)


def get_dag_version_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DAGVersionRepository:
    return SqlAlchemyDAGVersionRepository(session)


def get_causal_engine(
    settings: Annotated[Settings, Depends(get_settings)],
    frame_loader: Annotated[DatasetFrameLoader, Depends(get_dataset_frame_loader)],
    analyses: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
    dags: Annotated[DAGVersionRepository, Depends(get_dag_version_repository)],
) -> CausalEngine:
    return CausalEngine(settings, frame_loader, analyses, dags)


def get_run_causal_analysis_use_case(
    engine: Annotated[CausalEngine, Depends(get_causal_engine)],
    dags: Annotated[DAGVersionRepository, Depends(get_dag_version_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> RunCausalAnalysisUseCase:
    return RunCausalAnalysisUseCase(
        engine, dags, datasets, versions, projects, workspaces, authorization
    )


def get_get_causal_analysis_use_case(
    analyses: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetCausalAnalysisUseCase:
    return GetCausalAnalysisUseCase(analyses, authorization)


def get_list_causal_analysis_history_use_case(
    analyses: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListCausalAnalysisHistoryUseCase:
    return ListCausalAnalysisHistoryUseCase(
        analyses, datasets, versions, projects, workspaces, authorization
    )


def get_create_dag_use_case(
    dags: Annotated[DAGVersionRepository, Depends(get_dag_version_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> CreateDAGUseCase:
    return CreateDAGUseCase(dags, datasets, versions, projects, workspaces, authorization)


def get_update_dag_use_case(
    dags: Annotated[DAGVersionRepository, Depends(get_dag_version_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> UpdateDAGUseCase:
    return UpdateDAGUseCase(dags, datasets, versions, projects, workspaces, authorization)


def get_get_dag_use_case(
    dags: Annotated[DAGVersionRepository, Depends(get_dag_version_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDAGUseCase:
    return GetDAGUseCase(dags, authorization)


def get_refute_causal_analysis_use_case(
    analyses: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
    frame_loader: Annotated[DatasetFrameLoader, Depends(get_dataset_frame_loader)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> RefuteCausalAnalysisUseCase:
    return RefuteCausalAnalysisUseCase(
        analyses, frame_loader, datasets, versions, projects, workspaces, authorization
    )


RunCausalAnalysisDep = Annotated[RunCausalAnalysisUseCase, Depends(get_run_causal_analysis_use_case)]
GetCausalAnalysisDep = Annotated[GetCausalAnalysisUseCase, Depends(get_get_causal_analysis_use_case)]
ListCausalAnalysisHistoryDep = Annotated[
    ListCausalAnalysisHistoryUseCase, Depends(get_list_causal_analysis_history_use_case)
]
CreateDAGDep = Annotated[CreateDAGUseCase, Depends(get_create_dag_use_case)]
UpdateDAGDep = Annotated[UpdateDAGUseCase, Depends(get_update_dag_use_case)]
GetDAGDep = Annotated[GetDAGUseCase, Depends(get_get_dag_use_case)]
RefuteCausalAnalysisDep = Annotated[
    RefuteCausalAnalysisUseCase, Depends(get_refute_causal_analysis_use_case)
]

# --- Simulation engine (Phase 7) ---------------------------------------------


from app.application.services.simulation.engine import SimulationEngine  # noqa: E402
from app.application.use_cases.simulation import (  # noqa: E402
    CalculateROIUseCase,
    CalculateRiskUseCase,
    CreateScenarioUseCase,
    GetScenarioUseCase,
    GetSimulationUseCase,
    ListScenariosUseCase,
    ListSimulationHistoryUseCase,
    RunSimulationUseCase,
    UpdateScenarioUseCase,
)
from app.domain.repositories.simulation_run_repository import SimulationRunRepository  # noqa: E402
from app.domain.repositories.simulation_scenario_repository import (  # noqa: E402
    SimulationScenarioRepository,
)
from app.infrastructure.database.repositories.simulation_repositories import (  # noqa: E402
    SqlAlchemySimulationRunRepository,
    SqlAlchemySimulationScenarioRepository,
)


def get_simulation_run_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SimulationRunRepository:
    return SqlAlchemySimulationRunRepository(session)


def get_simulation_scenario_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SimulationScenarioRepository:
    return SqlAlchemySimulationScenarioRepository(session)


def get_simulation_engine(
    settings: Annotated[Settings, Depends(get_settings)],
    frame_loader: Annotated[DatasetFrameLoader, Depends(get_dataset_frame_loader)],
    runs: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    scenarios: Annotated[SimulationScenarioRepository, Depends(get_simulation_scenario_repository)],
    causal_analyses: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
) -> SimulationEngine:
    return SimulationEngine(settings, frame_loader, runs, scenarios, causal_analyses)


def get_run_simulation_use_case(
    engine: Annotated[SimulationEngine, Depends(get_simulation_engine)],
    scenarios: Annotated[SimulationScenarioRepository, Depends(get_simulation_scenario_repository)],
    causal_analyses: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> RunSimulationUseCase:
    return RunSimulationUseCase(
        engine, scenarios, causal_analyses, datasets, versions, projects, workspaces, authorization
    )


def get_get_simulation_use_case(
    runs: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetSimulationUseCase:
    return GetSimulationUseCase(runs, authorization)


def get_list_simulation_history_use_case(
    runs: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListSimulationHistoryUseCase:
    return ListSimulationHistoryUseCase(
        runs, datasets, versions, projects, workspaces, authorization
    )


def get_create_scenario_use_case(
    scenarios: Annotated[SimulationScenarioRepository, Depends(get_simulation_scenario_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> CreateScenarioUseCase:
    return CreateScenarioUseCase(
        scenarios, datasets, versions, projects, workspaces, authorization
    )


def get_update_scenario_use_case(
    scenarios: Annotated[SimulationScenarioRepository, Depends(get_simulation_scenario_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> UpdateScenarioUseCase:
    return UpdateScenarioUseCase(
        scenarios, datasets, versions, projects, workspaces, authorization
    )


def get_list_scenarios_use_case(
    scenarios: Annotated[SimulationScenarioRepository, Depends(get_simulation_scenario_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListScenariosUseCase:
    return ListScenariosUseCase(
        scenarios, datasets, versions, projects, workspaces, authorization
    )


def get_get_scenario_use_case(
    scenarios: Annotated[SimulationScenarioRepository, Depends(get_simulation_scenario_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetScenarioUseCase:
    return GetScenarioUseCase(scenarios, authorization)


def get_calculate_roi_use_case(
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> CalculateROIUseCase:
    return CalculateROIUseCase(authorization)


def get_calculate_risk_use_case(
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> CalculateRiskUseCase:
    return CalculateRiskUseCase(authorization)


RunSimulationDep = Annotated[RunSimulationUseCase, Depends(get_run_simulation_use_case)]
GetSimulationDep = Annotated[GetSimulationUseCase, Depends(get_get_simulation_use_case)]
ListSimulationHistoryDep = Annotated[
    ListSimulationHistoryUseCase, Depends(get_list_simulation_history_use_case)
]
CreateScenarioDep = Annotated[CreateScenarioUseCase, Depends(get_create_scenario_use_case)]
UpdateScenarioDep = Annotated[UpdateScenarioUseCase, Depends(get_update_scenario_use_case)]
ListScenariosDep = Annotated[ListScenariosUseCase, Depends(get_list_scenarios_use_case)]
GetScenarioDep = Annotated[GetScenarioUseCase, Depends(get_get_scenario_use_case)]
CalculateROIDep = Annotated[CalculateROIUseCase, Depends(get_calculate_roi_use_case)]
CalculateRiskDep = Annotated[CalculateRiskUseCase, Depends(get_calculate_risk_use_case)]

# --- Decision intelligence (Phase 8) -----------------------------------------


from app.application.services.decision.engine import DecisionEngine  # noqa: E402
from app.application.use_cases.decision import (  # noqa: E402
    GetDecisionUseCase,
    GetPrioritiesUseCase,
    GetRecommendationsUseCase,
    GetTradeoffsUseCase,
    ListDecisionHistoryUseCase,
    ListObjectivesUseCase,
    RunDecisionAnalysisUseCase,
)
from app.domain.repositories.decision_run_repository import DecisionRunRepository  # noqa: E402
from app.infrastructure.database.repositories.decision_repositories import (  # noqa: E402
    SqlAlchemyDecisionRunRepository,
)


def get_decision_run_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DecisionRunRepository:
    return SqlAlchemyDecisionRunRepository(session)


def get_decision_engine(
    settings: Annotated[Settings, Depends(get_settings)],
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    simulations: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    causal_analyses: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
) -> DecisionEngine:
    return DecisionEngine(settings, decisions, simulations, causal_analyses)


def get_run_decision_analysis_use_case(
    engine: Annotated[DecisionEngine, Depends(get_decision_engine)],
    simulations: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> RunDecisionAnalysisUseCase:
    return RunDecisionAnalysisUseCase(
        engine, simulations, datasets, versions, projects, workspaces, authorization
    )


def get_get_decision_use_case(
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDecisionUseCase:
    return GetDecisionUseCase(decisions, authorization)


def get_list_decision_history_use_case(
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListDecisionHistoryUseCase:
    return ListDecisionHistoryUseCase(
        decisions, datasets, versions, projects, workspaces, authorization
    )


def get_list_objectives_use_case(
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListObjectivesUseCase:
    return ListObjectivesUseCase(authorization)


def get_get_recommendations_use_case(
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetRecommendationsUseCase:
    return GetRecommendationsUseCase(decisions, authorization)


def get_get_tradeoffs_use_case(
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetTradeoffsUseCase:
    return GetTradeoffsUseCase(decisions, authorization)


def get_get_priorities_use_case(
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetPrioritiesUseCase:
    return GetPrioritiesUseCase(decisions, authorization)


RunDecisionAnalysisDep = Annotated[
    RunDecisionAnalysisUseCase, Depends(get_run_decision_analysis_use_case)
]
GetDecisionDep = Annotated[GetDecisionUseCase, Depends(get_get_decision_use_case)]
ListDecisionHistoryDep = Annotated[
    ListDecisionHistoryUseCase, Depends(get_list_decision_history_use_case)
]
ListObjectivesDep = Annotated[ListObjectivesUseCase, Depends(get_list_objectives_use_case)]
GetRecommendationsDep = Annotated[
    GetRecommendationsUseCase, Depends(get_get_recommendations_use_case)
]
GetTradeoffsDep = Annotated[GetTradeoffsUseCase, Depends(get_get_tradeoffs_use_case)]
GetPrioritiesDep = Annotated[GetPrioritiesUseCase, Depends(get_get_priorities_use_case)]


# ---------------------------------------------------------------------------
# Phase 9 — Executive Intelligence
# ---------------------------------------------------------------------------
from app.application.services.executive.engine import ExecutiveReportEngine  # noqa: E402
from app.application.use_cases.executive import (  # noqa: E402
    ExportExecutiveReportUseCase,
    GenerateExecutiveReportUseCase,
    GetExecutiveDashboardUseCase,
    GetExecutiveReportUseCase,
    ListExecutiveReportsUseCase,
)
from app.domain.repositories.executive_report_repository import (  # noqa: E402
    ExecutiveReportRepository,
)
from app.infrastructure.database.repositories.executive_repositories import (  # noqa: E402
    SqlAlchemyExecutiveReportRepository,
)


def get_executive_report_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExecutiveReportRepository:
    return SqlAlchemyExecutiveReportRepository(session)


def get_executive_report_engine(
    settings: Annotated[Settings, Depends(get_settings)],
    reports: Annotated[ExecutiveReportRepository, Depends(get_executive_report_repository)],
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    simulations: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    causal_analyses: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
) -> ExecutiveReportEngine:
    return ExecutiveReportEngine(settings, reports, decisions, simulations, causal_analyses)


def get_generate_executive_report_use_case(
    engine: Annotated[ExecutiveReportEngine, Depends(get_executive_report_engine)],
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GenerateExecutiveReportUseCase:
    return GenerateExecutiveReportUseCase(
        engine, decisions, datasets, versions, projects, workspaces, authorization
    )


def get_get_executive_report_use_case(
    reports: Annotated[ExecutiveReportRepository, Depends(get_executive_report_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetExecutiveReportUseCase:
    return GetExecutiveReportUseCase(reports, authorization)


def get_list_executive_reports_use_case(
    reports: Annotated[ExecutiveReportRepository, Depends(get_executive_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListExecutiveReportsUseCase:
    return ListExecutiveReportsUseCase(
        reports, datasets, versions, projects, workspaces, authorization
    )


def get_export_executive_report_use_case(
    reports: Annotated[ExecutiveReportRepository, Depends(get_executive_report_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ExportExecutiveReportUseCase:
    return ExportExecutiveReportUseCase(reports, authorization)


def get_executive_dashboard_use_case(
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    reports: Annotated[ExecutiveReportRepository, Depends(get_executive_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetExecutiveDashboardUseCase:
    return GetExecutiveDashboardUseCase(
        decisions, reports, datasets, versions, projects, workspaces, authorization
    )


GenerateExecutiveReportDep = Annotated[
    GenerateExecutiveReportUseCase, Depends(get_generate_executive_report_use_case)
]
GetExecutiveReportDep = Annotated[
    GetExecutiveReportUseCase, Depends(get_get_executive_report_use_case)
]
ListExecutiveReportsDep = Annotated[
    ListExecutiveReportsUseCase, Depends(get_list_executive_reports_use_case)
]
ExportExecutiveReportDep = Annotated[
    ExportExecutiveReportUseCase, Depends(get_export_executive_report_use_case)
]
GetExecutiveDashboardDep = Annotated[
    GetExecutiveDashboardUseCase, Depends(get_executive_dashboard_use_case)
]


# ---------------------------------------------------------------------------
# Phase 10 — Unified Decision Workspace
# ---------------------------------------------------------------------------
from app.application.services.workspace.comparison import ComparisonEngine  # noqa: E402
from app.application.services.workspace.search import WorkspaceSearchEngine  # noqa: E402
from app.application.services.workspace.session_engine import DecisionSessionEngine  # noqa: E402
from app.application.services.workspace.timeline import TimelineEngine  # noqa: E402
from app.application.use_cases.workspace import (  # noqa: E402
    AddSessionCommentUseCase,
    CompareSessionsUseCase,
    CreateDecisionSessionUseCase,
    GetDecisionSessionUseCase,
    GetSessionTimelineUseCase,
    ListDecisionSessionsUseCase,
    ListWorkspaceActivityUseCase,
    UpdateDecisionSessionUseCase,
    WorkspaceSearchUseCase,
)
from app.domain.repositories.decision_session_repository import (  # noqa: E402
    DecisionSessionRepository,
)
from app.domain.repositories.session_activity_repository import (  # noqa: E402
    SessionActivityRepository,
)
from app.infrastructure.database.repositories.workspace_repositories import (  # noqa: E402
    SqlAlchemyDecisionSessionRepository,
    SqlAlchemySessionActivityRepository,
)


def get_decision_session_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DecisionSessionRepository:
    return SqlAlchemyDecisionSessionRepository(session)


def get_session_activity_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SessionActivityRepository:
    return SqlAlchemySessionActivityRepository(session)


def get_decision_session_engine(
    sessions: Annotated[DecisionSessionRepository, Depends(get_decision_session_repository)],
    activities: Annotated[SessionActivityRepository, Depends(get_session_activity_repository)],
) -> DecisionSessionEngine:
    return DecisionSessionEngine(sessions, activities)


def get_timeline_engine(
    activities: Annotated[SessionActivityRepository, Depends(get_session_activity_repository)],
    statistics: Annotated[StatisticalAnalysisRepository, Depends(get_statistical_analysis_repository)],
    causal: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
    dags: Annotated[DAGVersionRepository, Depends(get_dag_version_repository)],
    simulations: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    reports: Annotated[ExecutiveReportRepository, Depends(get_executive_report_repository)],
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> TimelineEngine:
    return TimelineEngine(
        activities, statistics, causal, dags, simulations, decisions, reports, audit_logs
    )


def get_workspace_search_engine(
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    statistics: Annotated[StatisticalAnalysisRepository, Depends(get_statistical_analysis_repository)],
    causal: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
    simulations: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    reports: Annotated[ExecutiveReportRepository, Depends(get_executive_report_repository)],
    sessions: Annotated[DecisionSessionRepository, Depends(get_decision_session_repository)],
) -> WorkspaceSearchEngine:
    return WorkspaceSearchEngine(
        workspaces, projects, datasets, statistics, causal, simulations, decisions, reports, sessions
    )


def get_comparison_engine() -> ComparisonEngine:
    return ComparisonEngine()


def get_create_decision_session_use_case(
    engine: Annotated[DecisionSessionEngine, Depends(get_decision_session_engine)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> CreateDecisionSessionUseCase:
    return CreateDecisionSessionUseCase(
        engine, datasets, versions, projects, workspaces, authorization
    )


def get_get_decision_session_use_case(
    sessions: Annotated[DecisionSessionRepository, Depends(get_decision_session_repository)],
    engine: Annotated[DecisionSessionEngine, Depends(get_decision_session_engine)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetDecisionSessionUseCase:
    return GetDecisionSessionUseCase(
        sessions, engine, datasets, versions, projects, workspaces, authorization
    )


def get_list_decision_sessions_use_case(
    sessions: Annotated[DecisionSessionRepository, Depends(get_decision_session_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListDecisionSessionsUseCase:
    return ListDecisionSessionsUseCase(
        sessions, datasets, versions, projects, workspaces, authorization
    )


def get_update_decision_session_use_case(
    sessions: Annotated[DecisionSessionRepository, Depends(get_decision_session_repository)],
    engine: Annotated[DecisionSessionEngine, Depends(get_decision_session_engine)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> UpdateDecisionSessionUseCase:
    return UpdateDecisionSessionUseCase(
        sessions, engine, datasets, versions, projects, workspaces, authorization
    )


def get_add_session_comment_use_case(
    sessions: Annotated[DecisionSessionRepository, Depends(get_decision_session_repository)],
    engine: Annotated[DecisionSessionEngine, Depends(get_decision_session_engine)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> AddSessionCommentUseCase:
    return AddSessionCommentUseCase(
        sessions, engine, datasets, versions, projects, workspaces, authorization
    )


def get_session_timeline_use_case(
    sessions: Annotated[DecisionSessionRepository, Depends(get_decision_session_repository)],
    timeline: Annotated[TimelineEngine, Depends(get_timeline_engine)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetSessionTimelineUseCase:
    return GetSessionTimelineUseCase(
        sessions, timeline, datasets, versions, projects, workspaces, authorization
    )


def get_workspace_search_use_case(
    search: Annotated[WorkspaceSearchEngine, Depends(get_workspace_search_engine)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> WorkspaceSearchUseCase:
    return WorkspaceSearchUseCase(search, authorization)


def get_compare_sessions_use_case(
    sessions: Annotated[DecisionSessionRepository, Depends(get_decision_session_repository)],
    comparison: Annotated[ComparisonEngine, Depends(get_comparison_engine)],
    simulations: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    reports: Annotated[ExecutiveReportRepository, Depends(get_executive_report_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    versions: Annotated[DatasetVersionRepository, Depends(get_dataset_version_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> CompareSessionsUseCase:
    return CompareSessionsUseCase(
        sessions,
        comparison,
        simulations,
        decisions,
        reports,
        datasets,
        versions,
        projects,
        workspaces,
        authorization,
    )


def get_list_workspace_activity_use_case(
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListWorkspaceActivityUseCase:
    return ListWorkspaceActivityUseCase(audit_logs, authorization)


CreateDecisionSessionDep = Annotated[
    CreateDecisionSessionUseCase, Depends(get_create_decision_session_use_case)
]
GetDecisionSessionDep = Annotated[
    GetDecisionSessionUseCase, Depends(get_get_decision_session_use_case)
]
ListDecisionSessionsDep = Annotated[
    ListDecisionSessionsUseCase, Depends(get_list_decision_sessions_use_case)
]
UpdateDecisionSessionDep = Annotated[
    UpdateDecisionSessionUseCase, Depends(get_update_decision_session_use_case)
]
AddSessionCommentDep = Annotated[
    AddSessionCommentUseCase, Depends(get_add_session_comment_use_case)
]
GetSessionTimelineDep = Annotated[
    GetSessionTimelineUseCase, Depends(get_session_timeline_use_case)
]
WorkspaceSearchDep = Annotated[WorkspaceSearchUseCase, Depends(get_workspace_search_use_case)]
CompareSessionsDep = Annotated[CompareSessionsUseCase, Depends(get_compare_sessions_use_case)]
ListWorkspaceActivityDep = Annotated[
    ListWorkspaceActivityUseCase, Depends(get_list_workspace_activity_use_case)
]


# ---------------------------------------------------------------------------
# Phase 11 — Enterprise Analytics Infrastructure
# ---------------------------------------------------------------------------
from app.application.services.infrastructure.cache_service import (  # noqa: E402
    AnalyticsCacheService,
)
from app.application.services.infrastructure.execution_monitor import (  # noqa: E402
    ExecutionMonitor,
)
from app.application.services.infrastructure.job_orchestrator import (  # noqa: E402
    JobOrchestrator,
)
from app.application.services.infrastructure.metrics_service import (  # noqa: E402
    InfrastructureMetricsService,
    MetricsCollector,
    metrics_collector,
)
from app.application.services.infrastructure.queue_manager import QueueManager  # noqa: E402
from app.application.use_cases.infrastructure import (  # noqa: E402
    CancelAnalyticsJobUseCase,
    GetAnalyticsJobUseCase,
    GetCacheStatsUseCase,
    GetInfrastructureMetricsUseCase,
    GetQueueStatusUseCase,
    InvalidateDatasetCacheUseCase,
    ListAnalyticsJobsUseCase,
    RetryAnalyticsJobUseCase,
    SubmitAnalyticsJobUseCase,
)
from app.domain.ports.cache_store import CacheStorePort  # noqa: E402
from app.domain.ports.job_queue import JobQueuePort  # noqa: E402
from app.domain.repositories.analytics_job_repository import (  # noqa: E402
    AnalyticsJobRepository,
)
from app.infrastructure.cache.in_memory_cache_store import InMemoryCacheStore  # noqa: E402
from app.infrastructure.cache.redis_cache_store import RedisCacheStore  # noqa: E402
from app.infrastructure.database.repositories.analytics_job_repository import (  # noqa: E402
    SqlAlchemyAnalyticsJobRepository,
)
from app.infrastructure.queue.in_memory_job_queue import InMemoryJobQueue  # noqa: E402
from app.infrastructure.queue.redis_job_queue import RedisJobQueue  # noqa: E402


def _resolve_job_queue(request: Request) -> JobQueuePort:
    if getattr(request.app.state, "job_queue", None) is None:
        if getattr(request.app.state, "redis", None) is None:
            request.app.state.job_queue = InMemoryJobQueue()
        else:
            redis = get_redis(request)
            request.app.state.job_queue = RedisJobQueue(redis.client)
    return request.app.state.job_queue


def _resolve_cache_store(request: Request) -> CacheStorePort:
    if getattr(request.app.state, "cache_store", None) is None:
        if getattr(request.app.state, "redis", None) is None:
            request.app.state.cache_store = InMemoryCacheStore()
        else:
            redis = get_redis(request)
            request.app.state.cache_store = RedisCacheStore(redis.client)
    return request.app.state.cache_store


def get_analytics_job_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalyticsJobRepository:
    return SqlAlchemyAnalyticsJobRepository(session)


def get_job_queue(request: Request) -> JobQueuePort:
    return _resolve_job_queue(request)


def get_cache_store(request: Request) -> CacheStorePort:
    return _resolve_cache_store(request)


def get_analytics_cache_service(
    store: Annotated[CacheStorePort, Depends(get_cache_store)],
) -> AnalyticsCacheService:
    return AnalyticsCacheService(store)


def get_execution_monitor() -> ExecutionMonitor:
    return ExecutionMonitor()


def get_metrics_collector() -> MetricsCollector:
    return metrics_collector


def get_job_orchestrator(
    jobs: Annotated[AnalyticsJobRepository, Depends(get_analytics_job_repository)],
    queue: Annotated[JobQueuePort, Depends(get_job_queue)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JobOrchestrator:
    return JobOrchestrator(jobs, queue, max_retries=settings.job_max_retries)


def get_queue_manager(
    queue: Annotated[JobQueuePort, Depends(get_job_queue)],
) -> QueueManager:
    return QueueManager(queue)


def get_infrastructure_metrics_service(
    jobs: Annotated[AnalyticsJobRepository, Depends(get_analytics_job_repository)],
    queue: Annotated[JobQueuePort, Depends(get_job_queue)],
    cache: Annotated[AnalyticsCacheService, Depends(get_analytics_cache_service)],
    collector: Annotated[MetricsCollector, Depends(get_metrics_collector)],
) -> InfrastructureMetricsService:
    return InfrastructureMetricsService(jobs, queue, cache, collector)


# ---------------------------------------------------------------------------
# Phase 12 — Production Hardening
# ---------------------------------------------------------------------------
from app.application.services.audit.audit_service import AuditService  # noqa: E402
from app.infrastructure.secrets.env_secrets_provider import EnvSecretsProvider  # noqa: E402
from app.infrastructure.resilience.in_memory_circuit_breaker import (  # noqa: E402
    InMemoryCircuitBreaker,
)


def get_audit_service(
    audit_logs: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> AuditService:
    return AuditService(audit_logs)


def get_secrets_provider() -> EnvSecretsProvider:
    return EnvSecretsProvider()


def get_circuit_breaker(
    settings: Annotated[Settings, Depends(get_settings)],
) -> InMemoryCircuitBreaker:
    return InMemoryCircuitBreaker(
        failure_threshold=settings.circuit_breaker_failure_threshold,
        recovery_timeout_seconds=settings.circuit_breaker_recovery_seconds,
    )


# Re-wire infrastructure use cases that now require AuditService
def get_submit_analytics_job_use_case(
    orchestrator: Annotated[JobOrchestrator, Depends(get_job_orchestrator)],
    monitor: Annotated[ExecutionMonitor, Depends(get_execution_monitor)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> SubmitAnalyticsJobUseCase:
    return SubmitAnalyticsJobUseCase(orchestrator, monitor, datasets, authorization, audit)


def get_cancel_analytics_job_use_case(
    orchestrator: Annotated[JobOrchestrator, Depends(get_job_orchestrator)],
    monitor: Annotated[ExecutionMonitor, Depends(get_execution_monitor)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> CancelAnalyticsJobUseCase:
    return CancelAnalyticsJobUseCase(orchestrator, monitor, authorization, audit)


def get_retry_analytics_job_use_case(
    orchestrator: Annotated[JobOrchestrator, Depends(get_job_orchestrator)],
    monitor: Annotated[ExecutionMonitor, Depends(get_execution_monitor)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> RetryAnalyticsJobUseCase:
    return RetryAnalyticsJobUseCase(orchestrator, monitor, authorization, audit)


def get_invalidate_dataset_cache_use_case(
    cache: Annotated[AnalyticsCacheService, Depends(get_analytics_cache_service)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> InvalidateDatasetCacheUseCase:
    return InvalidateDatasetCacheUseCase(cache, datasets, authorization, audit)


def get_list_analytics_jobs_use_case(
    jobs: Annotated[AnalyticsJobRepository, Depends(get_analytics_job_repository)],
    monitor: Annotated[ExecutionMonitor, Depends(get_execution_monitor)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListAnalyticsJobsUseCase:
    return ListAnalyticsJobsUseCase(jobs, monitor, authorization)


def get_get_analytics_job_use_case(
    orchestrator: Annotated[JobOrchestrator, Depends(get_job_orchestrator)],
    monitor: Annotated[ExecutionMonitor, Depends(get_execution_monitor)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetAnalyticsJobUseCase:
    return GetAnalyticsJobUseCase(orchestrator, monitor, authorization)


def get_infrastructure_metrics_use_case(
    metrics: Annotated[InfrastructureMetricsService, Depends(get_infrastructure_metrics_service)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetInfrastructureMetricsUseCase:
    return GetInfrastructureMetricsUseCase(metrics, authorization)


def get_cache_stats_use_case(
    cache: Annotated[AnalyticsCacheService, Depends(get_analytics_cache_service)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetCacheStatsUseCase:
    return GetCacheStatsUseCase(cache, authorization)


def get_queue_status_use_case(
    queue: Annotated[QueueManager, Depends(get_queue_manager)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetQueueStatusUseCase:
    return GetQueueStatusUseCase(queue, authorization)


SubmitAnalyticsJobDep = Annotated[
    SubmitAnalyticsJobUseCase, Depends(get_submit_analytics_job_use_case)
]
ListAnalyticsJobsDep = Annotated[
    ListAnalyticsJobsUseCase, Depends(get_list_analytics_jobs_use_case)
]
GetAnalyticsJobDep = Annotated[GetAnalyticsJobUseCase, Depends(get_get_analytics_job_use_case)]
CancelAnalyticsJobDep = Annotated[
    CancelAnalyticsJobUseCase, Depends(get_cancel_analytics_job_use_case)
]
RetryAnalyticsJobDep = Annotated[
    RetryAnalyticsJobUseCase, Depends(get_retry_analytics_job_use_case)
]
GetInfrastructureMetricsDep = Annotated[
    GetInfrastructureMetricsUseCase, Depends(get_infrastructure_metrics_use_case)
]
GetCacheStatsDep = Annotated[GetCacheStatsUseCase, Depends(get_cache_stats_use_case)]
InvalidateDatasetCacheDep = Annotated[
    InvalidateDatasetCacheUseCase, Depends(get_invalidate_dataset_cache_use_case)
]
GetQueueStatusDep = Annotated[GetQueueStatusUseCase, Depends(get_queue_status_use_case)]

# ---------------------------------------------------------------------------
# Phase 13 — AI Decision Copilot
# ---------------------------------------------------------------------------
from app.application.services.copilot.citation_generator import CitationGenerator  # noqa: E402
from app.application.services.copilot.context_builder import CopilotContextBuilder  # noqa: E402
from app.application.services.copilot.conversation_manager import (  # noqa: E402
    CopilotConversationManager,
)
from app.application.services.copilot.prompt_composer import CopilotPromptComposer  # noqa: E402
from app.application.services.copilot.response_validator import (  # noqa: E402
    CopilotResponseValidator,
)
from app.application.use_cases.copilot import (  # noqa: E402
    CreateCopilotConversationUseCase,
    GetCopilotContextUseCase,
    GetCopilotConversationUseCase,
    ListCopilotConversationsUseCase,
    SendCopilotMessageUseCase,
)
from app.domain.ports.llm_provider import LlmProviderPort  # noqa: E402
from app.domain.repositories.copilot_conversation_repository import (  # noqa: E402
    CopilotConversationRepository,
)
from app.domain.repositories.copilot_message_repository import CopilotMessageRepository  # noqa: E402
from app.infrastructure.database.repositories.copilot_repositories import (  # noqa: E402
    SqlAlchemyCopilotConversationRepository,
    SqlAlchemyCopilotMessageRepository,
)
from app.infrastructure.llm.factory import create_llm_provider  # noqa: E402


def get_copilot_conversation_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CopilotConversationRepository:
    return SqlAlchemyCopilotConversationRepository(session)


def get_copilot_message_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CopilotMessageRepository:
    return SqlAlchemyCopilotMessageRepository(session)


def get_llm_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LlmProviderPort:
    return create_llm_provider(settings)


def get_copilot_context_builder(
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    intelligence: Annotated[IntelligenceReportRepository, Depends(get_intelligence_report_repository)],
    statistics: Annotated[StatisticalAnalysisRepository, Depends(get_statistical_analysis_repository)],
    causal: Annotated[CausalAnalysisRepository, Depends(get_causal_analysis_repository)],
    simulations: Annotated[SimulationRunRepository, Depends(get_simulation_run_repository)],
    decisions: Annotated[DecisionRunRepository, Depends(get_decision_run_repository)],
    reports: Annotated[ExecutiveReportRepository, Depends(get_executive_report_repository)],
    sessions: Annotated[DecisionSessionRepository, Depends(get_decision_session_repository)],
) -> CopilotContextBuilder:
    return CopilotContextBuilder(
        datasets, intelligence, statistics, causal, simulations, decisions, reports, sessions
    )


def get_copilot_prompt_composer() -> CopilotPromptComposer:
    return CopilotPromptComposer()


def get_copilot_response_validator() -> CopilotResponseValidator:
    return CopilotResponseValidator()


def get_citation_generator() -> CitationGenerator:
    return CitationGenerator()


def get_copilot_conversation_manager(
    conversations: Annotated[CopilotConversationRepository, Depends(get_copilot_conversation_repository)],
    messages: Annotated[CopilotMessageRepository, Depends(get_copilot_message_repository)],
    context_builder: Annotated[CopilotContextBuilder, Depends(get_copilot_context_builder)],
    prompt_composer: Annotated[CopilotPromptComposer, Depends(get_copilot_prompt_composer)],
    validator: Annotated[CopilotResponseValidator, Depends(get_copilot_response_validator)],
    citations: Annotated[CitationGenerator, Depends(get_citation_generator)],
    llm: Annotated[LlmProviderPort, Depends(get_llm_provider)],
) -> CopilotConversationManager:
    return CopilotConversationManager(
        conversations, messages, context_builder, prompt_composer, validator, citations, llm
    )


def get_create_copilot_conversation_use_case(
    conversations: Annotated[CopilotConversationRepository, Depends(get_copilot_conversation_repository)],
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> CreateCopilotConversationUseCase:
    return CreateCopilotConversationUseCase(conversations, datasets, authorization, audit)


def get_send_copilot_message_use_case(
    conversations: Annotated[CopilotConversationRepository, Depends(get_copilot_conversation_repository)],
    messages: Annotated[CopilotMessageRepository, Depends(get_copilot_message_repository)],
    manager: Annotated[CopilotConversationManager, Depends(get_copilot_conversation_manager)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> SendCopilotMessageUseCase:
    return SendCopilotMessageUseCase(conversations, messages, manager, authorization, audit)


def get_get_copilot_conversation_use_case(
    conversations: Annotated[CopilotConversationRepository, Depends(get_copilot_conversation_repository)],
    messages: Annotated[CopilotMessageRepository, Depends(get_copilot_message_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetCopilotConversationUseCase:
    return GetCopilotConversationUseCase(conversations, messages, authorization)


def get_list_copilot_conversations_use_case(
    conversations: Annotated[CopilotConversationRepository, Depends(get_copilot_conversation_repository)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> ListCopilotConversationsUseCase:
    return ListCopilotConversationsUseCase(conversations, authorization)


def get_get_copilot_context_use_case(
    context_builder: Annotated[CopilotContextBuilder, Depends(get_copilot_context_builder)],
    authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> GetCopilotContextUseCase:
    return GetCopilotContextUseCase(context_builder, authorization)


CreateCopilotConversationDep = Annotated[
    CreateCopilotConversationUseCase, Depends(get_create_copilot_conversation_use_case)
]
SendCopilotMessageDep = Annotated[SendCopilotMessageUseCase, Depends(get_send_copilot_message_use_case)]
GetCopilotConversationDep = Annotated[
    GetCopilotConversationUseCase, Depends(get_get_copilot_conversation_use_case)
]
ListCopilotConversationsDep = Annotated[
    ListCopilotConversationsUseCase, Depends(get_list_copilot_conversations_use_case)
]
GetCopilotContextDep = Annotated[GetCopilotContextUseCase, Depends(get_get_copilot_context_use_case)]

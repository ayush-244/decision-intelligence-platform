"""Organization, workspace, and project use cases."""

from __future__ import annotations

from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.dto.identity import OrganizationDTO, ProjectDTO, WorkspaceDTO
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.membership_repository import MembershipRepository
from app.domain.repositories.organization_repository import OrganizationRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.role import MembershipRole, Permission
from app.domain.value_objects.tenant import TenantContext
from app.shared.exceptions import BusinessValidationError, ConflictError, NotFoundError
from app.shared.utils.slug import slugify


class CreateOrganizationUseCase:
    def __init__(
        self,
        organizations: OrganizationRepository,
        memberships: MembershipRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._organizations = organizations
        self._memberships = memberships
        self._audit_logs = audit_logs

    async def execute(self, *, user_id: UUID, name: str) -> OrganizationDTO:
        base_slug = slugify(name)
        slug = base_slug
        suffix = 1
        while await self._organizations.get_by_slug(slug) is not None:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        org = await self._organizations.create(name=name, slug=slug)
        membership = await self._memberships.create(
            user_id=user_id,
            organization_id=org.id,
            role=MembershipRole.OWNER,
        )
        await self._audit_logs.append(
            action="organization.created",
            resource_type="organization",
            user_id=user_id,
            organization_id=org.id,
            resource_id=org.id,
            metadata={"name": name},
        )
        return OrganizationDTO(
            id=org.id,
            name=org.name,
            slug=org.slug,
            role=membership.role,
            created_at=org.created_at,
        )


class ListOrganizationsUseCase:
    def __init__(
        self,
        organizations: OrganizationRepository,
        memberships: MembershipRepository,
    ) -> None:
        self._organizations = organizations
        self._memberships = memberships

    async def execute(self, *, user_id: UUID) -> list[OrganizationDTO]:
        orgs = await self._organizations.list_for_user(user_id)
        results: list[OrganizationDTO] = []
        for org in orgs:
            membership = await self._memberships.get_membership(
                user_id=user_id, organization_id=org.id
            )
            if membership is None:
                continue
            results.append(
                OrganizationDTO(
                    id=org.id,
                    name=org.name,
                    slug=org.slug,
                    role=membership.role,
                    created_at=org.created_at,
                )
            )
        return results


class CreateWorkspaceUseCase:
    def __init__(
        self,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._workspaces = workspaces
        self._authorization = authorization
        self._audit_logs = audit_logs

    async def execute(
        self,
        *,
        tenant: TenantContext,
        name: str,
        description: str | None = None,
    ) -> WorkspaceDTO:
        self._authorization.require_permission(tenant.role, Permission.WORKSPACE_CREATE)
        if await self._workspaces.exists_by_name(organization_id=tenant.organization_id, name=name):
            raise ConflictError("A workspace with this name already exists in the organization.")
        slug = slugify(name)
        workspace = await self._workspaces.create(
            organization_id=tenant.organization_id,
            name=name,
            slug=slug,
            description=description,
        )
        await self._audit_logs.append(
            action="workspace.created",
            resource_type="workspace",
            user_id=tenant.user_id,
            organization_id=tenant.organization_id,
            resource_id=workspace.id,
            metadata={"name": name},
        )
        return WorkspaceDTO(
            id=workspace.id,
            organization_id=workspace.organization_id,
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            created_at=workspace.created_at,
        )


class ListWorkspacesUseCase:
    def __init__(
        self,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._workspaces = workspaces
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext) -> list[WorkspaceDTO]:
        self._authorization.require_permission(tenant.role, Permission.WORKSPACE_READ)
        rows = await self._workspaces.list_for_organization(tenant.organization_id)
        return [
            WorkspaceDTO(
                id=row.id,
                organization_id=row.organization_id,
                name=row.name,
                slug=row.slug,
                description=row.description,
                created_at=row.created_at,
            )
            for row in rows
        ]


class CreateProjectUseCase:
    def __init__(
        self,
        workspaces: WorkspaceRepository,
        projects: ProjectRepository,
        authorization: AuthorizationService,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._workspaces = workspaces
        self._projects = projects
        self._authorization = authorization
        self._audit_logs = audit_logs

    async def execute(
        self,
        *,
        tenant: TenantContext,
        workspace_id: UUID,
        name: str,
        description: str | None = None,
    ) -> ProjectDTO:
        workspace = await self._workspaces.get_by_id(
            workspace_id=workspace_id,
            organization_id=tenant.organization_id,
        )
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        self._authorization.require_permission(tenant.role, Permission.PROJECT_CREATE)
        if await self._projects.exists_by_name(workspace_id=workspace_id, name=name):
            raise ConflictError("A project with this name already exists in the workspace.")
        if not name.strip():
            raise BusinessValidationError("Project name is required.")
        project = await self._projects.create(
            workspace_id=workspace_id,
            name=name.strip(),
            slug=slugify(name),
            description=description,
        )
        await self._audit_logs.append(
            action="project.created",
            resource_type="project",
            user_id=tenant.user_id,
            organization_id=tenant.organization_id,
            resource_id=project.id,
            metadata={"workspace_id": str(workspace_id), "name": name},
        )
        return ProjectDTO(
            id=project.id,
            workspace_id=project.workspace_id,
            name=project.name,
            slug=project.slug,
            description=project.description,
            created_at=project.created_at,
        )


class ListProjectsUseCase:
    def __init__(
        self,
        workspaces: WorkspaceRepository,
        projects: ProjectRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._workspaces = workspaces
        self._projects = projects
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, workspace_id: UUID) -> list[ProjectDTO]:
        workspace = await self._workspaces.get_by_id(
            workspace_id=workspace_id,
            organization_id=tenant.organization_id,
        )
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        self._authorization.require_permission(tenant.role, Permission.PROJECT_READ)
        rows = await self._projects.list_for_workspace(workspace_id)
        return [
            ProjectDTO(
                id=row.id,
                workspace_id=row.workspace_id,
                name=row.name,
                slug=row.slug,
                description=row.description,
                created_at=row.created_at,
            )
            for row in rows
        ]

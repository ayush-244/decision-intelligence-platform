"""In-memory identity repositories for API integration tests."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4

from app.domain.entities.audit_log import AuditLog
from app.domain.entities.membership import Membership
from app.domain.entities.organization import Organization
from app.domain.entities.project import Project
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.domain.entities.workspace import Workspace
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.membership_repository import MembershipRepository
from app.domain.repositories.organization_repository import OrganizationRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.role import MembershipRole
from app.shared.utils.datetime import utc_now


class InMemoryIdentityStore:
    """Process-local store backing fake repository implementations."""

    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}
        self.password_hashes: dict[UUID, str] = {}
        self.organizations: dict[UUID, Organization] = {}
        self.memberships: dict[UUID, Membership] = {}
        self.workspaces: dict[UUID, Workspace] = {}
        self.projects: dict[UUID, Project] = {}
        self.refresh_tokens: dict[UUID, RefreshToken] = {}
        self.refresh_token_hashes: dict[str, UUID] = {}
        self.audit_logs: list[AuditLog] = []

    def user_repo(self) -> FakeUserRepository:
        return FakeUserRepository(self)

    def organization_repo(self) -> FakeOrganizationRepository:
        return FakeOrganizationRepository(self)

    def membership_repo(self) -> FakeMembershipRepository:
        return FakeMembershipRepository(self)

    def workspace_repo(self) -> FakeWorkspaceRepository:
        return FakeWorkspaceRepository(self)

    def project_repo(self) -> FakeProjectRepository:
        return FakeProjectRepository(self)

    def refresh_token_repo(self) -> FakeRefreshTokenRepository:
        return FakeRefreshTokenRepository(self)

    def audit_log_repo(self) -> FakeAuditLogRepository:
        return FakeAuditLogRepository(self)


class FakeUserRepository(UserRepository):
    def __init__(self, store: InMemoryIdentityStore) -> None:
        self._store = store

    async def get_by_id(self, user_id: UUID) -> User | None:
        user = self._store.users.get(user_id)
        if user is None or user.is_deleted:
            return None
        return user

    async def get_by_email(self, email: str) -> User | None:
        normalized = email.lower()
        for user in self._store.users.values():
            if user.email == normalized and not user.is_deleted:
                return user
        return None

    async def create(self, *, email: str, password_hash: str, full_name: str) -> User:
        now = utc_now()
        user = User(
            id=uuid4(),
            email=email.lower(),
            full_name=full_name,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._store.users[user.id] = user
        self._store.password_hashes[user.id] = password_hash
        return user

    async def get_password_hash(self, user_id: UUID) -> str | None:
        return self._store.password_hashes.get(user_id)


class FakeOrganizationRepository(OrganizationRepository):
    def __init__(self, store: InMemoryIdentityStore) -> None:
        self._store = store

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        org = self._store.organizations.get(organization_id)
        if org is None or org.is_deleted:
            return None
        return org

    async def get_by_slug(self, slug: str) -> Organization | None:
        for org in self._store.organizations.values():
            if org.slug == slug and not org.is_deleted:
                return org
        return None

    async def list_for_user(self, user_id: UUID) -> list[Organization]:
        org_ids = {
            membership.organization_id
            for membership in self._store.memberships.values()
            if membership.user_id == user_id and membership.is_active
        }
        orgs = [
            org
            for org in self._store.organizations.values()
            if org.id in org_ids and not org.is_deleted
        ]
        return sorted(orgs, key=lambda row: row.name)

    async def create(self, *, name: str, slug: str) -> Organization:
        now = utc_now()
        org = Organization(
            id=uuid4(),
            name=name,
            slug=slug,
            created_at=now,
            updated_at=now,
        )
        self._store.organizations[org.id] = org
        return org


class FakeMembershipRepository(MembershipRepository):
    def __init__(self, store: InMemoryIdentityStore) -> None:
        self._store = store

    async def get_membership(self, *, user_id: UUID, organization_id: UUID) -> Membership | None:
        for membership in self._store.memberships.values():
            if membership.user_id == user_id and membership.organization_id == organization_id:
                return membership
        return None

    async def create(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        role: MembershipRole,
    ) -> Membership:
        now = utc_now()
        membership = Membership(
            id=uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._store.memberships[membership.id] = membership
        return membership

    async def count_owners(self, organization_id: UUID) -> int:
        return sum(
            1
            for membership in self._store.memberships.values()
            if membership.organization_id == organization_id
            and membership.role is MembershipRole.OWNER
            and membership.is_active
        )


class FakeWorkspaceRepository(WorkspaceRepository):
    def __init__(self, store: InMemoryIdentityStore) -> None:
        self._store = store

    async def get_by_id(self, *, workspace_id: UUID, organization_id: UUID) -> Workspace | None:
        workspace = self._store.workspaces.get(workspace_id)
        if workspace is None or workspace.is_deleted:
            return None
        if workspace.organization_id != organization_id:
            return None
        return workspace

    async def list_for_organization(self, organization_id: UUID) -> list[Workspace]:
        return [
            workspace
            for workspace in self._store.workspaces.values()
            if workspace.organization_id == organization_id and not workspace.is_deleted
        ]

    async def exists_by_name(self, *, organization_id: UUID, name: str) -> bool:
        return any(
            workspace.organization_id == organization_id
            and workspace.name == name
            and not workspace.is_deleted
            for workspace in self._store.workspaces.values()
        )

    async def create(
        self,
        *,
        organization_id: UUID,
        name: str,
        slug: str,
        description: str | None,
    ) -> Workspace:
        now = utc_now()
        workspace = Workspace(
            id=uuid4(),
            organization_id=organization_id,
            name=name,
            slug=slug,
            description=description,
            created_at=now,
            updated_at=now,
        )
        self._store.workspaces[workspace.id] = workspace
        return workspace


class FakeProjectRepository(ProjectRepository):
    def __init__(self, store: InMemoryIdentityStore) -> None:
        self._store = store

    async def get_by_id(self, *, project_id: UUID, workspace_id: UUID) -> Project | None:
        project = self._store.projects.get(project_id)
        if project is None or project.is_deleted or project.workspace_id != workspace_id:
            return None
        return project

    async def list_for_workspace(self, workspace_id: UUID) -> list[Project]:
        return [
            project
            for project in self._store.projects.values()
            if project.workspace_id == workspace_id and not project.is_deleted
        ]

    async def exists_by_name(self, *, workspace_id: UUID, name: str) -> bool:
        return any(
            project.workspace_id == workspace_id
            and project.name == name
            and not project.is_deleted
            for project in self._store.projects.values()
        )

    async def create(
        self,
        *,
        workspace_id: UUID,
        name: str,
        slug: str,
        description: str | None,
    ) -> Project:
        now = utc_now()
        project = Project(
            id=uuid4(),
            workspace_id=workspace_id,
            name=name,
            slug=slug,
            description=description,
            created_at=now,
            updated_at=now,
        )
        self._store.projects[project.id] = project
        return project

    async def get_workspace_id(self, project_id: UUID) -> UUID | None:
        project = self._store.projects.get(project_id)
        if project is None or project.is_deleted:
            return None
        return project.workspace_id


class FakeRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, store: InMemoryIdentityStore) -> None:
        self._store = store

    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        family_id: UUID,
        expires_at: object,
    ) -> RefreshToken:
        now = utc_now()
        token = RefreshToken(
            id=uuid4(),
            user_id=user_id,
            family_id=family_id,
            expires_at=expires_at,  # type: ignore[arg-type]
            revoked_at=None,
            created_at=now,
        )
        self._store.refresh_tokens[token.id] = token
        self._store.refresh_token_hashes[token_hash] = token.id
        return token

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        token_id = self._store.refresh_token_hashes.get(token_hash)
        if token_id is None:
            return None
        return self._store.refresh_tokens.get(token_id)

    async def revoke(self, token_id: UUID) -> None:
        token = self._store.refresh_tokens.get(token_id)
        if token is not None:
            self._store.refresh_tokens[token_id] = replace(token, revoked_at=utc_now())

    async def revoke_family(self, family_id: UUID) -> None:
        now = utc_now()
        for token_id, token in list(self._store.refresh_tokens.items()):
            if token.family_id == family_id and token.revoked_at is None:
                self._store.refresh_tokens[token_id] = replace(token, revoked_at=now)


class FakeAuditLogRepository(AuditLogRepository):
    def __init__(self, store: InMemoryIdentityStore) -> None:
        self._store = store

    async def append(
        self,
        *,
        action: str,
        resource_type: str,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        resource_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            id=uuid4(),
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            organization_id=organization_id,
            resource_id=resource_id,
            metadata=metadata or {},
            created_at=utc_now(),
        )
        self._store.audit_logs.append(entry)
        return entry

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int = 50,
        resource_type: str | None = None,
    ) -> list[AuditLog]:
        rows = [
            log
            for log in self._store.audit_logs
            if log.organization_id == organization_id
            and (resource_type is None or log.resource_type == resource_type)
        ]
        rows.sort(key=lambda log: log.created_at, reverse=True)
        return rows[:limit]

"""SQLAlchemy repository implementations for identity and tenancy."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.infrastructure.database.mappers.identity import (
    to_audit_log,
    to_membership,
    to_organization,
    to_project,
    to_refresh_token,
    to_user,
    to_workspace,
)
from app.infrastructure.database.models.audit_log import AuditLogModel
from app.infrastructure.database.models.membership import MembershipModel
from app.infrastructure.database.models.organization import OrganizationModel
from app.infrastructure.database.models.project import ProjectModel
from app.infrastructure.database.models.refresh_token import RefreshTokenModel
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.workspace import WorkspaceModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
        )
        model = result.scalar_one_or_none()
        return to_user(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(
                func.lower(UserModel.email) == email.lower(),
                UserModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return to_user(model) if model else None

    async def create(self, *, email: str, password_hash: str, full_name: str) -> User:
        model = UserModel(email=email.lower(), password_hash=password_hash, full_name=full_name)
        self._session.add(model)
        await self._session.flush()
        return to_user(model)

    async def get_password_hash(self, user_id: UUID) -> str | None:
        result = await self._session.execute(
            select(UserModel.password_hash).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()


class SqlAlchemyOrganizationRepository(OrganizationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        result = await self._session.execute(
            select(OrganizationModel).where(
                OrganizationModel.id == organization_id,
                OrganizationModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return to_organization(model) if model else None

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self._session.execute(
            select(OrganizationModel).where(
                OrganizationModel.slug == slug,
                OrganizationModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return to_organization(model) if model else None

    async def list_for_user(self, user_id: UUID) -> list[Organization]:
        stmt = (
            select(OrganizationModel)
            .join(MembershipModel, MembershipModel.organization_id == OrganizationModel.id)
            .where(
                MembershipModel.user_id == user_id,
                MembershipModel.is_active.is_(True),
                OrganizationModel.deleted_at.is_(None),
            )
            .order_by(OrganizationModel.name)
        )
        result = await self._session.execute(stmt)
        return [to_organization(row) for row in result.scalars().all()]

    async def create(self, *, name: str, slug: str) -> Organization:
        model = OrganizationModel(name=name, slug=slug)
        self._session.add(model)
        await self._session.flush()
        return to_organization(model)


class SqlAlchemyMembershipRepository(MembershipRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_membership(self, *, user_id: UUID, organization_id: UUID) -> Membership | None:
        result = await self._session.execute(
            select(MembershipModel).where(
                MembershipModel.user_id == user_id,
                MembershipModel.organization_id == organization_id,
                MembershipModel.is_active.is_(True),
            )
        )
        model = result.scalar_one_or_none()
        return to_membership(model) if model else None

    async def create(
        self, *, user_id: UUID, organization_id: UUID, role: MembershipRole
    ) -> Membership:
        model = MembershipModel(
            user_id=user_id,
            organization_id=organization_id,
            role=role.value,
        )
        self._session.add(model)
        await self._session.flush()
        return to_membership(model)

    async def count_owners(self, organization_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(MembershipModel)
            .where(
                MembershipModel.organization_id == organization_id,
                MembershipModel.role == MembershipRole.OWNER.value,
                MembershipModel.is_active.is_(True),
            )
        )
        return int(result.scalar_one())


class SqlAlchemyWorkspaceRepository(WorkspaceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, workspace_id: UUID, organization_id: UUID) -> Workspace | None:
        result = await self._session.execute(
            select(WorkspaceModel).where(
                WorkspaceModel.id == workspace_id,
                WorkspaceModel.organization_id == organization_id,
                WorkspaceModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return to_workspace(model) if model else None

    async def list_for_organization(self, organization_id: UUID) -> list[Workspace]:
        result = await self._session.execute(
            select(WorkspaceModel)
            .where(
                WorkspaceModel.organization_id == organization_id,
                WorkspaceModel.deleted_at.is_(None),
            )
            .order_by(WorkspaceModel.name)
        )
        return [to_workspace(row) for row in result.scalars().all()]

    async def create(
        self, *, organization_id: UUID, name: str, slug: str, description: str | None
    ) -> Workspace:
        model = WorkspaceModel(
            organization_id=organization_id,
            name=name,
            slug=slug,
            description=description,
        )
        self._session.add(model)
        await self._session.flush()
        return to_workspace(model)

    async def exists_by_name(self, *, organization_id: UUID, name: str) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(WorkspaceModel)
            .where(
                WorkspaceModel.organization_id == organization_id,
                func.lower(WorkspaceModel.name) == name.lower(),
                WorkspaceModel.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one()) > 0


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, project_id: UUID, workspace_id: UUID) -> Project | None:
        result = await self._session.execute(
            select(ProjectModel).where(
                ProjectModel.id == project_id,
                ProjectModel.workspace_id == workspace_id,
                ProjectModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return to_project(model) if model else None

    async def list_for_workspace(self, workspace_id: UUID) -> list[Project]:
        result = await self._session.execute(
            select(ProjectModel)
            .where(ProjectModel.workspace_id == workspace_id, ProjectModel.deleted_at.is_(None))
            .order_by(ProjectModel.name)
        )
        return [to_project(row) for row in result.scalars().all()]

    async def create(
        self, *, workspace_id: UUID, name: str, slug: str, description: str | None
    ) -> Project:
        model = ProjectModel(
            workspace_id=workspace_id,
            name=name,
            slug=slug,
            description=description,
        )
        self._session.add(model)
        await self._session.flush()
        return to_project(model)

    async def exists_by_name(self, *, workspace_id: UUID, name: str) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(ProjectModel)
            .where(
                ProjectModel.workspace_id == workspace_id,
                func.lower(ProjectModel.name) == name.lower(),
                ProjectModel.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one()) > 0

    async def get_workspace_id(self, project_id: UUID) -> UUID | None:
        result = await self._session.execute(
            select(ProjectModel.workspace_id).where(ProjectModel.id == project_id)
        )
        return result.scalar_one_or_none()


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        family_id: UUID,
        expires_at: object,
    ) -> RefreshToken:
        model = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,  # type: ignore[arg-type]
        )
        self._session.add(model)
        await self._session.flush()
        return to_refresh_token(model)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        model = result.scalar_one_or_none()
        return to_refresh_token(model) if model else None

    async def revoke(self, token_id: UUID) -> None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.id == token_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            model.revoked_at = datetime.now(UTC)
            await self._session.flush()

    async def revoke_family(self, family_id: UUID) -> None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.family_id == family_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
        )
        now = datetime.now(UTC)
        for model in result.scalars().all():
            model.revoked_at = now
        await self._session.flush()


class SqlAlchemyAuditLogRepository(AuditLogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        *,
        action: str,
        resource_type: str,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        resource_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        model = AuditLogModel(
            id=uuid4(),
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            organization_id=organization_id,
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self._session.add(model)
        await self._session.flush()
        return to_audit_log(model)

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int = 50,
        resource_type: str | None = None,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.organization_id == organization_id)
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
        )
        if resource_type:
            stmt = stmt.where(AuditLogModel.resource_type == resource_type)
        result = await self._session.execute(stmt)
        return [to_audit_log(m) for m in result.scalars()]

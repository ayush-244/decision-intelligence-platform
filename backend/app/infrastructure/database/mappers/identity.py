"""Map ORM models to domain entities."""

from __future__ import annotations

from app.domain.entities.audit_log import AuditLog
from app.domain.entities.membership import Membership
from app.domain.entities.organization import Organization
from app.domain.entities.project import Project
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.domain.entities.workspace import Workspace
from app.domain.value_objects.role import MembershipRole
from app.infrastructure.database.models.audit_log import AuditLogModel
from app.infrastructure.database.models.membership import MembershipModel
from app.infrastructure.database.models.organization import OrganizationModel
from app.infrastructure.database.models.project import ProjectModel
from app.infrastructure.database.models.refresh_token import RefreshTokenModel
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.workspace import WorkspaceModel


def to_user(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        full_name=model.full_name,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def to_organization(model: OrganizationModel) -> Organization:
    return Organization(
        id=model.id,
        name=model.name,
        slug=model.slug,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def to_membership(model: MembershipModel) -> Membership:
    return Membership(
        id=model.id,
        user_id=model.user_id,
        organization_id=model.organization_id,
        role=MembershipRole(model.role),
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_workspace(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        organization_id=model.organization_id,
        name=model.name,
        slug=model.slug,
        description=model.description,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def to_project(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        slug=model.slug,
        description=model.description,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def to_refresh_token(model: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=model.id,
        user_id=model.user_id,
        family_id=model.family_id,
        expires_at=model.expires_at,
        revoked_at=model.revoked_at,
        created_at=model.created_at,
    )


def to_audit_log(model: AuditLogModel) -> AuditLog:
    return AuditLog(
        id=model.id,
        action=model.action,
        resource_type=model.resource_type,
        user_id=model.user_id,
        organization_id=model.organization_id,
        resource_id=model.resource_id,
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
    )

"""Authentication and tenancy DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_objects.role import MembershipRole


@dataclass(frozen=True, slots=True)
class UserDTO:
    id: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuthTokensDTO:
    access_token: str
    access_token_expires_in: int
    refresh_token: str


@dataclass(frozen=True, slots=True)
class AuthResultDTO:
    user: UserDTO
    tokens: AuthTokensDTO


@dataclass(frozen=True, slots=True)
class OrganizationDTO:
    id: UUID
    name: str
    slug: str
    role: MembershipRole
    created_at: datetime


@dataclass(frozen=True, slots=True)
class WorkspaceDTO:
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ProjectDTO:
    id: UUID
    workspace_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime

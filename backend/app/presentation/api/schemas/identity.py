"""Identity and tenancy wire schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.application.dto.identity import (
    AuthResultDTO,
    AuthTokensDTO,
    OrganizationDTO,
    ProjectDTO,
    UserDTO,
    WorkspaceDTO,
)
from app.domain.value_objects.role import MembershipRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: UserDTO) -> UserResponse:
        return cls(
            id=dto.id,
            email=dto.email,
            full_name=dto.full_name,
            is_active=dto.is_active,
            created_at=dto.created_at,
        )


class AuthTokensResponse(BaseModel):
    access_token: str
    access_token_expires_in: int
    token_type: str = "bearer"

    @classmethod
    def from_dto(cls, dto: AuthTokensDTO) -> AuthTokensResponse:
        return cls(
            access_token=dto.access_token,
            access_token_expires_in=dto.access_token_expires_in,
        )


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: AuthTokensResponse

    @classmethod
    def from_dto(cls, dto: AuthResultDTO) -> AuthResponse:
        return cls(
            user=UserResponse.from_dto(dto.user),
            tokens=AuthTokensResponse.from_dto(dto.tokens),
        )


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    role: MembershipRole
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: OrganizationDTO) -> OrganizationResponse:
        return cls(
            id=dto.id,
            name=dto.name,
            slug=dto.slug,
            role=dto.role,
            created_at=dto.created_at,
        )


class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: WorkspaceDTO) -> WorkspaceResponse:
        return cls(
            id=dto.id,
            organization_id=dto.organization_id,
            name=dto.name,
            slug=dto.slug,
            description=dto.description,
            created_at=dto.created_at,
        )


class CreateWorkspaceRequest(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: ProjectDTO) -> ProjectResponse:
        return cls(
            id=dto.id,
            workspace_id=dto.workspace_id,
            name=dto.name,
            slug=dto.slug,
            description=dto.description,
            created_at=dto.created_at,
        )


class CreateProjectRequest(BaseModel):
    workspace_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)

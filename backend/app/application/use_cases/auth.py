"""Authentication use cases."""

from __future__ import annotations

from uuid import UUID

from app.application.dto.identity import AuthResultDTO, AuthTokensDTO, UserDTO
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.security.password_service import PasswordService
from app.infrastructure.security.refresh_token_service import RefreshTokenService
from app.shared.exceptions import AuthenticationError, BusinessValidationError, ConflictError


class RegisterUserUseCase:
    def __init__(
        self,
        users: UserRepository,
        audit_logs: AuditLogRepository,
        passwords: PasswordService,
    ) -> None:
        self._users = users
        self._audit_logs = audit_logs
        self._passwords = passwords

    async def execute(self, *, email: str, password: str, full_name: str) -> UserDTO:
        if await self._users.get_by_email(email) is not None:
            raise ConflictError("An account with this email already exists.")
        try:
            password_hash = self._passwords.hash(password)
        except ValueError as exc:
            raise BusinessValidationError(str(exc)) from exc
        user = await self._users.create(email=email, password_hash=password_hash, full_name=full_name)
        await self._audit_logs.append(
            action="user.registered",
            resource_type="user",
            user_id=user.id,
            resource_id=user.id,
        )
        return _to_user_dto(user)


class LoginUserUseCase:
    def __init__(
        self,
        users: UserRepository,
        audit_logs: AuditLogRepository,
        passwords: PasswordService,
        jwt_service: JwtService,
        refresh_tokens: RefreshTokenService,
    ) -> None:
        self._users = users
        self._audit_logs = audit_logs
        self._passwords = passwords
        self._jwt = jwt_service
        self._refresh = refresh_tokens

    async def execute(self, *, email: str, password: str) -> AuthResultDTO:
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid email or password.")
        password_hash = await self._users.get_password_hash(user.id)
        if password_hash is None or not self._passwords.verify(password, password_hash):
            raise AuthenticationError("Invalid email or password.")
        access_token, expires_in = self._jwt.create_access_token(user_id=user.id, email=user.email)
        refresh_raw, _ = await self._refresh.issue(user_id=user.id)
        await self._audit_logs.append(
            action="user.login",
            resource_type="user",
            user_id=user.id,
            resource_id=user.id,
        )
        return AuthResultDTO(
            user=_to_user_dto(user),
            tokens=AuthTokensDTO(
                access_token=access_token,
                access_token_expires_in=expires_in,
                refresh_token=refresh_raw,
            ),
        )


class RefreshAccessTokenUseCase:
    def __init__(
        self,
        users: UserRepository,
        jwt_service: JwtService,
        refresh_tokens: RefreshTokenService,
    ) -> None:
        self._users = users
        self._jwt = jwt_service
        self._refresh = refresh_tokens

    async def execute(self, *, refresh_token: str) -> AuthResultDTO:
        new_raw, _, user_id = await self._refresh.rotate(refresh_token)
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User account is inactive.")
        access_token, expires_in = self._jwt.create_access_token(user_id=user.id, email=user.email)
        return AuthResultDTO(
            user=_to_user_dto(user),
            tokens=AuthTokensDTO(
                access_token=access_token,
                access_token_expires_in=expires_in,
                refresh_token=new_raw,
            ),
        )


class LogoutUserUseCase:
    def __init__(
        self,
        refresh_tokens: RefreshTokenService,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._refresh = refresh_tokens
        self._audit_logs = audit_logs

    async def execute(self, *, refresh_token: str | None, user_id: UUID | None) -> None:
        if refresh_token:
            await self._refresh.revoke_raw(refresh_token)
        if user_id is not None:
            await self._audit_logs.append(
                action="user.logout",
                resource_type="user",
                user_id=user_id,
                resource_id=user_id,
            )


class GetCurrentUserUseCase:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, user_id: UUID) -> UserDTO:
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found.")
        return _to_user_dto(user)


def _to_user_dto(user: object) -> UserDTO:
    from app.domain.entities.user import User

    assert isinstance(user, User)
    return UserDTO(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )

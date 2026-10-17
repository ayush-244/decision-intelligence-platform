"""Authentication endpoints."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Request, Response

from app.core.config import get_settings
from app.presentation.api.auth_cookies import clear_refresh_token_cookie, set_refresh_token_cookie
from app.presentation.api.deps import (
    CurrentUserIdDep,
    GetCurrentUserDep,
    LoginUserDep,
    LogoutUserDep,
    OptionalCurrentUserIdDep,
    RefreshAccessTokenDep,
    RegisterUserDep,
    SettingsDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.identity import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.presentation.rate_limit import limiter
from app.shared.exceptions import AuthenticationError

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_rate_limit() -> str:
    return get_settings().auth_rate_limit


def _read_refresh_token(request: Request, settings: SettingsDep) -> str:
    raw = request.cookies.get(settings.refresh_token_cookie_name)
    if raw is None:
        raise AuthenticationError("Refresh token cookie is missing.")
    return raw


@router.post(
    "/register",
    response_model=DataResponse[UserResponse],
    status_code=HTTPStatus.CREATED,
    summary="Register a new user account",
)
@limiter.limit(_auth_rate_limit)
async def register(
    request: Request,
    body: RegisterRequest,
    use_case: RegisterUserDep,
) -> DataResponse[UserResponse]:
    user = await use_case.execute(
        email=str(body.email),
        password=body.password,
        full_name=body.full_name,
    )
    return DataResponse(data=UserResponse.from_dto(user))


@router.post(
    "/login",
    response_model=DataResponse[AuthResponse],
    summary="Authenticate and receive tokens",
)
@limiter.limit(_auth_rate_limit)
async def login(
    request: Request,
    body: LoginRequest,
    use_case: LoginUserDep,
    settings: SettingsDep,
    response: Response,
) -> DataResponse[AuthResponse]:
    result = await use_case.execute(email=str(body.email), password=body.password)
    set_refresh_token_cookie(
        response,
        settings=settings,
        refresh_token=result.tokens.refresh_token,
    )
    return DataResponse(data=AuthResponse.from_dto(result))


@router.post(
    "/refresh",
    response_model=DataResponse[AuthResponse],
    summary="Rotate refresh token and issue a new access token",
)
@limiter.limit(_auth_rate_limit)
async def refresh_tokens(
    request: Request,
    use_case: RefreshAccessTokenDep,
    settings: SettingsDep,
    response: Response,
) -> DataResponse[AuthResponse]:
    raw = _read_refresh_token(request, settings)
    result = await use_case.execute(refresh_token=raw)
    set_refresh_token_cookie(
        response,
        settings=settings,
        refresh_token=result.tokens.refresh_token,
    )
    return DataResponse(data=AuthResponse.from_dto(result))


@router.post(
    "/logout",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Revoke refresh token and clear session cookie",
)
@limiter.limit(_auth_rate_limit)
async def logout(
    request: Request,
    use_case: LogoutUserDep,
    settings: SettingsDep,
    response: Response,
    user_id: OptionalCurrentUserIdDep,
) -> Response:
    raw = request.cookies.get(settings.refresh_token_cookie_name)
    await use_case.execute(refresh_token=raw, user_id=user_id)
    clear_refresh_token_cookie(response, settings=settings)
    response.status_code = HTTPStatus.NO_CONTENT
    return response


@router.get(
    "/me",
    response_model=DataResponse[UserResponse],
    summary="Return the currently authenticated user",
)
async def me(
    user_id: CurrentUserIdDep,
    use_case: GetCurrentUserDep,
) -> DataResponse[UserResponse]:
    user = await use_case.execute(user_id)
    return DataResponse(data=UserResponse.from_dto(user))

"""Integration tests for authentication and tenancy endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "password": "Password1",
            "full_name": "Alice Example",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "Password1"},
    )
    assert login.status_code == 200
    body = login.json()["data"]
    access_token = body["tokens"]["access_token"]
    refresh_cookie = login.cookies.get("delphi_refresh_token")
    assert refresh_cookie is not None
    return access_token, refresh_cookie


@pytest.mark.asyncio
async def test_register_rejects_weak_password(identity_client: AsyncClient) -> None:
    response = await identity_client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "password": "short", "full_name": "Bob"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_auth_and_tenancy_flow(identity_client: AsyncClient) -> None:
    register = await identity_client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "Password1",
            "full_name": "Owner User",
        },
    )
    assert register.status_code == 201
    assert register.json()["data"]["email"] == "owner@example.com"

    login = await identity_client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "Password1"},
    )
    assert login.status_code == 200
    access_token = login.json()["data"]["tokens"]["access_token"]

    me = await identity_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me.status_code == 200
    assert me.json()["data"]["full_name"] == "Owner User"

    org = await identity_client.post(
        "/api/v1/organizations",
        json={"name": "Acme Corp"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert org.status_code == 201
    org_id = org.json()["data"]["id"]
    assert org.json()["data"]["role"] == "owner"

    workspace = await identity_client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_id, "name": "Research"},
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Organization-ID": org_id,
        },
    )
    assert workspace.status_code == 201
    workspace_id = workspace.json()["data"]["id"]

    project = await identity_client.post(
        "/api/v1/projects",
        json={"workspace_id": workspace_id, "name": "Q3 Analysis"},
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Organization-ID": org_id,
        },
    )
    assert project.status_code == 201
    assert project.json()["data"]["name"] == "Q3 Analysis"

    projects = await identity_client.get(
        f"/api/v1/projects?workspace_id={workspace_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Organization-ID": org_id,
        },
    )
    assert projects.status_code == 200
    assert len(projects.json()["data"]) == 1


@pytest.mark.asyncio
async def test_refresh_rotates_cookie(identity_client: AsyncClient) -> None:
    await identity_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "Password1",
            "full_name": "Refresh User",
        },
    )
    login = await identity_client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "Password1"},
    )
    old_cookie = login.cookies.get("delphi_refresh_token")
    refresh = await identity_client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 200
    new_cookie = refresh.cookies.get("delphi_refresh_token")
    assert new_cookie is not None
    assert new_cookie != old_cookie
    assert "access_token" in refresh.json()["data"]["tokens"]

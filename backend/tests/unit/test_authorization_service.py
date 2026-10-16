"""Authorization service unit tests."""

from __future__ import annotations

import pytest

from app.application.authorization.authorization_service import AuthorizationService
from app.domain.value_objects.role import MembershipRole, Permission
from app.shared.exceptions import ForbiddenError

pytestmark = pytest.mark.unit


def test_owner_can_create_workspace() -> None:
    service = AuthorizationService()
    service.require_permission(MembershipRole.OWNER, Permission.WORKSPACE_CREATE)


def test_viewer_cannot_create_workspace() -> None:
    service = AuthorizationService()
    with pytest.raises(ForbiddenError):
        service.require_permission(MembershipRole.VIEWER, Permission.WORKSPACE_CREATE)


def test_viewer_can_read_datasets() -> None:
    service = AuthorizationService()
    assert service.has_permission(MembershipRole.VIEWER, Permission.DATASET_READ)


def test_viewer_cannot_upload_datasets() -> None:
    service = AuthorizationService()
    with pytest.raises(ForbiddenError):
        service.require_permission(MembershipRole.VIEWER, Permission.DATASET_CREATE)


def test_analyst_can_read_projects() -> None:
    service = AuthorizationService()
    assert service.has_permission(MembershipRole.ANALYST, Permission.PROJECT_READ)

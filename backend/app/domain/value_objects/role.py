"""Role and permission value objects for organization-scoped RBAC.

Roles are assigned via Membership (organization ↔ user). Permissions are
checked centrally by the authorization service — never scattered in routers.
"""

from __future__ import annotations

from enum import StrEnum


class MembershipRole(StrEnum):
    """Organization-level role. Ordered by privilege (highest first)."""

    OWNER = "owner"
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

    @property
    def rank(self) -> int:
        """Numeric rank where lower is more privileged."""
        return _ROLE_RANK[self]


_ROLE_RANK: dict[MembershipRole, int] = {
    MembershipRole.OWNER: 0,
    MembershipRole.ADMIN: 1,
    MembershipRole.ANALYST: 2,
    MembershipRole.VIEWER: 3,
}


class Permission(StrEnum):
    """Fine-grained capabilities checked by the authorization service."""

    # Organization
    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_UPDATE = "organization:update"
    ORGANIZATION_DELETE = "organization:delete"
    MEMBER_INVITE = "member:invite"
    MEMBER_MANAGE = "member:manage"

    # Workspace
    WORKSPACE_CREATE = "workspace:create"
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_UPDATE = "workspace:update"
    WORKSPACE_DELETE = "workspace:delete"

    # Project
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    # Dataset (Phase 3)
    DATASET_CREATE = "dataset:create"
    DATASET_READ = "dataset:read"
    DATASET_UPDATE = "dataset:update"
    DATASET_DELETE = "dataset:delete"

    # Statistics (Phase 5)
    STATISTICS_READ = "statistics:read"
    STATISTICS_CREATE = "statistics:create"

    # Causal inference (Phase 6)
    CAUSAL_READ = "causal:read"
    CAUSAL_CREATE = "causal:create"

    # Simulation (Phase 7)
    SIMULATION_READ = "simulation:read"
    SIMULATION_CREATE = "simulation:create"

    # Decision intelligence (Phase 8)
    DECISION_READ = "decision:read"
    DECISION_CREATE = "decision:create"

    # Executive intelligence (Phase 9)
    REPORT_READ = "report:read"
    REPORT_CREATE = "report:create"

    # Unified workspace (Phase 10)
    WORKSPACE_SEARCH = "workspace:search"
    SESSION_READ = "session:read"
    SESSION_CREATE = "session:create"
    SESSION_UPDATE = "session:update"

    # Enterprise infrastructure (Phase 11)
    JOB_READ = "job:read"
    JOB_CREATE = "job:create"
    JOB_CANCEL = "job:cancel"
    INFRA_READ = "infra:read"
    INFRA_MANAGE = "infra:manage"

    # AI Decision Copilot (Phase 13)
    COPILOT_READ = "copilot:read"
    COPILOT_CREATE = "copilot:create"


ROLE_PERMISSIONS: dict[MembershipRole, frozenset[Permission]] = {
    MembershipRole.OWNER: frozenset(Permission),
    MembershipRole.ADMIN: frozenset(
        p
        for p in Permission
        if p not in {Permission.ORGANIZATION_DELETE}
    ),
    MembershipRole.ANALYST: frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.WORKSPACE_READ,
            Permission.WORKSPACE_CREATE,
            Permission.WORKSPACE_UPDATE,
            Permission.PROJECT_CREATE,
            Permission.PROJECT_READ,
            Permission.PROJECT_UPDATE,
            Permission.DATASET_CREATE,
            Permission.DATASET_READ,
            Permission.DATASET_UPDATE,
            Permission.STATISTICS_READ,
            Permission.STATISTICS_CREATE,
            Permission.CAUSAL_READ,
            Permission.CAUSAL_CREATE,
            Permission.SIMULATION_READ,
            Permission.SIMULATION_CREATE,
            Permission.DECISION_READ,
            Permission.DECISION_CREATE,
            Permission.REPORT_READ,
            Permission.REPORT_CREATE,
            Permission.WORKSPACE_SEARCH,
            Permission.SESSION_READ,
            Permission.SESSION_CREATE,
            Permission.SESSION_UPDATE,
            Permission.JOB_READ,
            Permission.JOB_CREATE,
            Permission.JOB_CANCEL,
            Permission.INFRA_READ,
            Permission.COPILOT_READ,
            Permission.COPILOT_CREATE,
        }
    ),
    MembershipRole.VIEWER: frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.WORKSPACE_READ,
            Permission.PROJECT_READ,
            Permission.DATASET_READ,
            Permission.STATISTICS_READ,
            Permission.CAUSAL_READ,
            Permission.SIMULATION_READ,
            Permission.DECISION_READ,
            Permission.REPORT_READ,
            Permission.WORKSPACE_SEARCH,
            Permission.SESSION_READ,
            Permission.JOB_READ,
            Permission.INFRA_READ,
            Permission.COPILOT_READ,
        }
    ),
}

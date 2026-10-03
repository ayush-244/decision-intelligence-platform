"""Canonical audit action identifiers — append-only, stable for compliance."""

from __future__ import annotations

from enum import StrEnum


class AuditAction(StrEnum):
    """Security-relevant actions recorded in the immutable audit log."""

    # Authentication
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGIN_FAILED = "user.login_failed"
    USER_LOGOUT = "user.logout"
    TOKEN_REFRESHED = "user.token_refreshed"

    # Tenancy
    ORGANIZATION_CREATED = "organization.created"
    WORKSPACE_CREATED = "workspace.created"
    PROJECT_CREATED = "project.created"

    # Datasets
    DATASET_UPLOADED = "dataset.uploaded"
    DATASET_DELETED = "dataset.deleted"

    # Analyses
    ANALYSIS_RUN = "analysis.run"
    SIMULATION_RUN = "simulation.run"
    DECISION_RUN = "decision.run"
    REPORT_GENERATED = "report.generated"
    REPORT_EXPORTED = "report.exported"

    # Infrastructure
    JOB_SUBMITTED = "job.submitted"
    JOB_CANCELLED = "job.cancelled"
    JOB_RETRIED = "job.retried"
    CACHE_INVALIDATED = "cache.invalidated"

    # AI Copilot (Phase 13)
    COPILOT_CONVERSATION_CREATED = "copilot.conversation_created"
    COPILOT_MESSAGE_SENT = "copilot.message_sent"

    # Security
    AUTHORIZATION_DENIED = "security.authorization_denied"
    RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"

"""Unified workspace value objects."""

from __future__ import annotations

from enum import StrEnum


class DecisionSessionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class WorkflowStep(StrEnum):
    SELECT_PROJECT = "select_project"
    SELECT_VERSION = "select_version"
    DATA_INTELLIGENCE = "data_intelligence"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    REVIEW_ASSUMPTIONS = "review_assumptions"
    CAUSAL_DAG = "causal_dag"
    CAUSAL_ANALYSIS = "causal_analysis"
    SIMULATION = "simulation"
    RECOMMENDATIONS = "recommendations"
    EXECUTIVE_REPORT = "executive_report"
    SAVE_SESSION = "save_session"


WORKFLOW_STEP_ORDER: tuple[WorkflowStep, ...] = (
    WorkflowStep.SELECT_PROJECT,
    WorkflowStep.SELECT_VERSION,
    WorkflowStep.DATA_INTELLIGENCE,
    WorkflowStep.STATISTICAL_ANALYSIS,
    WorkflowStep.REVIEW_ASSUMPTIONS,
    WorkflowStep.CAUSAL_DAG,
    WorkflowStep.CAUSAL_ANALYSIS,
    WorkflowStep.SIMULATION,
    WorkflowStep.RECOMMENDATIONS,
    WorkflowStep.EXECUTIVE_REPORT,
    WorkflowStep.SAVE_SESSION,
)


class SessionActivityType(StrEnum):
    SESSION_CREATED = "session_created"
    STEP_COMPLETED = "step_completed"
    DATASET_UPLOADED = "dataset_uploaded"
    INTELLIGENCE_REVIEWED = "intelligence_reviewed"
    ANALYSIS_EXECUTED = "analysis_executed"
    DAG_CREATED = "dag_created"
    CAUSAL_COMPLETED = "causal_completed"
    SIMULATION_COMPLETED = "simulation_completed"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    REPORT_GENERATED = "report_generated"
    REPORT_EXPORTED = "report_exported"
    COMMENT = "comment"
    SESSION_PAUSED = "session_paused"
    SESSION_RESUMED = "session_resumed"
    SESSION_COMPLETED = "session_completed"


class SearchResourceType(StrEnum):
    PROJECT = "project"
    DATASET = "dataset"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    CAUSAL_ANALYSIS = "causal_analysis"
    SIMULATION = "simulation"
    DECISION = "decision"
    REPORT = "report"
    SESSION = "session"

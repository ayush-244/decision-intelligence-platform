"""Simulation engine value objects."""

from __future__ import annotations

from enum import StrEnum


class SimulationRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class InterventionMode(StrEnum):
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    SET_VALUE = "set_value"
    TOGGLE = "toggle"


class ConstraintSeverity(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class ConstraintType(StrEnum):
    MAX_BUDGET = "max_budget"
    MIN_ROI = "min_roi"
    LEGAL = "legal"
    CAPACITY = "capacity"
    OPERATIONAL = "operational"
    CUSTOM = "custom"

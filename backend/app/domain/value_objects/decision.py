"""Decision intelligence value objects."""

from __future__ import annotations

from enum import StrEnum


class DecisionRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DecisionObjective(StrEnum):
    MAXIMIZE_REVENUE = "maximize_revenue"
    MAXIMIZE_PROFIT = "maximize_profit"
    MINIMIZE_CHURN = "minimize_churn"
    INCREASE_RETENTION = "increase_retention"
    REDUCE_COST = "reduce_operational_cost"
    IMPROVE_SATISFACTION = "improve_customer_satisfaction"
    IMPROVE_CONVERSION = "improve_conversion_rate"
    CUSTOM = "custom"


class RecommendationStatus(StrEnum):
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    REJECTED = "rejected"
    DEFERRED = "deferred"

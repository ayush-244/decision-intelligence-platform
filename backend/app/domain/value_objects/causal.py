"""Causal inference value objects."""

from __future__ import annotations

from enum import StrEnum


class CausalRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CausalVariableRole(StrEnum):
    TREATMENT = "treatment"
    OUTCOME = "outcome"
    CONFOUNDER = "confounder"
    MEDIATOR = "mediator"
    COLLIDER = "collider"
    INSTRUMENT = "instrument"
    PROXY = "proxy"
    UNKNOWN = "unknown"


class IdentificationStrategy(StrEnum):
    BACKDOOR = "backdoor"
    FRONTDOOR = "frontdoor"
    INSTRUMENTAL_VARIABLE = "instrumental_variable"
    NOT_IDENTIFIED = "not_identified"


class CausalEstimatorType(StrEnum):
    DIFFERENCE_IN_MEANS = "difference_in_means"
    REGRESSION_ADJUSTMENT = "regression_adjustment"
    PROPENSITY_SCORE_MATCHING = "propensity_score_matching"
    INVERSE_PROBABILITY_WEIGHTING = "inverse_probability_weighting"
    DOUBLE_MACHINE_LEARNING = "double_machine_learning"
    META_LEARNER_T = "meta_learner_t"


class RefutationMethod(StrEnum):
    RANDOM_COMMON_CAUSE = "random_common_cause"
    PLACEBO_TREATMENT = "placebo_treatment"
    SUBSET_VALIDATION = "subset_validation"
    DATA_SUBSET = "data_subset"
    BOOTSTRAP = "bootstrap"


class AssumptionStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"
    NOT_CHECKED = "not_checked"

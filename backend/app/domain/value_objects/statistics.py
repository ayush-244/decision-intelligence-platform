"""Statistical analysis value objects."""

from __future__ import annotations

from enum import StrEnum


class AnalysisRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisGoal(StrEnum):
    """High-level research objective — drives test selection."""

    DESCRIBE = "describe"
    COMPARE_GROUPS = "compare_groups"
    COMPARE_PAIRED = "compare_paired"
    ASSOCIATION = "association"
    PREDICT_CONTINUOUS = "predict_continuous"
    PREDICT_BINARY = "predict_binary"
    TEST_CHANGE = "test_change"


class StatisticalTestType(StrEnum):
    DESCRIPTIVE = "descriptive"
    ONE_SAMPLE_TTEST = "one_sample_ttest"
    INDEPENDENT_TTEST = "independent_ttest"
    PAIRED_TTEST = "paired_ttest"
    WELCH_TTEST = "welch_ttest"
    ANOVA = "anova"
    CHI_SQUARE = "chi_square"
    FISHER_EXACT = "fisher_exact"
    MANN_WHITNEY_U = "mann_whitney_u"
    WILCOXON_SIGNED_RANK = "wilcoxon_signed_rank"
    PEARSON_CORRELATION = "pearson_correlation"
    SPEARMAN_CORRELATION = "spearman_correlation"
    KENDALL_CORRELATION = "kendall_correlation"
    SIMPLE_LINEAR_REGRESSION = "simple_linear_regression"
    MULTIPLE_LINEAR_REGRESSION = "multiple_linear_regression"
    LOGISTIC_REGRESSION = "logistic_regression"


class VariableRole(StrEnum):
    OUTCOME = "outcome"
    PREDICTOR = "predictor"
    GROUPING = "grouping"
    COVARIATE = "covariate"
    IDENTIFIER = "identifier"


class AssumptionStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"
    NOT_CHECKED = "not_checked"

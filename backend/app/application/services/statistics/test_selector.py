"""Rule-based statistical test recommendation engine."""

from __future__ import annotations

from app.application.dto.statistics import AnalysisRequestDTO, TestRecommendationDTO, VariableSpecDTO
from app.application.services.statistics.data_extractor import AnalysisDataExtractor, is_numeric
from app.domain.value_objects.statistics import AnalysisGoal, StatisticalTestType
import polars as pl


class StatisticalTestSelector:
    """Recommend appropriate tests from goal, variable types, and sample size."""

    def __init__(self) -> None:
        self._extractor = AnalysisDataExtractor()

    def recommend(
        self,
        *,
        request: AnalysisRequestDTO,
        frame: pl.DataFrame,
    ) -> TestRecommendationDTO:
        if request.test_type is not None:
            return TestRecommendationDTO(
                recommended_test=request.test_type,
                confidence=1.0,
                reasoning="User-specified test type.",
                expected_assumptions=self._expected_assumptions(request.test_type),
                limitations=("Manual test selection bypasses automatic assumption checks.",),
                alternatives=(),
            )

        goal = AnalysisGoal(request.goal)
        roles = {v.role: v for v in request.variables}

        if goal is AnalysisGoal.DESCRIBE:
            return self._rec(StatisticalTestType.DESCRIPTIVE, 1.0,
                "Describing central tendency and spread is appropriate for exploratory goals.",
                ("No distributional assumptions for descriptive summaries.",),
                ())

        if goal is AnalysisGoal.ASSOCIATION:
            return self._association_rec(roles, frame)

        if goal is AnalysisGoal.PREDICT_CONTINUOUS:
            preds = [v for v in request.variables if v.role in {"predictor", "covariate"}]
            test = (
                StatisticalTestType.MULTIPLE_LINEAR_REGRESSION
                if len(preds) > 1
                else StatisticalTestType.SIMPLE_LINEAR_REGRESSION
            )
            return self._rec(test, 0.9,
                "Continuous outcome with predictors suggests linear regression.",
                ("Linearity", "Independence", "Homoscedasticity", "Residual normality"),
                ("Check multicollinearity with VIF for multiple predictors.",))

        if goal is AnalysisGoal.PREDICT_BINARY:
            return self._rec(StatisticalTestType.LOGISTIC_REGRESSION, 0.85,
                "Binary or categorical outcome with predictors suggests logistic regression.",
                ("Independence", "Linearity of log-odds", "Adequate sample size"),
                ("Consider regularization if predictors are numerous.",))

        if goal is AnalysisGoal.COMPARE_PAIRED:
            return self._rec(
                StatisticalTestType.PAIRED_TTEST, 0.85,
                "Paired measurements suggest a paired t-test (or Wilcoxon if normality fails).",
                ("Normality of differences", "Independence of pairs"),
                (),
                (StatisticalTestType.WILCOXON_SIGNED_RANK,),
            )

        if goal is AnalysisGoal.COMPARE_GROUPS or goal is AnalysisGoal.TEST_CHANGE:
            return self._group_comparison_rec(roles, frame)

        return self._rec(StatisticalTestType.DESCRIPTIVE, 0.5,
            "Could not determine a specific test — defaulting to descriptive statistics.",
            (), ("Clarify your research question and variable roles.",))

    def _association_rec(
        self, roles: dict[str, VariableSpecDTO], frame: pl.DataFrame
    ) -> TestRecommendationDTO:
        outcome = roles.get("outcome")
        predictor = roles.get("predictor")
        if outcome and predictor:
            o_num = is_numeric(frame[outcome.name].dtype)
            p_num = is_numeric(frame[predictor.name].dtype)
            if o_num and p_num:
                return self._rec(
                    StatisticalTestType.PEARSON_CORRELATION, 0.9,
                    "Two numeric variables — Pearson correlation (Spearman if non-normal).",
                    ("Linearity", "Normality", "No extreme outliers"),
                    (),
                    (StatisticalTestType.SPEARMAN_CORRELATION, StatisticalTestType.KENDALL_CORRELATION),
                )
            return self._rec(
                StatisticalTestType.CHI_SQUARE, 0.8,
                "Categorical association — chi-square test of independence.",
                ("Independence", "Expected frequencies >= 5"),
                (),
                (StatisticalTestType.FISHER_EXACT,),
            )
        return self._rec(StatisticalTestType.PEARSON_CORRELATION, 0.5,
            "Association goal requires outcome and predictor variables.", (), ())

    def _group_comparison_rec(
        self, roles: dict[str, VariableSpecDTO], frame: pl.DataFrame
    ) -> TestRecommendationDTO:
        outcome = roles.get("outcome")
        grouping = roles.get("grouping")
        if not outcome or not grouping:
            return self._rec(StatisticalTestType.INDEPENDENT_TTEST, 0.5,
                "Group comparison requires outcome and grouping variables.", (), ())

        groups = frame[grouping.name].drop_nulls().unique().len()
        if groups == 2:
            return self._rec(
                StatisticalTestType.INDEPENDENT_TTEST, 0.88,
                "Two groups with numeric outcome — independent samples t-test.",
                ("Normality within groups", "Equal variances", "Independence"),
                (),
                (StatisticalTestType.WELCH_TTEST, StatisticalTestType.MANN_WHITNEY_U),
            )
        if groups > 2:
            return self._rec(StatisticalTestType.ANOVA, 0.85,
                f"{groups} groups — one-way ANOVA (Kruskal-Wallis if normality fails).",
                ("Normality within groups", "Equal variances", "Independence"),
                ())
        return self._rec(StatisticalTestType.ONE_SAMPLE_TTEST, 0.7,
            "Single group numeric data — one-sample t-test against reference value.",
            ("Normality",), ())

    @staticmethod
    def _rec(
        test: StatisticalTestType,
        confidence: float,
        reasoning: str,
        assumptions: tuple[str, ...],
        limitations: tuple[str, ...] = (),
        alternatives: tuple[StatisticalTestType, ...] = (),
    ) -> TestRecommendationDTO:
        return TestRecommendationDTO(
            recommended_test=test,
            confidence=confidence,
            reasoning=reasoning,
            expected_assumptions=assumptions,
            limitations=limitations,
            alternatives=alternatives,
        )

    @staticmethod
    def _expected_assumptions(test: StatisticalTestType) -> tuple[str, ...]:
        mapping: dict[StatisticalTestType, tuple[str, ...]] = {
            StatisticalTestType.INDEPENDENT_TTEST: ("Normality", "Equal variances", "Independence"),
            StatisticalTestType.PAIRED_TTEST: ("Normality of differences", "Independence"),
            StatisticalTestType.ANOVA: ("Normality", "Equal variances", "Independence"),
            StatisticalTestType.PEARSON_CORRELATION: ("Linearity", "Normality", "Bivariate outliers"),
            StatisticalTestType.CHI_SQUARE: ("Independence", "Expected frequencies >= 5"),
            StatisticalTestType.SIMPLE_LINEAR_REGRESSION: ("Linearity", "Homoscedasticity", "Residual normality"),
            StatisticalTestType.MULTIPLE_LINEAR_REGRESSION: ("Linearity", "Homoscedasticity", "No severe multicollinearity"),
            StatisticalTestType.LOGISTIC_REGRESSION: ("Independence", "Linearity of log-odds"),
        }
        return mapping.get(test, ())

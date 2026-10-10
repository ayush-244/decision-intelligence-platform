"""Variable role analyzer — classify columns for causal analysis."""

from __future__ import annotations

import polars as pl

from app.application.dto.causal import CausalVariableRoleDTO
from app.application.services.statistics.data_extractor import is_numeric
from app.domain.value_objects.causal import CausalVariableRole


class VariableRoleAnalyzer:
    """Suggest causal roles from data types, cardinality, and naming heuristics."""

    _TREATMENT_HINTS = ("treatment", "intervention", "exposure", "group", "arm", "variant")
    _OUTCOME_HINTS = ("outcome", "target", "response", "revenue", "churn", "retention", "conversion")
    _CONFOUNDER_HINTS = ("age", "gender", "region", "segment", "income", "tenure", "size")

    def analyze(
        self,
        *,
        frame: pl.DataFrame,
        treatment: str,
        outcome: str,
        overrides: dict[str, str] | None = None,
    ) -> tuple[CausalVariableRoleDTO, ...]:
        overrides = overrides or {}
        results: list[CausalVariableRoleDTO] = []

        for col in frame.columns:
            if col in overrides:
                role = CausalVariableRole(overrides[col])
                results.append(
                    CausalVariableRoleDTO(
                        name=col, role=role.value, confidence=1.0,
                        reasoning="User-specified role override.",
                    )
                )
                continue

            if col == treatment:
                results.append(CausalVariableRoleDTO(
                    name=col, role=CausalVariableRole.TREATMENT.value, confidence=1.0,
                    reasoning="Designated treatment variable.",
                ))
                continue
            if col == outcome:
                results.append(CausalVariableRoleDTO(
                    name=col, role=CausalVariableRole.OUTCOME.value, confidence=1.0,
                    reasoning="Designated outcome variable.",
                ))
                continue

            role, confidence, reasoning = self._infer_role(frame, col, treatment, outcome)
            results.append(CausalVariableRoleDTO(
                name=col, role=role.value, confidence=confidence, reasoning=reasoning,
            ))
        return tuple(results)

    def _infer_role(
        self, frame: pl.DataFrame, col: str, treatment: str, outcome: str
    ) -> tuple[CausalVariableRole, float, str]:
        lower = col.lower()
        series = frame[col]
        n_unique = series.n_unique()

        if any(h in lower for h in self._CONFOUNDER_HINTS):
            return (
                CausalVariableRole.CONFOUNDER, 0.75,
                f"Column name '{col}' suggests a demographic or segmentation confounder.",
            )

        if is_numeric(series.dtype) and n_unique > 20:
            return (
                CausalVariableRole.CONFOUNDER, 0.55,
                "Continuous variable with high cardinality — possible confounder; verify domain knowledge.",
            )

        if not is_numeric(series.dtype) and 2 <= n_unique <= 10:
            return (
                CausalVariableRole.CONFOUNDER, 0.6,
                f"Categorical variable with {n_unique} levels — may confound treatment-outcome relationship.",
            )

        if n_unique == frame.height:
            return (
                CausalVariableRole.UNKNOWN, 0.3,
                "Near-unique identifier — unlikely to be a causal variable.",
            )

        return (
            CausalVariableRole.UNKNOWN, 0.4,
            "Insufficient evidence to classify — review manually.",
        )

    def roles_dict(self, roles: tuple[CausalVariableRoleDTO, ...]) -> dict[str, str]:
        return {r.name: r.role for r in roles}

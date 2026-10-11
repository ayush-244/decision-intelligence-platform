"""Compare multiple simulation scenarios side by side."""

from __future__ import annotations

from app.application.dto.simulation import ScenarioComparisonDTO


class ScenarioComparator:
    """Rank scenarios by outcome, ROI, and risk."""

    def compare(
        self,
        entries: list[tuple[str, str, float, float | None, float]],
    ) -> tuple[ScenarioComparisonDTO, ...]:
        """Each entry: (scenario_id, name, expected_outcome, expected_roi, risk_score)."""
        if not entries:
            return ()

        def score(entry: tuple[str, str, float, float | None, float]) -> float:
            _, _, outcome, roi, risk = entry
            roi_val = roi if roi is not None else 0.0
            return outcome * 0.4 + roi_val * 0.4 - risk * 0.2

        ranked = sorted(entries, key=score, reverse=True)
        return tuple(
            ScenarioComparisonDTO(
                scenario_id=sid,
                scenario_name=name,
                expected_outcome=outcome,
                expected_roi=roi,
                risk_score=risk,
                rank=idx + 1,
            )
            for idx, (sid, name, outcome, roi, risk) in enumerate(ranked)
        )

"""Implementation roadmap and decision timeline."""

from __future__ import annotations

from typing import Any

from app.application.dto.executive import TimelineItemDTO


class TimelineEngine:
    """Generate prioritized implementation plans from recommendations."""

    def build_roadmap(
        self, recommendations: list[dict[str, Any]]
    ) -> tuple[TimelineItemDTO, ...]:
        items: list[TimelineItemDTO] = []
        for rec in recommendations[:5]:
            rank = int(rec.get("rank", len(items) + 1))
            difficulty = str(rec.get("implementation_difficulty", "moderate"))
            effort = {"low": "2-4 weeks", "moderate": "1-3 months", "high": "3-6 months"}.get(
                difficulty, "1-3 months"
            )
            risk = float(rec.get("risk", 0.5))
            risk_level = "low" if risk < 0.35 else "moderate" if risk < 0.65 else "high"
            roi = float(rec.get("roi", 0))
            items.append(
                TimelineItemDTO(
                    priority=rank,
                    title=str(rec.get("title", f"Initiative {rank}")),
                    effort=effort,
                    impact=str(rec.get("summary", ""))[:120],
                    dependencies=tuple(rec.get("dependencies", ())),
                    milestones=(
                        "Stakeholder alignment",
                        "Pilot launch",
                        "Measure KPIs",
                        "Scale or pivot",
                    ),
                    timeline=str(rec.get("expected_timeline", effort)),
                    business_owner="Business Lead (assign)",
                    risk_level=risk_level,
                    expected_kpi_changes=(
                        f"ROI target: {roi:.0%}",
                        f"Outcome shift per simulation evidence",
                    ),
                )
            )
        return tuple(items)

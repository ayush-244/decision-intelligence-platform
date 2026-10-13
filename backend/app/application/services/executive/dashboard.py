"""Executive dashboard aggregation."""

from __future__ import annotations

from typing import Any

from app.application.dto.executive import DashboardSnapshotDTO
from app.domain.entities.decision_run import DecisionRun
from app.domain.entities.executive_report import ExecutiveReport
from app.domain.value_objects.decision import DecisionRunStatus


class DashboardEngine:
    """Aggregate pipeline metrics for executive overview."""

    def build(
        self,
        *,
        decisions: list[DecisionRun],
        reports: list[ExecutiveReport],
    ) -> DashboardSnapshotDTO:
        pipeline = {
            "completed": sum(1 for d in decisions if d.status is DecisionRunStatus.COMPLETED),
            "failed": sum(1 for d in decisions if d.status is DecisionRunStatus.FAILED),
            "total": len(decisions),
        }
        status_counts: dict[str, int] = {"approved": 0, "conditional": 0, "deferred": 0, "rejected": 0}
        rois: list[float] = []
        risks: list[float] = []
        confidences: list[float] = []
        recent: list[dict[str, Any]] = []

        for d in decisions:
            if d.status is not DecisionRunStatus.COMPLETED:
                continue
            for rec in d.result.get("recommendations", []):
                st = str(rec.get("status", "approved"))
                status_counts[st] = status_counts.get(st, 0) + 1
                rois.append(float(rec.get("roi", 0)))
                risks.append(float(rec.get("risk", 0)))
                confidences.append(float(rec.get("confidence", 0)))
            recent.append({
                "id": str(d.id),
                "name": d.name,
                "objective": d.primary_objective,
                "created_at": d.created_at.isoformat(),
            })

        health = 0.7
        if decisions:
            completed_ratio = pipeline["completed"] / max(pipeline["total"], 1)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.5
            health = round(0.4 * completed_ratio + 0.6 * avg_conf, 3)

        return DashboardSnapshotDTO(
            business_health_score=health,
            decision_pipeline=pipeline,
            recommendation_status=status_counts,
            roi_overview={
                "average": round(sum(rois) / len(rois), 4) if rois else 0.0,
                "max": round(max(rois), 4) if rois else 0.0,
            },
            risk_overview={
                "average": round(sum(risks) / len(risks), 4) if risks else 0.0,
                "max": round(max(risks), 4) if risks else 0.0,
            },
            confidence_overview={
                "average": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
            },
            recent_decisions=tuple(recent[:10]),
            historical_reports=len(reports),
        )

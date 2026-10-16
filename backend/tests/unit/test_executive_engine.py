"""Unit tests for executive intelligence engines."""

from __future__ import annotations

from app.application.services.executive.business_language import BusinessLanguageEngine
from app.application.services.executive.export import ExportEngine
from app.application.services.executive.explainability import ExplainabilityEngine
from app.application.services.executive.timeline import TimelineEngine
from app.domain.value_objects.executive import ExportFormat


def test_business_language_treatment_effect_narrative() -> None:
    text = BusinessLanguageEngine.treatment_effect_narrative(
        treatment="delivery time",
        outcome="customer retention",
        ate=0.14,
        ci_lower=0.05,
        ci_upper=0.23,
        identified=True,
    )
    assert "delivery time" in text
    assert "14.0%" in text
    assert "backdoor" in text.lower()


def test_business_language_executive_summary() -> None:
    summary = BusinessLanguageEngine.executive_summary(
        objective="Increase retention",
        top_recommendation="Reduce delivery time",
        confidence="moderate",
        roi=0.25,
    )
    assert "Increase retention" in summary
    assert "Reduce delivery time" in summary
    assert "moderate" in summary


def test_explainability_aggregate_confidence() -> None:
    from uuid import uuid4

    from app.domain.entities.decision_run import DecisionRun
    from app.domain.value_objects.decision import DecisionRunStatus
    from app.shared.utils.datetime import utc_now

    now = utc_now()
    decision = DecisionRun(
        id=uuid4(),
        dataset_id=uuid4(),
        version_id=uuid4(),
        organization_id=uuid4(),
        project_id=uuid4(),
        created_by=uuid4(),
        status=DecisionRunStatus.COMPLETED,
        name="Test",
        primary_objective="maximize_revenue",
        configuration={},
        result={"overall_summary": "Test summary", "limitations": []},
        error_message=None,
        executed_at=now,
        created_at=now,
        updated_at=now,
    )
    engine = ExplainabilityEngine()
    block = engine.explain_recommendation(
        rec={
            "title": "Test action",
            "summary": "Do something",
            "confidence": 0.7,
            "roi": 0.2,
            "risk": 0.3,
            "rank": 1,
            "decision_score": {"overall_score": 0.8},
            "evidence": {},
        },
        causal=None,
        simulation=None,
        decision=decision,
    )
    agg = engine.aggregate_confidence((block,))
    assert "level" in agg
    assert "score" in agg
    assert agg["score"] > 0


def test_timeline_build_roadmap() -> None:
    roadmap = TimelineEngine().build_roadmap(
        [
            {
                "title": "Pilot intervention",
                "rank": 1,
                "roi": 0.3,
                "risk": 0.2,
                "confidence": 0.75,
            }
        ]
    )
    assert len(roadmap) == 1
    assert roadmap[0].priority == 1
    assert roadmap[0].timeline


def test_export_markdown_and_csv() -> None:
    report = {
        "name": "Q3 Strategy",
        "executive_summary": "Strong opportunity.",
        "business_objective": "Grow revenue",
        "key_findings": ["Finding one"],
        "decision_summary": "Proceed with pilot",
        "top_recommendations": [{"title": "Pilot", "summary": "Start small"}],
        "confidence_assessment": {"summary": "Moderate confidence"},
        "implementation_roadmap": [
            {"title": "Pilot", "timeline": "Q1", "risk_level": "low"}
        ],
    }
    engine = ExportEngine()
    md, media_type, ext = engine.export(report=report, format=ExportFormat.MARKDOWN)
    assert "# Q3 Strategy" in md
    assert media_type == "text/markdown"
    assert ext == "md"

    csv_content, _, csv_ext = engine.export(report=report, format=ExportFormat.CSV)
    assert "executive_summary" in csv_content
    assert csv_ext == "csv"

    json_content, _, json_ext = engine.export(report=report, format=ExportFormat.JSON)
    assert "Q3 Strategy" in json_content
    assert json_ext == "json"

"""Unit tests for unified workspace engines."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.services.workspace.comparison import ComparisonEngine
from app.application.services.workspace.session_engine import DecisionSessionEngine
from app.domain.entities.decision_session import DecisionSession
from app.domain.value_objects.workspace import DecisionSessionStatus, WorkflowStep
from app.shared.utils.datetime import utc_now


def _session(name: str = "A") -> DecisionSession:
    now = utc_now()
    return DecisionSession(
        id=uuid4(),
        dataset_id=uuid4(),
        version_id=uuid4(),
        organization_id=uuid4(),
        project_id=uuid4(),
        created_by=uuid4(),
        name=name,
        description=None,
        status=DecisionSessionStatus.ACTIVE,
        version_number=1,
        current_step=WorkflowStep.CAUSAL_ANALYSIS,
        statistical_analysis_id=None,
        dag_version_id=None,
        causal_analysis_id=None,
        simulation_run_id=None,
        decision_run_id=None,
        executive_report_id=None,
        workspace_state={},
        configuration={},
        paused_at=None,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )


def test_session_progress_percent() -> None:
    engine = DecisionSessionEngine(sessions=None, activities=None)  # type: ignore[arg-type]
    progress = engine.progress(_session())
    assert progress.current_step == WorkflowStep.CAUSAL_ANALYSIS.value
    assert progress.percent_complete > 0
    assert progress.next_step is not None


@pytest.mark.asyncio
async def test_comparison_summary() -> None:
    result = await ComparisonEngine().compare_sessions(
        session_a=_session("Alpha"),
        session_b=_session("Beta"),
        simulations=None,  # type: ignore[arg-type]
        decisions=None,  # type: ignore[arg-type]
        reports=None,  # type: ignore[arg-type]
        organization_id=uuid4(),
    )
    assert "Alpha" in result.summary
    assert len(result.items) >= 3

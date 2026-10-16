"""Unit tests for AI Decision Copilot components."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.dto.copilot import StructuredContext
from app.application.services.copilot.citation_generator import CitationGenerator
from app.application.services.copilot.prompt_composer import CopilotPromptComposer
from app.application.services.copilot.response_validator import CopilotResponseValidator
from app.infrastructure.llm.mock_llm_provider import MockLlmProvider
from app.shared.exceptions import BusinessValidationError


def _sample_context() -> StructuredContext:
    stat_id = str(uuid4())
    causal_id = str(uuid4())
    sim_id = str(uuid4())
    decision_id = str(uuid4())
    report_id = str(uuid4())
    return StructuredContext(
        dataset={"id": str(uuid4()), "name": "Revenue dataset"},
        data_quality={"health_score": 0.82, "quality_score": 0.91},
        statistics=[
            {
                "id": stat_id,
                "short_id": 1,
                "goal": "Compare groups",
                "summary": "Significant difference detected.",
            }
        ],
        causal=[
            {
                "id": causal_id,
                "short_id": 1,
                "treatment": "treatment",
                "outcome": "outcome",
                "summary": "Estimated ATE: 2.5",
            }
        ],
        simulations=[
            {
                "id": sim_id,
                "short_id": 1,
                "name": "Uplift scenario",
                "summary": "Expected outcome: 12%",
            }
        ],
        decisions=[
            {
                "id": decision_id,
                "short_id": 1,
                "objective": "maximize_revenue",
                "top_recommendation": "Reduce delivery time",
            }
        ],
        reports=[
            {
                "id": report_id,
                "short_id": 1,
                "name": "Q3 Executive Brief",
                "summary": "Revenue uplift expected.",
            }
        ],
    )


def test_prompt_composer_includes_verified_context() -> None:
    composer = CopilotPromptComposer()
    context = _sample_context()
    system = composer.compose_system(context)
    assert "NEVER invent numbers" in system
    assert "[Statistical Analysis #1]" in system
    assert composer.prompt_version == "1.0.0"


def test_response_validator_accepts_valid_citations() -> None:
    validator = CopilotResponseValidator()
    context = _sample_context()
    content = (
        "Delphi recommends reducing delivery time based on [Decision #1] "
        "after [Statistical Analysis #1] and [Causal Analysis #1]."
    )
    result = validator.validate(content=content, context=context)
    assert result.valid is True


def test_response_validator_rejects_hallucinated_citation() -> None:
    validator = CopilotResponseValidator()
    context = _sample_context()
    content = "See [Statistical Analysis #99] for details."
    result = validator.validate(content=content, context=context)
    assert result.valid is False
    assert any("non-existent" in v for v in result.violations)


def test_response_validator_enforce_raises() -> None:
    validator = CopilotResponseValidator()
    context = StructuredContext()
    with pytest.raises(BusinessValidationError) as exc:
        validator.enforce_or_raise(
            content="The p-value is 0.001 for treatment effect.",
            context=context,
        )
    assert exc.value.code == "copilot_validation_failed"


def test_citation_generator_extracts_labels() -> None:
    generator = CitationGenerator()
    context = _sample_context()
    content = "Evidence: [Decision #1] and [Executive Report #1]."
    citations = generator.extract(content=content, context=context)
    assert len(citations) == 2
    assert citations[0].label == "Decision #1"
    assert citations[1].label == "Executive Report #1"


@pytest.mark.asyncio
async def test_mock_llm_provider_returns_analyst_response() -> None:
    provider = MockLlmProvider()
    from app.domain.ports.llm_provider import LlmCompletionRequest, LlmMessage

    response = await provider.complete(
        LlmCompletionRequest(
            messages=[LlmMessage(role="user", content="Summarize for the CEO")],
            system_prompt="VERIFIED CONTEXT:\n[Decision #1]",
        )
    )
    assert "Executive Summary" in response.content
    assert response.provider == "mock"

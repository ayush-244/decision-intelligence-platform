"""Deterministic LLM provider — interprets verified context without external APIs."""

from __future__ import annotations

from app.application.services.executive.business_language import BusinessLanguageEngine
from app.domain.ports.llm_provider import (
    LlmCompletionRequest,
    LlmCompletionResponse,
    LlmProviderPort,
)


class MockLlmProvider(LlmProviderPort):
    """Template-based analyst responses for tests and offline deployments."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        user_msg = request.messages[-1].content if request.messages else ""
        context_block = request.system_prompt
        response = self._synthesize(user_msg, context_block)
        return LlmCompletionResponse(
            content=response,
            provider=self.provider_name,
            model="delphi-analyst-v1",
            usage={"prompt_tokens": len(request.system_prompt), "completion_tokens": len(response)},
        )

    def _synthesize(self, user_message: str, context: str) -> str:
        lower = user_message.lower()
        bl = BusinessLanguageEngine()

        if "ceo" in lower or "executive" in lower or "summarize" in lower:
            return self._executive_summary(context)

        if "assumption" in lower or "causal" in lower:
            return (
                "The causal conclusions in your workspace depend on the backdoor identification "
                "strategy and covariate adjustment applied by Delphi's Causal Engine. "
                "[Causal Analysis #1] provides the estimated treatment effect — I cannot restate "
                "numbers not shown in the verified context. Review the DAG and refutation tests "
                "before acting on this recommendation."
            )

        if "compare" in lower or "scenario" in lower:
            return (
                "Comparing scenarios using verified Delphi outputs:\n\n"
                "- [Simulation #1] projects outcomes under the primary intervention scenario.\n"
                "- [Decision #1] ranks recommendations by expected business impact.\n\n"
                "Use the Simulation and Decision workspaces for side-by-side numeric comparison. "
                "I only interpret stored results — I do not generate new projections."
            )

        if "recommend" in lower or "why" in lower:
            return (
                "Delphi's recommendation is grounded in the full analytical pipeline:\n\n"
                "1. [Statistical Analysis #1] establishes whether observed differences are reliable.\n"
                "2. [Causal Analysis #1] estimates the intervention effect under stated assumptions.\n"
                "3. [Simulation #1] stress-tests the intervention under uncertainty.\n"
                "4. [Decision #1] synthesizes tradeoffs into a ranked recommendation.\n\n"
                "The top recommendation reflects maximizing your stated objective while respecting "
                "constraints configured in the Decision Engine. See [Decision #1] for the evidence chain."
            )

        if "evidence" in lower:
            return (
                "Evidence supporting the primary findings:\n"
                "- [Statistical Analysis #1]: hypothesis test results\n"
                "- [Causal Analysis #1]: treatment effect estimate\n"
                "- [Decision #1]: ranked recommendations with scores\n\n"
                "Each citation links to a persisted Delphi analysis you can audit in the Evidence panel."
            )

        return (
            f"Based on the verified analytical context for your dataset, I can help explain "
            f"statistical results, causal assumptions, simulations, and recommendations. "
            f"Your question: \"{user_message[:120]}\"\n\n"
            f"Key available evidence includes analyses cited in the context snapshot. "
            f"I only reference outputs computed by Delphi's engines — I never estimate effects independently."
        )

    def _executive_summary(self, context: str) -> str:
        return (
            "**Executive Summary** (from verified Delphi analyses only)\n\n"
            "Delphi has completed a structured analytical review of your dataset. "
            "Data quality and statistical readiness have been assessed. "
            "Causal and simulation engines have produced intervention estimates subject to "
            "documented assumptions.\n\n"
            "**Key takeaway:** The Decision Engine's top recommendation reflects the best "
            "expected outcome given your configured objective — see [Decision #1] and "
            "[Executive Report #1] for the full narrative.\n\n"
            "*All figures originate from persisted Delphi analyses. This summary does not "
            "introduce new calculations.*"
        )

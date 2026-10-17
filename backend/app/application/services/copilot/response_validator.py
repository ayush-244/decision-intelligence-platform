"""Validate AI responses against verified evidence — reject hallucinations."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.application.dto.copilot import StructuredContext
from app.shared.exceptions import BusinessValidationError


_CITATION_PATTERN = re.compile(
    r"\[(Statistical Analysis|Causal Analysis|Simulation|Decision|Executive Report) #(\d+)\]",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    sanitized_content: str
    violations: tuple[str, ...]


class CopilotResponseValidator:
    """Ensure cited analyses exist in the verified context snapshot."""

    def validate(
        self,
        *,
        content: str,
        context: StructuredContext,
    ) -> ValidationResult:
        violations: list[str] = []
        citations = _CITATION_PATTERN.findall(content)

        type_map = {
            "statistical analysis": context.statistics,
            "causal analysis": context.causal,
            "simulation": context.simulations,
            "decision": context.decisions,
            "executive report": context.reports,
        }

        for cite_type, num_str in citations:
            entries = type_map.get(cite_type.lower(), [])
            num = int(num_str)
            if num < 1 or num > len(entries):
                violations.append(
                    f"Citation [{cite_type} #{num}] references non-existent analysis."
                )

        if self._contains_fabricated_numbers(content, context):
            violations.append("Response may contain numbers not present in verified context.")

        if violations:
            sanitized = (
                content
                + "\n\n---\n*Note: Some claims could not be verified against stored analyses. "
                "Please refer to the Evidence panel for authoritative results.*"
            )
            return ValidationResult(valid=False, sanitized_content=sanitized, violations=tuple(violations))

        return ValidationResult(valid=True, sanitized_content=content, violations=())

    def enforce_or_raise(self, *, content: str, context: StructuredContext) -> str:
        result = self.validate(content=content, context=context)
        if not result.valid:
            raise BusinessValidationError(
                "AI response failed validation.",
                code="copilot_validation_failed",
                details={"violations": list(result.violations)},
            )
        return result.sanitized_content

    @staticmethod
    def _contains_fabricated_numbers(content: str, context: StructuredContext) -> bool:
        """Heuristic: flag invented p-values or ATEs when no context exists."""
        lower = content.lower()
        if not context.statistics and re.search(r"\bp[- ]?value\b", lower):
            return True
        if not context.causal and re.search(r"\bate\b", lower):
            return True
        return False

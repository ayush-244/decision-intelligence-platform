"""Extract and format evidence citations from context and response."""

from __future__ import annotations

import re
from typing import Any

from app.application.dto.copilot import CitationDTO, StructuredContext
from app.domain.value_objects.copilot import CitationResourceType


_CITATION_PATTERN = re.compile(
    r"\[(Statistical Analysis|Causal Analysis|Simulation|Decision|Executive Report) #(\d+)\]",
    re.IGNORECASE,
)


class CitationGenerator:
    """Build citation DTOs linking statements to stored analyses."""

    def extract(
        self,
        *,
        content: str,
        context: StructuredContext,
    ) -> list[CitationDTO]:
        citations: list[CitationDTO] = []
        seen: set[str] = set()

        type_config: list[tuple[str, list[dict[str, Any]], CitationResourceType, str]] = [
            ("statistical analysis", context.statistics, CitationResourceType.STATISTICAL_ANALYSIS, "Statistical Analysis"),
            ("causal analysis", context.causal, CitationResourceType.CAUSAL_ANALYSIS, "Causal Analysis"),
            ("simulation", context.simulations, CitationResourceType.SIMULATION, "Simulation"),
            ("decision", context.decisions, CitationResourceType.DECISION, "Decision"),
            ("executive report", context.reports, CitationResourceType.EXECUTIVE_REPORT, "Executive Report"),
        ]

        for cite_type, num_str in _CITATION_PATTERN.findall(content):
            for key, entries, resource_type, label_prefix in type_config:
                if cite_type.lower() != key:
                    continue
                num = int(num_str)
                if num < 1 or num > len(entries):
                    continue
                entry = entries[num - 1]
                resource_id = entry.get("id", "")
                dedup = f"{resource_type}:{resource_id}"
                if dedup in seen:
                    continue
                seen.add(dedup)
                citations.append(
                    CitationDTO(
                        resource_type=resource_type.value,
                        resource_id=resource_id,
                        label=f"{label_prefix} #{num}",
                        excerpt=str(entry.get("summary", ""))[:200],
                    )
                )
        return citations

    def primary_citations(self, context: StructuredContext) -> list[CitationDTO]:
        """Default citations when response doesn't cite explicitly."""
        citations: list[CitationDTO] = []
        if context.decisions:
            d = context.decisions[0]
            citations.append(
                CitationDTO(
                    resource_type=CitationResourceType.DECISION.value,
                    resource_id=d["id"],
                    label="Decision #1",
                    excerpt=str(d.get("top_recommendation", ""))[:200],
                )
            )
        if context.statistics:
            s = context.statistics[0]
            citations.append(
                CitationDTO(
                    resource_type=CitationResourceType.STATISTICAL_ANALYSIS.value,
                    resource_id=s["id"],
                    label="Statistical Analysis #1",
                    excerpt=str(s.get("summary", ""))[:200],
                )
            )
        return citations

"""Export executive reports to multiple formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from app.domain.value_objects.executive import ExportFormat


class ExportEngine:
    """Generate Markdown, CSV, JSON, and print-ready PDF (Markdown) exports."""

    def export(self, *, report: dict[str, Any], format: ExportFormat) -> tuple[str, str, str]:
        """Returns (content, media_type, filename_extension)."""
        if format is ExportFormat.JSON:
            return json.dumps(report, indent=2), "application/json", "json"
        if format is ExportFormat.CSV:
            return self._to_csv(report), "text/csv", "csv"
        if format in {ExportFormat.MARKDOWN, ExportFormat.PDF}:
            md = self._to_markdown(report)
            media = "text/markdown" if format is ExportFormat.MARKDOWN else "application/pdf"
            ext = "md" if format is ExportFormat.MARKDOWN else "md"
            return md, media, ext
        return self._to_markdown(report), "text/markdown", "md"

    def _to_markdown(self, report: dict[str, Any]) -> str:
        lines = [
            f"# {report.get('name', 'Executive Report')}",
            "",
            "## Executive Summary",
            report.get("executive_summary", ""),
            "",
            "## Business Objective",
            report.get("business_objective", ""),
            "",
            "## Key Findings",
        ]
        for finding in report.get("key_findings", []):
            lines.append(f"- {finding}")
        lines.extend(["", "## Decision Summary", report.get("decision_summary", ""), "", "## Top Recommendations"])
        for rec in report.get("top_recommendations", []):
            lines.append(f"### {rec.get('title', 'Recommendation')}")
            lines.append(rec.get("summary", ""))
            lines.append("")
        lines.extend(["## Confidence Assessment", report.get("confidence_assessment", {}).get("summary", ""), ""])
        lines.extend(["## Implementation Roadmap"])
        for item in report.get("implementation_roadmap", []):
            lines.append(f"- **{item.get('title')}** — {item.get('timeline')} ({item.get('risk_level')} risk)")
        if report.get("include_technical_appendix"):
            lines.extend(["", "## Appendix: Technical Evidence", "```json", json.dumps(report.get("appendix", {}), indent=2)[:4000], "```"])
        return "\n".join(lines)

    def _to_csv(self, report: dict[str, Any]) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["section", "content"])
        writer.writerow(["executive_summary", report.get("executive_summary", "")])
        writer.writerow(["business_objective", report.get("business_objective", "")])
        for i, rec in enumerate(report.get("top_recommendations", []), start=1):
            writer.writerow([f"recommendation_{i}", rec.get("title", "")])
            writer.writerow([f"recommendation_{i}_summary", rec.get("summary", "")])
        return buffer.getvalue()

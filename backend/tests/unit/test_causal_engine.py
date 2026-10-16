"""Unit tests for causal DAG and identification."""

from __future__ import annotations

from app.application.services.causal.dag_manager import DAGManager
from app.application.services.causal.identification import IdentificationEngine
from app.infrastructure.causal.networkx_graph import NetworkXCausalGraph


def test_dag_validation_rejects_cycle() -> None:
    manager = DAGManager()
    result = manager.validate(
        nodes=[{"id": "A", "label": "A"}, {"id": "B", "label": "B"}],
        edges=[{"source": "A", "target": "B"}, {"source": "B", "target": "A"}],
    )
    assert not result.is_valid
    assert result.validation_errors


def test_backdoor_identification_with_confounder() -> None:
    graph = NetworkXCausalGraph.from_dict({
        "nodes": [
            {"id": "Z", "label": "Z", "role": "confounder"},
            {"id": "T", "label": "T", "role": "treatment"},
            {"id": "Y", "label": "Y", "role": "outcome"},
        ],
        "edges": [
            {"source": "Z", "target": "T"},
            {"source": "Z", "target": "Y"},
            {"source": "T", "target": "Y"},
        ],
    })
    report = IdentificationEngine().identify(graph=graph, treatment="T", outcome="Y")
    assert report.identified
    assert report.strategy.value == "backdoor"
    assert "Z" in report.adjustment_set

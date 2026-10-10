"""NetworkX implementation of CausalGraphPort — internal detail, not exposed via API."""

from __future__ import annotations

from typing import Any

import networkx as nx

from app.domain.ports.causal_graph import (
    CausalGraphPort,
    GraphEdge,
    GraphNode,
    GraphValidationResult,
)


class NetworkXCausalGraph(CausalGraphPort):
    """DAG backed by NetworkX DiGraph."""

    def __init__(self) -> None:
        self._graph = nx.DiGraph()

    def add_node(self, node: GraphNode) -> None:
        self._graph.add_node(node.id, label=node.label, role=node.role)

    def add_edge(self, edge: GraphEdge) -> None:
        self._graph.add_edge(edge.source, edge.target)

    def validate(self) -> GraphValidationResult:
        errors: list[str] = []
        if not self._graph.nodes:
            errors.append("DAG has no nodes.")
        is_acyclic = nx.is_directed_acyclic_graph(self._graph)
        if not is_acyclic:
            try:
                cycle = nx.find_cycle(self._graph)
                errors.append(f"Cycle detected: {' → '.join(f'{u}→{v}' for u, v in cycle)}")
            except nx.NetworkXNoCycle:
                errors.append("Graph contains a cycle.")
        return GraphValidationResult(
            is_valid=len(errors) == 0 and is_acyclic,
            is_acyclic=is_acyclic,
            errors=tuple(errors),
        )

    def ancestors(self, node_id: str) -> frozenset[str]:
        if node_id not in self._graph:
            return frozenset()
        return frozenset(nx.ancestors(self._graph, node_id))

    def descendants(self, node_id: str) -> frozenset[str]:
        if node_id not in self._graph:
            return frozenset()
        return frozenset(nx.descendants(self._graph, node_id))

    def parents(self, node_id: str) -> frozenset[str]:
        if node_id not in self._graph:
            return frozenset()
        return frozenset(self._graph.predecessors(node_id))

    def children(self, node_id: str) -> frozenset[str]:
        if node_id not in self._graph:
            return frozenset()
        return frozenset(self._graph.successors(node_id))

    def nodes(self) -> tuple[str, ...]:
        return tuple(self._graph.nodes())

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                {"id": n, "label": d.get("label", n), "role": d.get("role")}
                for n, d in self._graph.nodes(data=True)
            ],
            "edges": [{"source": u, "target": v} for u, v in self._graph.edges()],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkXCausalGraph:
        graph = cls()
        for node in data.get("nodes", []):
            graph.add_node(
                GraphNode(
                    id=str(node["id"]),
                    label=str(node.get("label", node["id"])),
                    role=node.get("role"),
                )
            )
        for edge in data.get("edges", []):
            graph.add_edge(GraphEdge(source=str(edge["source"]), target=str(edge["target"])))
        return graph

    @property
    def nx_graph(self) -> nx.DiGraph:
        return self._graph

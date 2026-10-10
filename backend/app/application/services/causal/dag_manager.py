"""DAG management — create, validate, version, and suggest causal graphs."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import polars as pl

from app.application.dto.causal import DAGDTO, DAGEdgeDTO, DAGNodeDTO
from app.domain.entities.dag_version import DAGVersion
from app.domain.ports.causal_graph import GraphEdge, GraphNode
from app.domain.repositories.dag_version_repository import DAGVersionRepository
from app.domain.value_objects.causal import CausalVariableRole
from app.infrastructure.causal.networkx_graph import NetworkXCausalGraph
from app.shared.exceptions import BusinessValidationError
from app.shared.utils.datetime import utc_now


class DAGManager:
    """Manage causal DAG lifecycle with validation and versioning."""

    def build_graph(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> NetworkXCausalGraph:
        graph = NetworkXCausalGraph()
        for node in nodes:
            graph.add_node(
                GraphNode(
                    id=str(node["id"]),
                    label=str(node.get("label", node["id"])),
                    role=node.get("role"),
                )
            )
        for edge in edges:
            graph.add_edge(GraphEdge(source=str(edge["source"]), target=str(edge["target"])))
        return graph

    def validate(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> DAGDTO:
        graph = self.build_graph(nodes, edges)
        result = graph.validate()
        return DAGDTO(
            nodes=tuple(
                DAGNodeDTO(id=n["id"], label=n.get("label", n["id"]), role=n.get("role"))
                for n in nodes
            ),
            edges=tuple(DAGEdgeDTO(source=e["source"], target=e["target"]) for e in edges),
            is_valid=result.is_valid,
            validation_errors=result.errors,
        )

    def suggest_dag(
        self,
        *,
        frame: pl.DataFrame,
        treatment: str,
        outcome: str,
        variable_roles: dict[str, str],
    ) -> DAGDTO:
        """Experimental: suggest a simple DAG from variable roles and correlations."""
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        all_vars = [treatment, outcome] + [
            v for v, r in variable_roles.items()
            if v not in {treatment, outcome} and r != CausalVariableRole.UNKNOWN.value
        ]
        for var in dict.fromkeys(all_vars):
            if var in frame.columns:
                nodes.append({"id": var, "label": var, "role": variable_roles.get(var)})

        for var, role in variable_roles.items():
            if var in {treatment, outcome} or var not in frame.columns:
                continue
            if role in {CausalVariableRole.CONFOUNDER.value, CausalVariableRole.INSTRUMENT.value}:
                edges.append({"source": var, "target": treatment})
                edges.append({"source": var, "target": outcome})
            elif role == CausalVariableRole.MEDIATOR.value:
                edges.append({"source": treatment, "target": var})
                edges.append({"source": var, "target": outcome})

        if not any(e["source"] == treatment and e["target"] == outcome for e in edges):
            edges.append({"source": treatment, "target": outcome})

        return self.validate(nodes, edges)

    async def save_dag(
        self,
        *,
        repo: DAGVersionRepository,
        dataset_id: UUID,
        version_id: UUID,
        organization_id: UUID,
        project_id: UUID,
        created_by: UUID,
        name: str,
        description: str | None,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        variable_roles: dict[str, str],
        dag_id: UUID | None = None,
    ) -> DAGVersion:
        validation = self.validate(nodes, edges)
        if not validation.is_valid:
            raise BusinessValidationError(
                f"Invalid DAG: {'; '.join(validation.validation_errors)}",
                code="invalid_dag",
            )
        now = utc_now()
        version_number = await repo.next_version_number(dataset_id=dataset_id)

        if dag_id:
            existing = await repo.get_by_id(dag_id=dag_id, organization_id=organization_id)
            if existing is None:
                raise BusinessValidationError("DAG not found.")
            updated = DAGVersion(
                id=existing.id,
                dataset_id=dataset_id,
                version_id=version_id,
                organization_id=organization_id,
                project_id=project_id,
                created_by=created_by,
                name=name,
                description=description,
                nodes=tuple(nodes),
                edges=tuple(edges),
                variable_roles=variable_roles,
                version_number=existing.version_number,
                is_valid=True,
                validation_errors=(),
                created_at=existing.created_at,
                updated_at=now,
            )
            return await repo.update(updated)

        dag = DAGVersion(
            id=uuid4(),
            dataset_id=dataset_id,
            version_id=version_id,
            organization_id=organization_id,
            project_id=project_id,
            created_by=created_by,
            name=name,
            description=description,
            nodes=tuple(nodes),
            edges=tuple(edges),
            variable_roles=variable_roles,
            version_number=version_number,
            is_valid=True,
            validation_errors=(),
            created_at=now,
            updated_at=now,
        )
        return await repo.create(dag)

    def to_dag_dto(self, dag: DAGVersion) -> DAGDTO:
        return DAGDTO(
            nodes=tuple(
                DAGNodeDTO(id=n["id"], label=n.get("label", n["id"]), role=n.get("role"))
                for n in dag.nodes
            ),
            edges=tuple(DAGEdgeDTO(source=e["source"], target=e["target"]) for e in dag.edges),
            is_valid=dag.is_valid,
            validation_errors=dag.validation_errors,
        )

"""Causal graph port — stable abstraction over graph implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GraphNode:
    id: str
    label: str
    role: str | None = None


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str


@dataclass(frozen=True, slots=True)
class GraphValidationResult:
    is_valid: bool
    is_acyclic: bool
    errors: tuple[str, ...]


class CausalGraphPort(ABC):
    """Abstract causal DAG — implementations may use NetworkX or other libraries."""

    @abstractmethod
    def add_node(self, node: GraphNode) -> None: ...

    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> None: ...

    @abstractmethod
    def validate(self) -> GraphValidationResult: ...

    @abstractmethod
    def ancestors(self, node_id: str) -> frozenset[str]: ...

    @abstractmethod
    def descendants(self, node_id: str) -> frozenset[str]: ...

    @abstractmethod
    def parents(self, node_id: str) -> frozenset[str]: ...

    @abstractmethod
    def children(self, node_id: str) -> frozenset[str]: ...

    @abstractmethod
    def nodes(self) -> tuple[str, ...]: ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> CausalGraphPort: ...

"""Causal identification engine — backdoor criterion and adjustment sets."""

from __future__ import annotations

from itertools import combinations

from app.application.dto.causal import IdentificationReportDTO
from app.domain.ports.causal_graph import CausalGraphPort
from app.domain.value_objects.causal import IdentificationStrategy
from app.infrastructure.causal.networkx_graph import NetworkXCausalGraph


class IdentificationEngine:
    """Determine whether a causal effect is identifiable from the DAG."""

    def identify(
        self,
        *,
        graph: CausalGraphPort,
        treatment: str,
        outcome: str,
    ) -> IdentificationReportDTO:
        if treatment not in graph.nodes() or outcome not in graph.nodes():
            return IdentificationReportDTO(
                strategy=IdentificationStrategy.NOT_IDENTIFIED,
                identified=False,
                adjustment_set=(),
                reasoning="Treatment or outcome not present in the DAG.",
                required_assumptions=("Valid DAG specification",),
                limitations=("Add treatment and outcome to the DAG.",),
            )

        # Backdoor paths: paths from treatment to outcome that start with arrow into treatment
        backdoor_sets = self._find_backdoor_adjustment_sets(graph, treatment, outcome)
        if backdoor_sets:
            minimal = min(backdoor_sets, key=len)
            return IdentificationReportDTO(
                strategy=IdentificationStrategy.BACKDOOR,
                identified=True,
                adjustment_set=tuple(sorted(minimal)),
                reasoning=(
                    f"Backdoor criterion satisfied by adjusting for {', '.join(sorted(minimal))}. "
                    "This blocks all backdoor paths between treatment and outcome."
                ),
                required_assumptions=(
                    "Causal Markov condition",
                    "Faithfulness",
                    "No unmeasured confounders outside the DAG",
                    "Correct DAG structure",
                ),
                limitations=(
                    "Identification assumes the DAG is correct.",
                    "Unmeasured confounders invalidate backdoor adjustment.",
                ),
            )

        # Check for frontdoor path architecture (mediator between T and Y)
        mediators = graph.children(treatment) & graph.parents(outcome)
        if mediators:
            return IdentificationReportDTO(
                strategy=IdentificationStrategy.FRONTDOOR,
                identified=False,
                adjustment_set=tuple(sorted(mediators)),
                reasoning=(
                    f"Frontdoor paths may exist via {', '.join(mediators)}, but full frontdoor "
                    "identification requires additional assumptions not yet automated."
                ),
                required_assumptions=(
                    "No unblocked backdoor paths from treatment to mediator",
                    "Treatment affects outcome only through mediator",
                    "No confounders of mediator-outcome affecting treatment",
                ),
                limitations=("Frontdoor estimation is not yet fully implemented.",),
            )

        return IdentificationReportDTO(
            strategy=IdentificationStrategy.NOT_IDENTIFIED,
            identified=False,
            adjustment_set=(),
            reasoning=(
                "No valid backdoor adjustment set found. The causal effect may not be "
                "identifiable from observed data under this DAG."
            ),
            required_assumptions=("Valid DAG", "Sufficient covariates measured"),
            limitations=(
                "Consider instrumental variables or experimental data.",
                "Review DAG for colliders and mediators.",
            ),
        )

    def _find_backdoor_adjustment_sets(
        self, graph: CausalGraphPort, treatment: str, outcome: str
    ) -> list[frozenset[str]]:
        """Find adjustment sets satisfying the backdoor criterion."""
        if not isinstance(graph, NetworkXCausalGraph):
            graph = NetworkXCausalGraph.from_dict(graph.to_dict())

        nx_g = graph.nx_graph
        candidates = set(graph.nodes()) - {treatment, outcome}
        valid_sets: list[frozenset[str]] = []

        for size in range(len(candidates) + 1):
            for subset in combinations(candidates, size):
                z_set = frozenset(subset)
                if self._satisfies_backdoor(nx_g, treatment, outcome, z_set):
                    valid_sets.append(z_set)
        return valid_sets

    @staticmethod
    def _satisfies_backdoor(
        nx_g: object, treatment: str, outcome: str, z: frozenset[str]
    ) -> bool:
        """Check backdoor criterion via d-separation on the mutilated graph."""
        import networkx as nx

        g: nx.DiGraph = nx_g  # type: ignore[assignment]
        descendants = nx.descendants(g, treatment) if treatment in g else set()
        if z & descendants:
            return False

        g_mutilated = g.copy()
        g_mutilated.remove_edges_from(list(g_mutilated.out_edges(treatment)))

        try:
            return nx.is_d_separator(g_mutilated, {treatment}, {outcome}, z)
        except (nx.NodeNotFound, nx.NetworkXError):
            return False

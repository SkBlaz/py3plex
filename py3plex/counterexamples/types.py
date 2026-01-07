"""Data types for counterexample generation.

This module defines the core dataclasses used in counterexample generation:
- Claim: Represents a network invariant claim
- Violation: A specific violation of a claim
- Counterexample: The complete counterexample with witness subgraph
- Budget: Resource limits for minimization
- MinimizationReport: Stats from minimization process
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set, Tuple


@dataclass
class Budget:
    """Resource limits for counterexample generation.

    Attributes:
        max_tests: Maximum number of violation tests during minimization
        max_witness_size: Maximum nodes/edges in witness (enforced during extraction)
        timeout_seconds: Optional timeout for entire process
    """

    max_tests: int = 200
    max_witness_size: int = 500
    timeout_seconds: Optional[float] = None


@dataclass
class Claim:
    """Represents a network invariant claim.

    A claim is typically an implication: antecedent -> consequent
    For MVP: degree__ge(k) -> pagerank__rank_gt(r)

    Attributes:
        claim_str: Original claim string
        claim_hash: Stable hash of normalized claim
        antecedent: Callable that checks antecedent condition on a node
        consequent: Callable that checks consequent condition on a node + metrics
        params: Parameter bindings (e.g., {"k": 10, "r": 50})
        description: Human-readable description
    """

    claim_str: str
    claim_hash: str
    antecedent: Callable[[Any], bool]
    consequent: Callable[[Any, Dict[str, Any]], bool]
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self):
        """Set description from claim_str if not provided."""
        if not self.description:
            self.description = self.claim_str


@dataclass
class Violation:
    """Represents a specific violation of a claim.

    Attributes:
        node: Node identifier
        layer: Layer where violation occurs
        antecedent_values: Metric values that satisfy antecedent
        consequent_values: Metric values that violate consequent
        margin: How badly the consequent is violated (higher = worse)
    """

    node: Any
    layer: str
    antecedent_values: Dict[str, Any]
    consequent_values: Dict[str, Any]
    margin: float = 0.0


@dataclass
class MinimizationReport:
    """Report on minimization process.

    Attributes:
        is_minimal: Whether witness is provably minimal within budget
        tests_used: Number of violation tests performed
        max_tests: Budget limit
        initial_edges: Edge count before minimization
        final_edges: Edge count after minimization
        initial_nodes: Node count before minimization
        final_nodes: Node count after minimization
        strategy: Minimization strategy used (e.g., "ddmin_edges")
        time_ms: Time spent in minimization (milliseconds)
    """

    is_minimal: bool
    tests_used: int
    max_tests: int
    initial_edges: int
    final_edges: int
    initial_nodes: int
    final_nodes: int
    strategy: str = "ddmin_edges"
    time_ms: float = 0.0


@dataclass
class Counterexample:
    """Complete counterexample with witness subgraph and provenance.

    Attributes:
        subgraph: Witness subgraph (py3plex multi_layer_network)
        violation: The violation found
        witness_nodes: Set of (node, layer) tuples in witness
        witness_edges: Set of edge tuples in witness
        minimization: Report on minimization process
        meta: Metadata including provenance
    """

    subgraph: Any  # multi_layer_network object
    violation: Violation
    witness_nodes: Set[Tuple[Any, str]]
    witness_edges: Set[Tuple[Any, Any, str, str]]
    minimization: MinimizationReport
    meta: Dict[str, Any] = field(default_factory=dict)

    def explain(self) -> str:
        """Generate human-readable explanation of counterexample.

        Returns:
            Multi-line string explaining the counterexample
        """
        lines = []
        lines.append("=" * 70)
        lines.append("COUNTEREXAMPLE FOUND")
        lines.append("=" * 70)
        lines.append("")

        # Violation details
        lines.append(f"Violating Node: {self.violation.node}")
        lines.append(f"Layer: {self.violation.layer}")
        lines.append("")

        # Antecedent
        lines.append("Antecedent (satisfied):")
        for key, val in self.violation.antecedent_values.items():
            lines.append(f"  {key}: {val}")
        lines.append("")

        # Consequent
        lines.append("Consequent (violated):")
        for key, val in self.violation.consequent_values.items():
            lines.append(f"  {key}: {val}")
        lines.append(f"  violation_margin: {self.violation.margin:.4f}")
        lines.append("")

        # Witness stats
        lines.append("Witness subgraph:")
        lines.append(f"  nodes: {len(self.witness_nodes)}")
        lines.append(f"  edges: {len(self.witness_edges)}")
        lines.append("")

        # Minimization
        lines.append("Minimization:")
        lines.append(f"  is_minimal: {self.minimization.is_minimal}")
        lines.append(
            f"  tests_used: {self.minimization.tests_used} / {self.minimization.max_tests}"
        )
        lines.append(f"  strategy: {self.minimization.strategy}")
        lines.append(
            f"  reduction: {self.minimization.initial_edges} -> {self.minimization.final_edges} edges"
        )
        lines.append("")

        # Provenance
        if "provenance" in self.meta:
            prov = self.meta["provenance"]
            lines.append("Provenance:")
            lines.append(f"  engine: {prov.get('engine', 'unknown')}")
            lines.append(f"  seed: {prov.get('randomness', {}).get('seed', 'none')}")
            lines.append(f"  timestamp: {prov.get('timestamp_utc', 'unknown')}")

        lines.append("=" * 70)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert counterexample to JSON-serializable dictionary.

        Returns:
            Dictionary representation (without subgraph object)
        """
        return {
            "violation": {
                "node": str(self.violation.node),
                "layer": self.violation.layer,
                "antecedent_values": self.violation.antecedent_values,
                "consequent_values": self.violation.consequent_values,
                "margin": self.violation.margin,
            },
            "witness": {
                "nodes": len(self.witness_nodes),
                "edges": len(self.witness_edges),
            },
            "minimization": {
                "is_minimal": self.minimization.is_minimal,
                "tests_used": self.minimization.tests_used,
                "max_tests": self.minimization.max_tests,
                "initial_edges": self.minimization.initial_edges,
                "final_edges": self.minimization.final_edges,
                "initial_nodes": self.minimization.initial_nodes,
                "final_nodes": self.minimization.final_nodes,
                "strategy": self.minimization.strategy,
                "time_ms": self.minimization.time_ms,
            },
            "meta": self.meta,
        }

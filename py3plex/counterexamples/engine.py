"""Main counterexample generation engine.

This module orchestrates the counterexample generation process:
1. Find violation in full network
2. Extract witness subgraph
3. Minimize witness
4. Assemble Counterexample with provenance
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from py3plex.exceptions import AlgorithmError
from .types import Budget, Claim, Counterexample, MinimizationReport, Violation
from .claim_lang import parse_and_compile_claim
from .witness import ego_subgraph
from .ddmin import minimize_edges


class CounterexampleNotFound(AlgorithmError):
    """Exception raised when no counterexample exists.

    Error code: PX301
    """

    default_code = "PX301"


def find_counterexample(
    network: Any,
    claim_str: str,
    params: Dict[str, Any],
    layers: Optional[List[str]] = None,
    seed: int = 42,
    find_minimal: bool = True,
    budget: Optional[Budget] = None,
    initial_radius: int = 2,
) -> Optional[Counterexample]:
    """Find counterexample for a claim on a network.

    Args:
        network: py3plex multi_layer_network object
        claim_str: Claim string (e.g., "degree__ge(k) -> pagerank__rank_gt(r)")
        params: Parameter bindings (e.g., {"k": 10, "r": 50})
        layers: Layers to consider (None = all layers)
        seed: Random seed for determinism
        find_minimal: Whether to minimize witness
        budget: Resource limits (defaults to Budget())
        initial_radius: Radius for ego subgraph extraction (default: 2)

    Returns:
        Counterexample object if found, None otherwise

    Raises:
        CounterexampleNotFound: If no violation exists
    """
    start_time = time.time()

    if budget is None:
        budget = Budget()

    # Parse claim
    claim = parse_and_compile_claim(claim_str, params)

    # Stage 1: Find violation
    t0 = time.time()
    violation = find_violation(network, claim, layers, seed)
    find_time = (time.time() - t0) * 1000

    if violation is None:
        raise CounterexampleNotFound(
            f"No violation found for claim: {claim_str}",
            context={"params": params, "layers": layers},
        )

    # Stage 2: Extract witness
    t0 = time.time()
    witness = build_witness(
        network, violation, initial_radius, layers, budget.max_witness_size
    )
    extract_time = (time.time() - t0) * 1000

    # Stage 3: Minimize witness
    minimize_time = 0.0
    minimization_report = None

    if find_minimal:
        t0 = time.time()
        witness, minimization_report = minimize_witness(
            witness, violation, claim, budget.max_tests, seed
        )
        minimize_time = (time.time() - t0) * 1000
    else:
        # No minimization
        initial_edges = len(list(witness.get_edges()))
        initial_nodes = len(list(witness.get_nodes()))
        minimization_report = MinimizationReport(
            is_minimal=False,
            tests_used=0,
            max_tests=budget.max_tests,
            initial_edges=initial_edges,
            final_edges=initial_edges,
            initial_nodes=initial_nodes,
            final_nodes=initial_nodes,
            strategy="none",
            time_ms=0.0,
        )

    # Collect witness nodes and edges
    witness_nodes = set()
    for node in witness.get_nodes():
        witness_nodes.add((node[0], node[1]))

    witness_edges = set()
    for edge in witness.get_edges():
        # Parse edge format: ((src, src_layer), (tgt, tgt_layer))
        src_tuple = edge[0]
        tgt_tuple = edge[1]
        witness_edges.add((src_tuple[0], tgt_tuple[0], src_tuple[1], tgt_tuple[1]))

    # Build provenance
    total_time = (time.time() - start_time) * 1000
    provenance = _build_provenance(
        network,
        claim,
        seed,
        find_time,
        extract_time,
        minimize_time,
        total_time,
        minimization_report,
        budget,
    )

    # Assemble Counterexample
    cex = Counterexample(
        subgraph=witness,
        violation=violation,
        witness_nodes=witness_nodes,
        witness_edges=witness_edges,
        minimization=minimization_report,
        meta={"provenance": provenance},
    )

    return cex


def find_violation(
    network: Any, claim: Claim, layers: Optional[List[str]], seed: int
) -> Optional[Violation]:
    """Find a violating node in the network.

    Args:
        network: py3plex multi_layer_network object
        claim: Parsed claim object
        layers: Layers to consider (None = all)
        seed: Random seed for tie-breaking

    Returns:
        Violation object if found, None otherwise
    """
    from py3plex.dsl import Q

    # Determine layers to search
    if layers is None:
        # Use all layers
        search_layers = [str(layer) for layer in network.layers]
    else:
        search_layers = layers

    # Build DSL query to compute needed metrics
    # For MVP: antecedent uses "degree" (cheap), consequent uses computed metric

    # Extract metric names from claim
    # For now, we'll use a simple approach: compute degree + compute consequent metric

    # Parse claim to identify metrics
    # Antecedent: typically "degree"
    # Consequent: typically "pagerank" or "betweenness_centrality"

    antecedent_metric = _extract_antecedent_metric(claim.claim_str)
    consequent_metric = _extract_consequent_metric(claim.claim_str)

    # Query nodes with metrics
    query = Q.nodes()
    if layers is not None:
        from py3plex.dsl import L

        layer_expr = None
        for layer in layers:
            if layer_expr is None:
                layer_expr = L[layer]
            else:
                layer_expr = layer_expr + L[layer]
        query = query.from_layers(layer_expr)

    # Compute consequent metric
    query = query.compute(consequent_metric)

    result = query.execute(network)

    # Convert to list of node records
    nodes_data = result.to_pandas().to_dict("records")

    # Add degree if not present
    for record in nodes_data:
        if "degree" not in record and antecedent_metric == "degree":
            # Compute degree for this node
            node = record.get(
                "id", record.get("node")
            )  # Handle both 'id' and 'node' columns
            layer = record["layer"]
            degree = _compute_degree(network, node, layer)
            record["degree"] = degree

    # Add ranks for consequent metric
    is_rank_based = "_rank_" in claim.claim_str
    if is_rank_based:
        _add_ranks(nodes_data, consequent_metric)

    # Find violating nodes
    violating_nodes = []
    for record in nodes_data:
        # Check antecedent
        if not claim.antecedent(record):
            continue

        # Check consequent (negated - we want violations)
        if not claim.consequent(record, {}):
            # This is a violation
            violating_nodes.append(record)

    if not violating_nodes:
        return None

    # Select best violating node (deterministic)
    # Heuristic: highest antecedent margin, worst consequent margin
    best = _select_best_violation(
        violating_nodes, antecedent_metric, consequent_metric, is_rank_based, seed
    )

    # Extract node identifier (handle both 'id' and 'node' columns)
    node_id = best.get("id", best.get("node"))

    # Build Violation object
    violation = Violation(
        node=node_id,
        layer=best["layer"],
        antecedent_values={antecedent_metric: best.get(antecedent_metric, 0)},
        consequent_values={consequent_metric: best.get(consequent_metric, 0)},
        margin=best.get("margin", 0.0),
    )

    return violation


def build_witness(
    network: Any,
    violation: Violation,
    radius: int,
    layers: Optional[List[str]],
    max_size: int,
) -> Any:
    """Extract witness subgraph around violation.

    Args:
        network: py3plex multi_layer_network object
        violation: Violation object
        radius: Ego subgraph radius
        layers: Layers to include
        max_size: Maximum witness size (nodes)

    Returns:
        Witness subgraph
    """
    return ego_subgraph(
        network,
        violation.node,
        violation.layer,
        radius=radius,
        layers=layers,
        max_nodes=max_size,
        strategy="top_neighbors",
    )


def minimize_witness(
    witness: Any, violation: Violation, claim: Claim, max_tests: int, seed: int
) -> Tuple[Any, MinimizationReport]:
    """Minimize witness subgraph using ddmin.

    Args:
        witness: Witness subgraph
        violation: Original violation
        claim: Claim object
        max_tests: Maximum violation tests
        seed: Random seed

    Returns:
        Tuple of (minimized_witness, MinimizationReport)
    """
    initial_edges = len(list(witness.get_edges()))
    initial_nodes = len(list(witness.get_nodes()))

    # Build violation tester
    def violation_tester(candidate: Any) -> bool:
        """Check if candidate still violates claim."""
        # Re-run find_violation on candidate
        cand_violation = find_violation(candidate, claim, None, seed)
        return cand_violation is not None

    # Minimize edges
    minimized, tests_used, is_minimal = minimize_edges(
        witness, violation_tester, max_tests, seed
    )

    final_edges = len(list(minimized.get_edges()))
    final_nodes = len(list(minimized.get_nodes()))

    report = MinimizationReport(
        is_minimal=is_minimal,
        tests_used=tests_used,
        max_tests=max_tests,
        initial_edges=initial_edges,
        final_edges=final_edges,
        initial_nodes=initial_nodes,
        final_nodes=final_nodes,
        strategy="ddmin_edges",
        time_ms=0.0,  # Filled by caller
    )

    return minimized, report


def _extract_antecedent_metric(claim_str: str) -> str:
    """Extract antecedent metric name from claim string."""
    import re

    match = re.match(r"(\w+)__", claim_str)
    if match:
        return match.group(1)
    return "degree"


def _extract_consequent_metric(claim_str: str) -> str:
    """Extract consequent metric name from claim string."""
    import re

    parts = claim_str.split("->")
    if len(parts) == 2:
        consequent = parts[1].strip()
        match = re.match(r"(\w+)__", consequent)
        if match:
            return match.group(1)
    return "pagerank"


def _compute_degree(network: Any, node: Any, layer: str) -> int:
    """Compute degree of a node in a specific layer."""
    degree = 0
    for edge in network.get_edges():
        # Edge format: ((src, src_layer), (tgt, tgt_layer)) or extended
        if len(edge) >= 2:
            src_tuple = edge[0]
            tgt_tuple = edge[1]

            if isinstance(src_tuple, tuple) and len(src_tuple) >= 2:
                src = src_tuple[0]
                src_layer = src_tuple[1]
            else:
                # Fallback for different format
                src = src_tuple
                src_layer = layer

            if isinstance(tgt_tuple, tuple) and len(tgt_tuple) >= 2:
                tgt = tgt_tuple[0]
                tgt_layer = tgt_tuple[1]
            else:
                tgt = tgt_tuple
                tgt_layer = layer

            if src == node and src_layer == layer:
                degree += 1
            elif not network.directed and tgt == node and tgt_layer == layer:
                degree += 1

    return degree


def _add_ranks(nodes_data: List[Dict], metric: str) -> None:
    """Add rank column for a metric (in-place).

    Args:
        nodes_data: List of node records
        metric: Metric name to rank
    """

    # Get node id helper
    def get_node_id(record):
        return str(record.get("id", record.get("node", "")))

    # Sort by metric descending, then by (node, layer) for determinism
    sorted_nodes = sorted(
        nodes_data, key=lambda x: (-x.get(metric, 0), get_node_id(x), x["layer"])
    )

    # Assign ranks (1-indexed)
    for i, record in enumerate(sorted_nodes):
        record[f"{metric}_rank"] = i + 1


def _select_best_violation(
    violating_nodes: List[Dict],
    antecedent_metric: str,
    consequent_metric: str,
    is_rank_based: bool,
    seed: int,
) -> Dict:
    """Select best violating node deterministically.

    Heuristic: highest antecedent value, worst consequent violation
    """
    # Compute margins
    for record in violating_nodes:
        # Antecedent margin: how much it exceeds threshold (higher = better)
        # Consequent margin: how much it violates (higher = worse)
        # For now, use simple heuristic
        record["margin"] = record.get(antecedent_metric, 0)

    # Get node id (handle both 'id' and 'node')
    def get_node_id(record):
        return str(record.get("id", record.get("node", "")))

    # Sort by margin descending, then by (node, layer)
    sorted_violations = sorted(
        violating_nodes, key=lambda x: (-x["margin"], get_node_id(x), x["layer"])
    )

    return sorted_violations[0]


def _build_provenance(
    network: Any,
    claim: Claim,
    seed: int,
    find_time: float,
    extract_time: float,
    minimize_time: float,
    total_time: float,
    minimization_report: MinimizationReport,
    budget: Budget,
) -> Dict[str, Any]:
    """Build provenance record."""
    from py3plex.dsl.provenance import get_py3plex_version, network_fingerprint

    return {
        "engine": "counterexample_engine",
        "py3plex_version": get_py3plex_version(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "claim": {
            "claim_str": claim.claim_str,
            "claim_hash": claim.claim_hash,
            "params": claim.params,
        },
        "randomness": {
            "seed": seed,
        },
        "network_fingerprint": network_fingerprint(network),
        "performance": {
            "find_violation_ms": find_time,
            "extract_witness_ms": extract_time,
            "minimize_ms": minimize_time,
            "total_ms": total_time,
        },
        "minimization": {
            "max_tests": minimization_report.max_tests,
            "tests_used": minimization_report.tests_used,
            "is_minimal": minimization_report.is_minimal,
            "strategy": minimization_report.strategy,
            "final_size": {
                "nodes": minimization_report.final_nodes,
                "edges": minimization_report.final_edges,
            },
        },
        "budget": {
            "max_tests": budget.max_tests,
            "max_witness_size": budget.max_witness_size,
        },
    }

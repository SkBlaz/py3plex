"""Simulation executor for dynamics module.

This module provides the execution engine that runs simulations on
multilayer networks.
"""

from typing import Any, Dict, List, Set, Tuple

import numpy as np

from .ast import SimulationStmt, InitialSpec
from .result import SimulationResult
from .processes import get_process, ProcessSpec
from .registry import measure_registry
from .errors import (
    MissingInitialConditionError,
    SimulationConfigError,
    UnknownMeasureError,
)


def run_simulation(network: Any, stmt: SimulationStmt,
                   backend: str = "numpy") -> SimulationResult:
    """Execute a simulation on a multilayer network.

    Pipeline:
    1. Layer resolution - evaluate layer_expr to get active layers
    2. Network projection - extract subgraph over selected layers
    3. Initialization - set up initial state from InitialSpec
    4. Backend & update function - create update step function
    5. Replicate loop - run simulation for each replicate
    6. Collect results - build SimulationResult

    Args:
        network: Multilayer network object
        stmt: SimulationStmt specification
        backend: Backend to use ("numpy" currently supported)

    Returns:
        SimulationResult with collected measures

    Raises:
        DynamicsError: For various simulation errors
    """
    # Validate configuration
    if stmt.steps < 1:
        raise SimulationConfigError("steps", f"Must be >= 1, got {stmt.steps}")
    if stmt.replicates < 1:
        raise SimulationConfigError("replicates", f"Must be >= 1, got {stmt.replicates}")

    # Get process specification
    process_spec = get_process(stmt.process_name)

    # Merge parameters (stmt params override process defaults)
    params = {**process_spec.params, **stmt.params}

    # Validate required initial conditions
    for key in process_spec.required_initial:
        if key not in stmt.initial:
            raise MissingInitialConditionError(key, process_spec.required_initial)

    # Validate measures
    for measure in stmt.measures:
        if not measure_registry.has(process_spec.name, measure):
            known = measure_registry.list_measures(process_spec.name)
            raise UnknownMeasureError(measure, known, process_spec.name)

    # Step 1 & 2: Layer resolution and network projection
    nodes, adj_matrix, node_to_idx, layer_info = _prepare_network(
        network, stmt.layer_expr
    )

    if len(nodes) == 0:
        # Empty network
        return SimulationResult(
            process_name=process_spec.name,
            measures=stmt.measures,
            data={m: np.array([]) for m in stmt.measures},
            meta={"steps": stmt.steps, "replicates": stmt.replicates, "warning": "Empty network"}
        )

    # Step 3: Create update function
    update_step = process_spec.update_fn(params, stmt.coupling)

    # Step 4: Initialize RNG
    base_seed = stmt.seed if stmt.seed is not None else 42

    # Step 5: Run replicates
    all_results: Dict[str, List[np.ndarray]] = {m: [] for m in stmt.measures}

    for rep in range(stmt.replicates):
        # Create RNG for this replicate
        rng = np.random.default_rng(base_seed + rep)

        # Initialize state
        state = _initialize_state(
            process_spec, stmt.initial, nodes, node_to_idx,
            layer_info, network, rng
        )

        # Storage for this replicate's measures
        rep_results: Dict[str, List[Any]] = {m: [] for m in stmt.measures}

        # Context for measure functions
        ctx: Dict[str, Any] = {
            "layer_info": _get_layer_indices(layer_info, node_to_idx),
            "prev_state": None,
            "params": params,
            "step": 0,
        }

        # Run simulation steps
        for t in range(stmt.steps):
            ctx["step"] = t

            # Record measures at current state
            for measure in stmt.measures:
                measure_fn = measure_registry.get(process_spec.name, measure)
                value = measure_fn(state, ctx)
                rep_results[measure].append(value)

            # Store previous state for incidence calculations
            ctx["prev_state"] = state.copy()

            # Update state
            state = update_step(adj_matrix, state, rng, node_to_idx, layer_info)

        # Store replicate results
        for measure in stmt.measures:
            all_results[measure].append(np.array(rep_results[measure]))

    # Step 6: Collect results
    data = {}
    for measure in stmt.measures:
        if all_results[measure]:
            data[measure] = np.array(all_results[measure])
        else:
            data[measure] = np.array([])

    meta = {
        "steps": stmt.steps,
        "replicates": stmt.replicates,
        "params": params,
        "coupling": stmt.coupling,
        "seed": base_seed,
        "network_nodes": len(nodes),
    }

    return SimulationResult(
        process_name=process_spec.name,
        measures=stmt.measures,
        data=data,
        meta=meta
    )


def _prepare_network(network: Any, layer_expr: Any) -> Tuple[
    List[Any], np.ndarray, Dict[Any, int], Dict[str, List[Any]]
]:
    """Prepare network data for simulation.

    Args:
        network: Multilayer network object
        layer_expr: Layer expression for filtering (optional)

    Returns:
        Tuple of (nodes, adj_matrix, node_to_idx, layer_info)
    """
    # Get core network
    if not hasattr(network, 'core_network') or network.core_network is None:
        return [], np.array([[]]), {}, {}

    G = network.core_network

    # Get all nodes
    nodes = list(G.nodes())

    # Filter by layers if layer_expr is provided
    if layer_expr is not None:
        active_layers = _evaluate_layer_expr(layer_expr, network)
        nodes = [n for n in nodes if isinstance(n, tuple) and len(n) >= 2 and n[1] in active_layers]

    if len(nodes) == 0:
        return [], np.array([[]]), {}, {}

    # Build node to index mapping
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    # Build adjacency matrix
    n = len(nodes)
    adj_matrix = np.zeros((n, n))

    for u, v in G.edges():
        if u in node_to_idx and v in node_to_idx:
            i, j = node_to_idx[u], node_to_idx[v]
            adj_matrix[i, j] = 1
            adj_matrix[j, i] = 1  # Undirected

    # Build layer info
    layer_info: Dict[str, List[Any]] = {}
    for node in nodes:
        if isinstance(node, tuple) and len(node) >= 2:
            layer = node[1]
            layer_info.setdefault(str(layer), []).append(node)

    return nodes, adj_matrix, node_to_idx, layer_info


def _evaluate_layer_expr(layer_expr: Any, network: Any) -> Set[str]:
    """Evaluate a layer expression to get active layers.

    Args:
        layer_expr: LayerExpr from DSL AST
        network: Multilayer network

    Returns:
        Set of active layer names
    """
    if layer_expr is None:
        return set()

    # Handle LayerExpr from AST
    if hasattr(layer_expr, 'terms') and hasattr(layer_expr, 'ops'):
        if not layer_expr.terms:
            return set()

        result = {layer_expr.terms[0].name}

        for i, op in enumerate(layer_expr.ops):
            next_term = layer_expr.terms[i + 1].name

            if op == "+":
                result.add(next_term)
            elif op == "-":
                result.discard(next_term)
            elif op == "&":
                if next_term in result:
                    result = {next_term}
                else:
                    result = set()

        return result

    return set()


def _get_layer_indices(layer_info: Dict[str, List[Any]],
                       node_to_idx: Dict[Any, int]) -> Dict[str, np.ndarray]:
    """Convert layer_info to indices for measure computation.

    Args:
        layer_info: Dictionary mapping layer names to node lists
        node_to_idx: Node to index mapping

    Returns:
        Dictionary mapping layer names to index arrays
    """
    result = {}
    for layer, nodes in layer_info.items():
        indices = [node_to_idx[n] for n in nodes if n in node_to_idx]
        result[layer] = np.array(indices, dtype=int)
    return result


def _initialize_state(process_spec: ProcessSpec,
                      initial: Dict[str, InitialSpec],
                      nodes: List[Any],
                      node_to_idx: Dict[Any, int],
                      layer_info: Dict[str, List[Any]],
                      network: Any,
                      rng: np.random.Generator) -> np.ndarray:
    """Initialize simulation state from InitialSpec.

    Args:
        process_spec: Process specification
        initial: Initial conditions mapping
        nodes: List of nodes
        node_to_idx: Node to index mapping
        layer_info: Layer information
        network: Multilayer network
        rng: Random number generator

    Returns:
        Initial state array
    """
    n = len(nodes)

    if process_spec.name in ("SIS", "SIR"):
        # Epidemic models: 0=S, 1=I, (2=R for SIR)
        state = np.zeros(n, dtype=int)

        if "infected" in initial:
            infected_spec = initial["infected"]

            if infected_spec.constant is not None:
                if isinstance(infected_spec.constant, float) and 0 <= infected_spec.constant <= 1:
                    # Fraction of nodes to infect
                    fraction = infected_spec.constant
                    n_infected = int(fraction * n)
                    # Preserve the "at least one" behavior for small positive fractions,
                    # but allow an explicit 0.0 to mean "infect nobody".
                    if fraction > 0 and n_infected == 0 and n > 0:
                        n_infected = 1
                    if n_infected > 0:
                        infected_indices = rng.choice(
                            n, size=min(n_infected, n), replace=False
                        )
                        state[infected_indices] = 1
                elif isinstance(infected_spec.constant, int):
                    # Specific number of nodes
                    n_infected = min(infected_spec.constant, n)
                    infected_indices = rng.choice(n, size=n_infected, replace=False)
                    state[infected_indices] = 1
                else:
                    # Try to find node by name
                    for node, idx in node_to_idx.items():
                        if isinstance(node, tuple) and node[0] == infected_spec.constant:
                            state[idx] = 1
                            break

            elif infected_spec.query is not None:
                # Execute query to get initial infected nodes
                from py3plex.dsl import execute_ast
                from py3plex.dsl.ast import Query

                query = Query(explain=False, select=infected_spec.query)
                result = execute_ast(network, query)

                for node in result.items:
                    if node in node_to_idx:
                        state[node_to_idx[node]] = 1

        return state

    elif process_spec.name == "RANDOM_WALK":
        # Random walk: 0=absent, 1=present (only one node has 1)
        state = np.zeros(n, dtype=int)

        if "start_node" in initial:
            start_spec = initial["start_node"]

            if start_spec.constant is not None:
                # Find node by name
                for node, idx in node_to_idx.items():
                    if isinstance(node, tuple) and node[0] == start_spec.constant:
                        state[idx] = 1
                        break
                else:
                    # Node not found, start at random
                    state[rng.integers(0, n)] = 1
            else:
                # Random start
                state[rng.integers(0, n)] = 1
        else:
            # Default to random start
            state[rng.integers(0, n)] = 1

        return state

    else:
        # Default: all zeros
        return np.zeros(n, dtype=int)

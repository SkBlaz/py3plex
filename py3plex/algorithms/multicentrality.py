"""
Multiplex Participation Coefficient (MPC) for multiplex networks.

This module implements the Multiplex Participation Coefficient metric for
multiplex networks (networks with identical node sets across all layers).

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict

# Optional formal verification support
try:
    from icontract import ensure, require

    ICONTRACT_AVAILABLE = True
except ImportError:
    # Create no-op decorators when icontract is not available
    def require(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def ensure(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    ICONTRACT_AVAILABLE = False


@require(lambda multinet: multinet is not None, "multinet must not be None")
@require(lambda normalized: isinstance(normalized, bool), "normalized must be a bool")
@require(
    lambda check_multiplex: isinstance(check_multiplex, bool),
    "check_multiplex must be a bool",
)
@ensure(lambda result: isinstance(result, dict), "result must be a dictionary")
@ensure(
    lambda result: all(isinstance(v, (int, float)) for v in result.values()),
    "all result values must be numeric",
)
def multiplex_participation_coefficient(
    multinet: Any, normalized: bool = True, check_multiplex: bool = True
) -> Dict[Any, float]:
    """
    Compute the Multiplex Participation Coefficient (MPC) for multiplex networks.
    MPC measures how evenly a node participates across layers.

    Parameters
    ----------
    multinet : py3plex.core.multinet.multi_layer_network
        Multiplex network object (same node set across layers).
    normalized : bool, optional
        Whether to normalize MPC to [0,1]. Default: True.
    check_multiplex : bool, optional
        Validate that all layers share the same node set.

    Returns
    -------
    dict
        Node → MPC value mapping.

    Notes
    -----
    The MPC is computed as:
        MPC(i) = 1 - sum_α (k_i^α / k_i^total)^2

    Where:
    - k_i^α is the degree of node i in layer α
    - k_i^total is the total degree of node i across all layers

    When normalized=True, the result is multiplied by L/(L-1) to normalize
    to [0,1] range, where L is the number of layers.

    References
    ----------
    - Battiston, F., et al. (2014). "Structural measures for multiplex networks."
      Physical Review E, 89(3), 032804.
    - De Domenico, M., et al. (2015). "Identifying modular flows on multilayer networks
      reveals highly overlapping organization in interconnected systems."
      Physical Review X, 5(1), 011027.
    - Harooni, M., et al. (2025). "Centrality in Multilayer Networks: Accurate
      Measurements with MultiNetPy." The Journal of Supercomputing, 81(1), 92.
      DOI: 10.1007/s11227-025-07197-8

    Contracts:
        - Precondition: multinet must not be None
        - Precondition: normalized and check_multiplex must be booleans
        - Postcondition: returns a dictionary with numeric values
    """

    # Get layers from the multiplex network
    multinet.split_to_layers(style="none", convert_to_simple=True)
    layers = multinet.layer_names
    layer_graphs = multinet.separate_layers

    L = len(layers)

    if L < 2:
        raise ValueError("Multiplex network must have at least 2 layers.")

    # Extract node sets from each layer
    # Nodes are stored as tuples (node_id, layer_id), we need just node_id
    layer_node_sets = []
    for layer_graph in layer_graphs:
        # Extract just the node IDs (first element of tuple)
        node_set = set()
        for node in layer_graph.nodes():
            if isinstance(node, tuple):
                node_set.add(node[0])
            else:
                node_set.add(node)
        layer_node_sets.append(node_set)

    # Ensure identical node set across layers (true multiplex assumption)
    if check_multiplex:
        base_nodes = layer_node_sets[0]
        for i, node_set in enumerate(layer_node_sets[1:], 1):
            if node_set != base_nodes:
                raise ValueError(
                    f"Non-multiplex structure detected: layer {layers[0]} has nodes {base_nodes} "
                    f"but layer {layers[i]} has nodes {node_set}. "
                    f"Layers have distinct node sets."
                )

    # Get all unique nodes
    all_nodes = layer_node_sets[0]

    # Compute degrees for each layer
    degrees = {}
    for i, (layer_name, layer_graph) in enumerate(zip(layers, layer_graphs)):
        layer_degrees = {}
        for node, degree in layer_graph.degree():
            # Extract node ID from tuple
            if isinstance(node, tuple):
                node_id = node[0]
            else:
                node_id = node
            layer_degrees[node_id] = degree
        degrees[layer_name] = layer_degrees

    # Compute MPC for each node
    mpc = {}

    for node in all_nodes:
        # Calculate total degree across all layers
        k_total = sum(degrees[layer].get(node, 0) for layer in layers)

        if k_total == 0:
            # Isolated node has MPC = 0
            mpc[node] = 0.0
            continue

        # Calculate participation probabilities
        p = [degrees[layer].get(node, 0) / k_total for layer in layers]

        # Calculate MPC: 1 - sum of squared probabilities
        val = 1 - sum(pi**2 for pi in p)

        # Normalize to [0,1] if requested
        if normalized:
            val *= L / (L - 1)

        mpc[node] = val

    return mpc

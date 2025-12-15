"""
Multilayer Clustering Coefficients
====================================

This module implements clustering coefficients for multilayer networks,
extending the classical clustering coefficient concept to networks with
multiple layers.

Mathematical Definitions
------------------------

Throughout, let V be the set of physical nodes and L the set of layers.
Let N_{v,ℓ} be the neighbor set of node v within layer ℓ.
Let k_{v,ℓ} = |N_{v,ℓ}|.

Define the set of node-layer "state nodes":
    V_M = {(v,ℓ) | v ∈ V, ℓ ∈ L, v appears in layer ℓ}

Define an undirected edge existence predicate:
    E_ℓ(x,y) = 1 if there is an intralayer edge between x and y in layer ℓ
    E_M((v,α),(w,β)) = 1 if there is an edge between state nodes in the 
                       multilayer representation

Variant A - Intra-layer local clustering (per node per layer)
--------------------------------------------------------------
For each node-layer (v,ℓ), define:

    C^{intra}_{v,ℓ} = 2 T_{v,ℓ} / (k_{v,ℓ}(k_{v,ℓ}-1))  if k_{v,ℓ} ≥ 2
                    = 0                                  otherwise

where T_{v,ℓ} = |{{x,y} ⊂ N_{v,ℓ} : E_ℓ(x,y)=1}|

Variant B - Aggregated multiplex local clustering (node-level, across layers)
-----------------------------------------------------------------------------
Define the aggregated neighbor set across selected layers:

    N_v^(𝓛) = ⋃_{ℓ∈𝓛} N_{v,ℓ}
    k_v^(𝓛) = |N_v^(𝓛)|

Define the number of "closed" neighbor pairs (triangles centered at v):

    T_v^(𝓛) = |{{x,y} ⊂ N_v^(𝓛) : ∃α,β∈𝓛 s.t. E_α(v,x)=1, E_β(v,y)=1, 
                                  ∃γ∈𝓛 s.t. E_γ(x,y)=1}|

Then the aggregated multiplex clustering is:

    C_v^{multiplex} = 2 T_v^(𝓛) / (k_v^(𝓛)(k_v^(𝓛)-1))  if k_v^(𝓛) ≥ 2
                    = 0                                    otherwise

Variant D - Supra-adjacency clustering
---------------------------------------
Construct a supra-adjacency matrix A on state nodes V_M. For undirected graphs,
triangles incident to state node i are:

    t_i = (A³)_{ii} / 2

    C_i^{supra} = 2 t_i / (d_i(d_i-1))  if d_i ≥ 2
                = 0                      otherwise

where d_i is the degree of state node i in the supra-adjacency matrix.

References
----------
.. [1] Battiston et al. (2014). "Structural measures for multiplex networks"
.. [2] Cozzo et al. (2015). "Clustering coefficients in multiplex networks"
"""

from typing import Dict, List, Optional, Set, Tuple, Union
import numpy as np
from scipy.sparse import csr_matrix, lil_matrix

from py3plex.core.multinet import multi_layer_network


def multilayer_clustering(
    network: multi_layer_network,
    coefficient: str = "multiplex",
    mode: str = "local",
    layers: Optional[List[str]] = None,
    include_cross_layer: bool = True,
    normalized: bool = True,
) -> Union[Dict[Tuple, float], float]:
    """
    Compute clustering coefficients for multilayer networks.

    Parameters
    ----------
    network : multi_layer_network
        py3plex multilayer network object.
    coefficient : str, optional
        One of {"intra", "multiplex", "supra"}. Default is "multiplex".
    mode : str, optional
        {"local", "global"}. Default is "local".
    layers : list or None, optional
        Subset of layers to consider. If None, use all layers.
    include_cross_layer : bool, optional
        If True, allow inter-layer edges to participate in triangle closure
        (where applicable). Default is True.
    normalized : bool, optional
        If True, return values normalized to [0, 1]. If False, also expose
        raw counts via internal helpers. Default is True.

    Returns
    -------
    dict or float
        Local mode:
            - For "intra" and "supra": dict mapping (node, layer) -> coefficient
            - For "multiplex": dict mapping (node, None) -> coefficient
        Global mode:
            - float (average of local coefficients)

    Raises
    ------
    ValueError
        If coefficient type is invalid or layers are empty/invalid.

    Examples
    --------
    >>> from py3plex.core import multinet
    >>> net = multinet.multi_layer_network()
    >>> net.add_edges([
    ...     {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
    ...     {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
    ...     {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
    ... ])
    >>> cintra = multilayer_clustering(net, coefficient="intra", mode="local")
    >>> cmux = multilayer_clustering(net, coefficient="multiplex", mode="local")
    >>> cg = multilayer_clustering(net, coefficient="multiplex", mode="global")
    """
    # Validate inputs
    if coefficient not in {"intra", "multiplex", "supra"}:
        raise ValueError(
            f"Invalid coefficient type: {coefficient}. "
            "Must be one of: 'intra', 'multiplex', 'supra'"
        )
    
    if mode not in {"local", "global"}:
        raise ValueError(
            f"Invalid mode: {mode}. Must be one of: 'local', 'global'"
        )
    
    # Check if network is empty
    if network.core_network is None or network.core_network.number_of_nodes() == 0:
        raise ValueError("No layers specified or available in network")
    
    # Get all available layers if not specified
    if layers is None:
        all_layers, _, _ = network.get_layers()
        layers = list(all_layers)
    
    if not layers:
        raise ValueError("No layers specified or available in network")
    
    # Validate that specified layers exist
    all_layers, _, _ = network.get_layers()
    all_layers = set(all_layers)
    invalid_layers = set(layers) - all_layers
    if invalid_layers:
        raise ValueError(f"Invalid layers: {invalid_layers}")
    
    # Build adjacency structures
    layer_adjacency = _build_layer_adjacency(network, layers)
    
    # Compute clustering based on coefficient type
    if coefficient == "intra":
        local_coeffs = _compute_intra_clustering(layer_adjacency, layers)
    elif coefficient == "multiplex":
        local_coeffs = _compute_multiplex_clustering(
            layer_adjacency, layers, network
        )
    elif coefficient == "supra":
        local_coeffs = _compute_supra_clustering(
            network, layers, include_cross_layer
        )
    else:
        raise ValueError(f"Unknown coefficient type: {coefficient}")
    
    # Return based on mode
    if mode == "local":
        return local_coeffs
    elif mode == "global":
        if not local_coeffs:
            return 0.0
        return sum(local_coeffs.values()) / len(local_coeffs)
    else:
        raise ValueError(f"Unknown mode: {mode}")


def _build_layer_adjacency(
    network: multi_layer_network, layers: List[str]
) -> Dict[str, Dict[str, Set[str]]]:
    """
    Build adjacency indices keyed by layer for intralayer edges.

    Parameters
    ----------
    network : multi_layer_network
        The multilayer network.
    layers : list of str
        Layers to include.

    Returns
    -------
    dict
        Mapping: layer -> node -> set of neighbor nodes
        Example: {'L1': {'A': {'B', 'C'}, 'B': {'A', 'C'}, 'C': {'A', 'B'}}}
    """
    layer_adjacency = {layer: {} for layer in layers}
    
    # Iterate through edges in the core network
    for u, v, data in network.core_network.edges(data=True):
        # u and v are tuples (node_id, layer)
        node_u, layer_u = u
        node_v, layer_v = v
        
        # Only consider intralayer edges within specified layers
        if layer_u == layer_v and layer_u in layers:
            # Add to adjacency for this layer
            if node_u not in layer_adjacency[layer_u]:
                layer_adjacency[layer_u][node_u] = set()
            if node_v not in layer_adjacency[layer_u]:
                layer_adjacency[layer_u][node_v] = set()
            
            layer_adjacency[layer_u][node_u].add(node_v)
            layer_adjacency[layer_u][node_v].add(node_u)
    
    return layer_adjacency


def _build_state_node_index(
    network: multi_layer_network, layers: List[str]
) -> Tuple[List[Tuple[str, str]], Dict[Tuple[str, str], int]]:
    """
    Build state node index for supra-adjacency matrix construction.

    Parameters
    ----------
    network : multi_layer_network
        The multilayer network.
    layers : list of str
        Layers to include.

    Returns
    -------
    tuple
        (state_nodes, state_node_to_idx)
        - state_nodes: List of (node, layer) tuples in stable order
        - state_node_to_idx: Mapping from (node, layer) to index
    """
    state_nodes = []
    state_node_to_idx = {}
    
    # Collect all state nodes in specified layers
    for node_tuple in network.core_network.nodes():
        node_id, layer = node_tuple
        if layer in layers:
            state_nodes.append((node_id, layer))
            state_node_to_idx[(node_id, layer)] = len(state_nodes) - 1
    
    return state_nodes, state_node_to_idx


def _compute_intra_clustering(
    layer_adjacency: Dict[str, Dict[str, Set[str]]], layers: List[str]
) -> Dict[Tuple[str, str], float]:
    """
    Compute intra-layer clustering coefficient for each (node, layer) pair.

    Parameters
    ----------
    layer_adjacency : dict
        Adjacency structure from _build_layer_adjacency
    layers : list of str
        Layers to process

    Returns
    -------
    dict
        Mapping (node, layer) -> clustering coefficient
    """
    coefficients = {}
    
    for layer in layers:
        for node, neighbors in layer_adjacency[layer].items():
            k = len(neighbors)
            
            # Need at least 2 neighbors to form triangles
            if k < 2:
                coefficients[(node, layer)] = 0.0
                continue
            
            # Count triangles: for each pair of neighbors, check if they're connected
            triangles = 0
            neighbors_list = list(neighbors)
            for i in range(len(neighbors_list)):
                for j in range(i + 1, len(neighbors_list)):
                    neighbor_i = neighbors_list[i]
                    neighbor_j = neighbors_list[j]
                    
                    # Check if neighbor_i and neighbor_j are connected in this layer
                    if (neighbor_j in layer_adjacency[layer].get(neighbor_i, set())):
                        triangles += 1
            
            # Clustering coefficient formula
            max_possible_triangles = k * (k - 1) / 2
            if max_possible_triangles > 0:
                coefficients[(node, layer)] = triangles / max_possible_triangles
            else:
                coefficients[(node, layer)] = 0.0
    
    return coefficients


def _compute_multiplex_clustering(
    layer_adjacency: Dict[str, Dict[str, Set[str]]],
    layers: List[str],
    network: multi_layer_network,
) -> Dict[Tuple[str, None], float]:
    """
    Compute aggregated multiplex clustering coefficient for each node.

    This aggregates neighbors across all specified layers and counts triangles
    that can close in any of those layers.

    Parameters
    ----------
    layer_adjacency : dict
        Adjacency structure from _build_layer_adjacency
    layers : list of str
        Layers to aggregate over
    network : multi_layer_network
        The multilayer network

    Returns
    -------
    dict
        Mapping (node, None) -> clustering coefficient
    """
    coefficients = {}
    
    # Get all unique physical nodes across specified layers
    all_nodes = set()
    for layer in layers:
        all_nodes.update(layer_adjacency[layer].keys())
    
    for node in all_nodes:
        # Aggregate neighbors across all layers
        aggregated_neighbors = set()
        for layer in layers:
            if node in layer_adjacency[layer]:
                aggregated_neighbors.update(layer_adjacency[layer][node])
        
        k = len(aggregated_neighbors)
        
        # Need at least 2 neighbors to form triangles
        if k < 2:
            coefficients[(node, None)] = 0.0
            continue
        
        # Count triangles: for each pair of neighbors, check if they're connected
        # in ANY of the specified layers
        triangles = 0
        neighbors_list = list(aggregated_neighbors)
        for i in range(len(neighbors_list)):
            for j in range(i + 1, len(neighbors_list)):
                neighbor_i = neighbors_list[i]
                neighbor_j = neighbors_list[j]
                
                # Check if this pair is connected in any layer
                connected = False
                for layer in layers:
                    if neighbor_i in layer_adjacency[layer].get(neighbor_j, set()):
                        connected = True
                        break
                
                if connected:
                    triangles += 1
        
        # Clustering coefficient formula
        max_possible_triangles = k * (k - 1) / 2
        if max_possible_triangles > 0:
            coefficients[(node, None)] = triangles / max_possible_triangles
        else:
            coefficients[(node, None)] = 0.0
    
    return coefficients


def _compute_supra_clustering(
    network: multi_layer_network,
    layers: List[str],
    include_cross_layer: bool = True,
) -> Dict[Tuple[str, str], float]:
    """
    Compute clustering coefficient using supra-adjacency matrix.

    Parameters
    ----------
    network : multi_layer_network
        The multilayer network
    layers : list of str
        Layers to include
    include_cross_layer : bool
        If True, include inter-layer edges in the supra-adjacency matrix

    Returns
    -------
    dict
        Mapping (node, layer) -> clustering coefficient
    """
    # Build state node index
    state_nodes, state_node_to_idx = _build_state_node_index(network, layers)
    n = len(state_nodes)
    
    if n == 0:
        return {}
    
    # Build supra-adjacency matrix as sparse matrix
    A = lil_matrix((n, n), dtype=float)
    
    for u, v, data in network.core_network.edges(data=True):
        node_u, layer_u = u
        node_v, layer_v = v
        
        # Check if both state nodes are in our index
        if (node_u, layer_u) not in state_node_to_idx:
            continue
        if (node_v, layer_v) not in state_node_to_idx:
            continue
        
        # Include intralayer edges from specified layers
        if layer_u == layer_v and layer_u in layers:
            idx_u = state_node_to_idx[(node_u, layer_u)]
            idx_v = state_node_to_idx[(node_v, layer_v)]
            A[idx_u, idx_v] = 1.0
            A[idx_v, idx_u] = 1.0  # Undirected
        
        # Include inter-layer edges if requested
        elif include_cross_layer and layer_u != layer_v:
            idx_u = state_node_to_idx[(node_u, layer_u)]
            idx_v = state_node_to_idx[(node_v, layer_v)]
            A[idx_u, idx_v] = 1.0
            A[idx_v, idx_u] = 1.0  # Undirected
    
    # Convert to CSR for efficient matrix operations
    A = A.tocsr()
    
    # Compute A^2
    A2 = A @ A
    
    # Compute A^3
    A3 = A2 @ A
    
    # Extract diagonal of A^3 (number of triangles * 2 for each node)
    diagonal_A3 = A3.diagonal()
    
    # Compute degrees
    degrees = np.array(A.sum(axis=1)).flatten()
    
    # Compute clustering coefficients
    coefficients = {}
    for i, (node, layer) in enumerate(state_nodes):
        d = degrees[i]
        
        if d < 2:
            coefficients[(node, layer)] = 0.0
            continue
        
        # Number of triangles incident to this node
        t = diagonal_A3[i] / 2.0
        
        # Clustering coefficient
        max_possible_triangles = d * (d - 1) / 2.0
        if max_possible_triangles > 0:
            coefficients[(node, layer)] = t / max_possible_triangles
        else:
            coefficients[(node, layer)] = 0.0
    
    return coefficients

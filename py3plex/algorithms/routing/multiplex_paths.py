"""
Native multiplex shortest-path routing with explicit layer-switching costs.

This module implements routing algorithms that preserve layer semantics
and avoid flattening the network. Routes are computed over an implicit
(node, layer) state space with configurable switching costs.

Key Features:
    - Sparse-first implementation (no dense supra-adjacency materialization)
    - Explicit layer-switching costs (scalar or matrix-valued)
    - Multi-objective optimization (distance vs. switches)
    - Layer filtering and constraints
    - Deterministic and reproducible results

Example:
    >>> from py3plex.core import multinet
    >>> from py3plex.algorithms.routing import multiplex_shortest_path
    >>> 
    >>> # Create a multilayer network
    >>> net = multinet.multi_layer_network()
    >>> net.add_edges([
    ...     {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    ...     {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    ...     {'source': 'A', 'target': 'C', 'source_type': 'work', 'target_type': 'work', 'weight': 0.5},
    ... ])
    >>> 
    >>> # Find shortest path with switch cost
    >>> result = multiplex_shortest_path(net, 'A', 'C', switch_cost=2.0)
    >>> print(result['path'])
    [('A', 'work'), ('C', 'work')]
    >>> print(result['total_distance'])
    0.5
"""

import heapq
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import networkx as nx

from py3plex.exceptions import AlgorithmError, InvalidNodeError


def _get_node_layers(network: Any, node_id: Any) -> List[str]:
    """Get all layers where a node exists.
    
    Args:
        network: Multi-layer network
        node_id: Node identifier
        
    Returns:
        List of layer names where the node exists
    """
    G = network.core_network if hasattr(network, 'core_network') else network
    layers = []
    
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            if node[0] == node_id:
                layers.append(node[1])
    
    return layers


def _get_neighbors_in_layer(
    network: Any,
    node_id: Any,
    layer: str,
    weight: str = "weight"
) -> List[Tuple[Any, str, float]]:
    """Get neighbors of a node within the same layer (intra-layer edges).
    
    Args:
        network: Multi-layer network
        node_id: Node identifier
        layer: Layer name
        weight: Edge weight attribute name
        
    Returns:
        List of tuples: (neighbor_id, layer, edge_weight)
    """
    G = network.core_network if hasattr(network, 'core_network') else network
    state = (node_id, layer)
    
    if state not in G:
        return []
    
    neighbors = []
    for neighbor in G.neighbors(state):
        if isinstance(neighbor, tuple) and len(neighbor) >= 2:
            neighbor_id, neighbor_layer = neighbor[0], neighbor[1]
            
            # Only consider intra-layer edges
            if neighbor_layer == layer:
                edge_data = G.get_edge_data(state, neighbor)
                
                # Handle MultiGraph (edge_data is dict of dicts) vs Graph
                if edge_data:
                    if isinstance(edge_data, dict) and 0 in edge_data:
                        # MultiGraph: edge_data = {0: {'weight': ..., ...}, ...}
                        edge_weight = edge_data[0].get(weight, 1.0)
                    else:
                        # Regular Graph: edge_data = {'weight': ..., ...}
                        edge_weight = edge_data.get(weight, 1.0)
                else:
                    edge_weight = 1.0
                
                neighbors.append((neighbor_id, neighbor_layer, edge_weight))
    
    return neighbors


def _get_switch_cost(
    from_layer: str,
    to_layer: str,
    switch_cost: float,
    switch_cost_matrix: Optional[Dict[Tuple[str, str], float]]
) -> float:
    """Get the cost of switching from one layer to another.
    
    Args:
        from_layer: Source layer
        to_layer: Target layer
        switch_cost: Default scalar switch cost
        switch_cost_matrix: Optional matrix of layer-pair-specific costs
        
    Returns:
        Switch cost value
    """
    if from_layer == to_layer:
        return 0.0
    
    if switch_cost_matrix is not None:
        # Try both orderings (for asymmetric matrices)
        if (from_layer, to_layer) in switch_cost_matrix:
            return switch_cost_matrix[(from_layer, to_layer)]
        elif (to_layer, from_layer) in switch_cost_matrix:
            return switch_cost_matrix[(to_layer, from_layer)]
    
    return switch_cost


def _dijkstra_multiplex(
    network: Any,
    source: Any,
    target: Any,
    weight: str = "weight",
    switch_cost: float = 1.0,
    switch_cost_matrix: Optional[Dict[Tuple[str, str], float]] = None,
    allowed_layers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Dijkstra's algorithm on multiplex network with layer switching costs.
    
    This implements single-source shortest path over the implicit (node, layer)
    state space. Intralayer edges use the original edge weights, while interlayer
    transitions (layer switches) use configurable switch costs.
    
    Args:
        network: Multi-layer network
        source: Source node ID (layer-agnostic)
        target: Target node ID (layer-agnostic)
        weight: Edge weight attribute name
        switch_cost: Default scalar switch cost for layer transitions
        switch_cost_matrix: Optional dict mapping (layer1, layer2) -> cost
        allowed_layers: Optional list of layers to restrict search
        
    Returns:
        Dictionary with:
            - path: List of (node, layer) tuples
            - total_distance: Sum of edge weights and switch costs
            - num_switches: Number of layer transitions
            - layers_visited: Set of layers in the path
            - success: Boolean indicating if path was found
    """
    # Get all layers where source and target exist
    source_layers = _get_node_layers(network, source)
    target_layers = _get_node_layers(network, target)
    
    if not source_layers:
        raise InvalidNodeError(source, suggestions=["Check that the node exists in the network"])
    
    if not target_layers:
        raise InvalidNodeError(target, suggestions=["Check that the node exists in the network"])
    
    # Filter by allowed layers if specified
    if allowed_layers is not None:
        source_layers = [l for l in source_layers if l in allowed_layers]
        target_layers = [l for l in target_layers if l in allowed_layers]
        
        if not source_layers or not target_layers:
            return {
                'path': [],
                'total_distance': float('inf'),
                'num_switches': 0,
                'layers_visited': set(),
                'success': False,
                'error': 'No valid layers for source or target'
            }
    
    # Priority queue: (distance, num_switches, current_state)
    # current_state is (node_id, layer)
    pq = []
    distances = {}
    predecessors = {}
    
    # Initialize with all source states
    for layer in source_layers:
        state = (source, layer)
        heapq.heappush(pq, (0.0, 0, state))
        distances[state] = 0.0
        predecessors[state] = None
    
    visited = set()
    
    while pq:
        current_dist, current_switches, current_state = heapq.heappop(pq)
        
        if current_state in visited:
            continue
        
        visited.add(current_state)
        current_node, current_layer = current_state
        
        # Check if we reached the target
        if current_node == target:
            # Reconstruct path
            path = []
            state = current_state
            while state is not None:
                path.append(state)
                state = predecessors.get(state)
            path.reverse()
            
            # Count layer switches
            num_switches = 0
            for i in range(1, len(path)):
                if path[i][1] != path[i-1][1]:
                    num_switches += 1
            
            layers_visited = {state[1] for state in path}
            
            return {
                'path': path,
                'total_distance': current_dist,
                'num_switches': num_switches,
                'layers_visited': layers_visited,
                'success': True
            }
        
        # Explore intralayer neighbors (same layer)
        for neighbor_id, neighbor_layer, edge_weight in _get_neighbors_in_layer(
            network, current_node, current_layer, weight
        ):
            if allowed_layers is not None and neighbor_layer not in allowed_layers:
                continue
            
            neighbor_state = (neighbor_id, neighbor_layer)
            new_dist = current_dist + edge_weight
            
            if neighbor_state not in distances or new_dist < distances[neighbor_state]:
                distances[neighbor_state] = new_dist
                predecessors[neighbor_state] = current_state
                heapq.heappush(pq, (new_dist, current_switches, neighbor_state))
        
        # Explore interlayer transitions (layer switches for same node)
        node_layers = _get_node_layers(network, current_node)
        if allowed_layers is not None:
            node_layers = [l for l in node_layers if l in allowed_layers]
        
        for other_layer in node_layers:
            if other_layer == current_layer:
                continue
            
            switch_cost_val = _get_switch_cost(
                current_layer, other_layer, switch_cost, switch_cost_matrix
            )
            new_dist = current_dist + switch_cost_val
            neighbor_state = (current_node, other_layer)
            
            if neighbor_state not in distances or new_dist < distances[neighbor_state]:
                distances[neighbor_state] = new_dist
                predecessors[neighbor_state] = current_state
                heapq.heappush(pq, (new_dist, current_switches + 1, neighbor_state))
    
    # No path found
    return {
        'path': [],
        'total_distance': float('inf'),
        'num_switches': 0,
        'layers_visited': set(),
        'success': False,
        'error': 'No path found'
    }


def _multiobjective_dijkstra(
    network: Any,
    source: Any,
    target: Any,
    weight: str = "weight",
    switch_cost: float = 1.0,
    switch_cost_matrix: Optional[Dict[Tuple[str, str], float]] = None,
    allowed_layers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Multi-objective Dijkstra returning Pareto-optimal paths.
    
    Optimizes over two objectives:
        1. Total distance (sum of edge weights and switch costs)
        2. Number of layer switches
    
    Uses label-setting approach with Pareto dominance checking.
    
    Args:
        network: Multi-layer network
        source: Source node ID
        target: Target node ID
        weight: Edge weight attribute name
        switch_cost: Default scalar switch cost
        switch_cost_matrix: Optional dict mapping (layer1, layer2) -> cost
        allowed_layers: Optional list of layers to restrict search
        
    Returns:
        Dictionary with:
            - paths: List of Pareto-optimal paths
            - objectives: List of (distance, switches) tuples for each path
            - success: Boolean indicating if any path was found
    """
    # Get all layers where source and target exist
    source_layers = _get_node_layers(network, source)
    target_layers = _get_node_layers(network, target)
    
    if not source_layers:
        raise InvalidNodeError(source)
    if not target_layers:
        raise InvalidNodeError(target)
    
    # Filter by allowed layers if specified
    if allowed_layers is not None:
        source_layers = [l for l in source_layers if l in allowed_layers]
        target_layers = [l for l in target_layers if l in allowed_layers]
        
        if not source_layers or not target_layers:
            return {
                'paths': [],
                'objectives': [],
                'success': False,
                'error': 'No valid layers'
            }
    
    # Label class to track multiple non-dominated solutions per state
    class Label:
        def __init__(self, distance, switches, state, predecessor_label=None):
            self.distance = distance
            self.switches = switches
            self.state = state
            self.predecessor = predecessor_label
        
        def dominates(self, other):
            """Check if this label Pareto-dominates another."""
            return (self.distance <= other.distance and self.switches <= other.switches and
                    (self.distance < other.distance or self.switches < other.switches))
        
        def __lt__(self, other):
            # For priority queue ordering
            return (self.distance, self.switches) < (other.distance, other.switches)
    
    # Track non-dominated labels per state
    labels = {}  # state -> list of Label objects
    pq = []
    
    # Initialize with source states
    for layer in source_layers:
        state = (source, layer)
        label = Label(0.0, 0, state)
        labels[state] = [label]
        heapq.heappush(pq, (0.0, 0, label))
    
    # Track target labels (Pareto frontier at target)
    target_labels = []
    
    while pq:
        _, _, current_label = heapq.heappop(pq)
        current_state = current_label.state
        current_node, current_layer = current_state
        
        # Check if dominated by existing labels at this state
        dominated = False
        for other_label in labels.get(current_state, []):
            if other_label is not current_label and other_label.dominates(current_label):
                dominated = True
                break
        
        if dominated:
            continue
        
        # Check if reached target
        if current_node == target:
            # Check if this label is non-dominated by existing target labels
            is_dominated = False
            labels_to_remove = []
            
            for i, other_label in enumerate(target_labels):
                if other_label.dominates(current_label):
                    is_dominated = True
                    break
                elif current_label.dominates(other_label):
                    labels_to_remove.append(i)
            
            if not is_dominated:
                # Remove dominated labels
                for i in reversed(labels_to_remove):
                    target_labels.pop(i)
                target_labels.append(current_label)
            
            continue
        
        # Explore intralayer neighbors
        for neighbor_id, neighbor_layer, edge_weight in _get_neighbors_in_layer(
            network, current_node, current_layer, weight
        ):
            if allowed_layers is not None and neighbor_layer not in allowed_layers:
                continue
            
            neighbor_state = (neighbor_id, neighbor_layer)
            new_label = Label(
                current_label.distance + edge_weight,
                current_label.switches,
                neighbor_state,
                current_label
            )
            
            # Check if new label is dominated
            is_dominated = False
            for other_label in labels.get(neighbor_state, []):
                if other_label.dominates(new_label):
                    is_dominated = True
                    break
            
            if not is_dominated:
                if neighbor_state not in labels:
                    labels[neighbor_state] = []
                labels[neighbor_state].append(new_label)
                heapq.heappush(pq, (new_label.distance, new_label.switches, new_label))
        
        # Explore interlayer transitions
        node_layers = _get_node_layers(network, current_node)
        if allowed_layers is not None:
            node_layers = [l for l in node_layers if l in allowed_layers]
        
        for other_layer in node_layers:
            if other_layer == current_layer:
                continue
            
            switch_cost_val = _get_switch_cost(
                current_layer, other_layer, switch_cost, switch_cost_matrix
            )
            neighbor_state = (current_node, other_layer)
            new_label = Label(
                current_label.distance + switch_cost_val,
                current_label.switches + 1,
                neighbor_state,
                current_label
            )
            
            # Check if dominated
            is_dominated = False
            for other_label in labels.get(neighbor_state, []):
                if other_label.dominates(new_label):
                    is_dominated = True
                    break
            
            if not is_dominated:
                if neighbor_state not in labels:
                    labels[neighbor_state] = []
                labels[neighbor_state].append(new_label)
                heapq.heappush(pq, (new_label.distance, new_label.switches, new_label))
    
    # Reconstruct Pareto-optimal paths
    if not target_labels:
        return {
            'paths': [],
            'objectives': [],
            'success': False,
            'error': 'No path found'
        }
    
    paths = []
    objectives = []
    
    for label in target_labels:
        path = []
        current = label
        while current is not None:
            path.append(current.state)
            current = current.predecessor
        path.reverse()
        paths.append(path)
        objectives.append((label.distance, label.switches))
    
    return {
        'paths': paths,
        'objectives': objectives,
        'success': True
    }


def multiplex_shortest_path(
    multilayer_network: Any,
    source: Any,
    target: Any,
    weight: str = "weight",
    switch_cost: float = 1.0,
    switch_cost_matrix: Optional[Dict[Tuple[str, str], float]] = None,
    allowed_layers: Optional[List[str]] = None,
    objective: str = "single",
    method: str = "dijkstra",
    return_path: bool = True
) -> Dict[str, Any]:
    """Find shortest path(s) in a multiplex network with layer switching costs.
    
    This function computes routing over the implicit (node, layer) state space,
    preserving layer semantics without flattening the network. Supports both
    single-objective and multi-objective optimization.
    
    State Space:
        - States are (node_id, layer_id) tuples
        - Intralayer edges: (u, L) -> (v, L) with original edge weight
        - Interlayer transitions: (u, L1) -> (u, L2) with switch cost
        - No dense supra-adjacency is materialized
    
    Args:
        multilayer_network: Multi-layer network (multi_layer_network object)
        source: Source node ID (layer-agnostic)
        target: Target node ID (layer-agnostic)
        weight: Edge weight attribute name (default: "weight")
        switch_cost: Scalar switch cost for layer transitions (default: 1.0)
        switch_cost_matrix: Optional dict mapping (layer1, layer2) -> cost
            for asymmetric switching costs
        allowed_layers: Optional list of layer names to restrict search
        objective: Optimization objective (default: "single")
            - "single": Single shortest path
            - "lexicographic": Minimize distance, then switches
            - "pareto": Return all Pareto-optimal paths
        method: Algorithm to use (default: "dijkstra")
            - "dijkstra": Standard Dijkstra's algorithm
            - "multiobjective": Label-setting multi-objective Dijkstra
        return_path: Whether to return path details (default: True)
        
    Returns:
        For objective="single":
            Dictionary with keys:
                - path: List of (node, layer) tuples
                - total_distance: Sum of edge weights and switch costs
                - num_switches: Number of layer transitions
                - layers_visited: Set of layers in the path
                - success: Boolean indicating if path was found
                
        For objective="pareto":
            Dictionary with keys:
                - paths: List of Pareto-optimal paths
                - objectives: List of (distance, switches) tuples
                - success: Boolean
    
    Raises:
        InvalidNodeError: If source or target node not found
        AlgorithmError: If invalid objective or method specified
        
    Examples:
        >>> # Basic usage with switch cost
        >>> result = multiplex_shortest_path(net, 'A', 'C', switch_cost=2.0)
        >>> print(result['path'])
        [('A', 'layer1'), ('B', 'layer1'), ('C', 'layer1')]
        
        >>> # Zero switch cost (equivalent to flattened network)
        >>> result = multiplex_shortest_path(net, 'A', 'C', switch_cost=0.0)
        
        >>> # High switch cost (bias towards single-layer paths)
        >>> result = multiplex_shortest_path(net, 'A', 'C', switch_cost=100.0)
        
        >>> # Asymmetric switch costs
        >>> switch_matrix = {
        ...     ('social', 'work'): 0.5,
        ...     ('work', 'social'): 2.0,
        ... }
        >>> result = multiplex_shortest_path(net, 'A', 'C', 
        ...                                   switch_cost_matrix=switch_matrix)
        
        >>> # Multi-objective optimization
        >>> result = multiplex_shortest_path(net, 'A', 'C', 
        ...                                   objective="pareto")
        >>> for path, (dist, switches) in zip(result['paths'], result['objectives']):
        ...     print(f"Path: {path}, Distance: {dist}, Switches: {switches}")
        
        >>> # Layer-constrained routing
        >>> result = multiplex_shortest_path(net, 'A', 'C',
        ...                                   allowed_layers=['social', 'work'])
    
    Notes:
        - Complexity: O((|V| * |L|) * log(|V| * |L|) + |E|) where |V| is nodes,
          |L| is layers, |E| is edges
        - State space grows as |V| * |L|, so performance depends on layer count
        - Zero switch cost reduces to shortest path on flattened network
        - High switch cost biases towards single-layer paths
        - Results are deterministic given the same input
    
    See Also:
        - py3plex.paths.shortest_path: Single-layer shortest path
        - py3plex.algorithms.temporal: Temporal path algorithms
    """
    # Validate inputs
    valid_objectives = ["single", "lexicographic", "pareto"]
    if objective not in valid_objectives:
        raise AlgorithmError(
            f"Invalid objective '{objective}'",
            algorithm_name="multiplex_shortest_path",
            valid_algorithms=valid_objectives
        )
    
    valid_methods = ["dijkstra", "multiobjective"]
    if method not in valid_methods:
        raise AlgorithmError(
            f"Invalid method '{method}'",
            algorithm_name="multiplex_shortest_path", 
            valid_algorithms=valid_methods
        )
    
    # Route to appropriate algorithm
    if objective == "pareto" or method == "multiobjective":
        result = _multiobjective_dijkstra(
            multilayer_network,
            source,
            target,
            weight=weight,
            switch_cost=switch_cost,
            switch_cost_matrix=switch_cost_matrix,
            allowed_layers=allowed_layers
        )
    else:
        # Single-objective or lexicographic
        result = _dijkstra_multiplex(
            multilayer_network,
            source,
            target,
            weight=weight,
            switch_cost=switch_cost,
            switch_cost_matrix=switch_cost_matrix,
            allowed_layers=allowed_layers
        )
    
    # Add metadata
    if 'path' in result and result['path']:
        result['method'] = method
        result['switch_cost'] = switch_cost
        result['source'] = source
        result['target'] = target
    
    return result

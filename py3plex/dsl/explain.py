"""Explanation engine for DSL queries.

This module provides functions to attach explanations to query results,
enriching each result row (typically nodes) with additional context such as:
- Community membership and size
- Top neighbors by weight or degree
- Layer footprint (which layers a node appears in)
"""

from typing import Any, Dict, List, Optional, Tuple
import logging
from collections import Counter

logger = logging.getLogger(__name__)


def explain_rows(
    network: Any,
    rows: List[Dict[str, Any]],
    *,
    include: List[str],
    neighbors_top: int,
    neighbors_cfg: Dict[str, Any],
    community_cfg: Dict[str, Any],
    layer_footprint_cfg: Dict[str, Any],
    attribution_cfg: Dict[str, Any],
    metric_values: Optional[Dict[str, Dict[Any, Any]]] = None,
    context: Optional[Dict[str, Any]] = None,
    cache: bool = True,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Attach explanations to result rows.
    
    This is the main entry point for the explanation engine. It processes a list
    of result rows (typically from a node query) and attaches explanation metadata
    to each row.
    
    Args:
        network: Multilayer network instance
        rows: List of result row dictionaries (each with 'id' and optionally 'layer')
        include: List of explanation blocks to compute
        neighbors_top: Maximum number of neighbors to return
        neighbors_cfg: Configuration for neighbor selection
        community_cfg: Configuration for community explanations
        layer_footprint_cfg: Configuration for layer footprint
        attribution_cfg: Configuration for attribution explanations
        metric_values: Dictionary of computed metric values (for attribution)
        context: Query context (for attribution)
        cache: Whether to enable caching (currently unused, reserved for future)
        
    Returns:
        Tuple of (enriched_rows, explanation_schema)
        - enriched_rows: Rows with added '_explanations' field
        - explanation_schema: Metadata describing the explanation structure
        
    Example:
        >>> rows = [{'id': 'A', 'layer': 'social'}, {'id': 'B', 'layer': 'social'}]
        >>> enriched, schema = explain_rows(
        ...     network, rows,
        ...     include=["community", "top_neighbors"],
        ...     neighbors_top=5,
        ...     neighbors_cfg={},
        ...     community_cfg={},
        ...     layer_footprint_cfg={},
        ...     attribution_cfg={},
        ...     cache=True,
        ... )
    """
    if not rows:
        return rows, {}
    
    # Initialize explanation cache if needed
    cache_dict = {} if cache else None
    
    # Precompute community info if needed
    community_data = None
    if "community" in include:
        community_data = _precompute_community_data(network, rows, community_cfg)
    
    # Precompute layer footprint lookup if needed
    layer_footprint_data = None
    if "layer_footprint" in include:
        layer_footprint_data = _precompute_layer_footprint(network, rows, layer_footprint_cfg)
    
    # Precompute attribution if needed
    attribution_data = None
    if "attribution" in include:
        attribution_data = _precompute_attribution(
            network, rows, attribution_cfg, metric_values, context
        )
    
    # Process each row
    enriched_rows = []
    for row in rows:
        node_id = row.get('id')
        layer = row.get('layer')
        
        if node_id is None:
            # Skip rows without node ID
            enriched_rows.append(row)
            continue
        
        # Build explanations for this row
        explanations = {}
        
        # Community explanation
        if "community" in include and community_data is not None:
            comm_exp = _explain_community(node_id, layer, community_data)
            explanations.update(comm_exp)
        
        # Top neighbors explanation
        if "top_neighbors" in include:
            neighbors_exp = _explain_top_neighbors(
                network, node_id, layer, neighbors_top, neighbors_cfg, cache_dict
            )
            explanations.update(neighbors_exp)
        
        # Layer footprint explanation
        if "layer_footprint" in include and layer_footprint_data is not None:
            footprint_exp = _explain_layer_footprint(node_id, layer_footprint_data)
            explanations.update(footprint_exp)
        
        # Attribution explanation
        if "attribution" in include and attribution_data is not None:
            key = (node_id, layer)
            if key in attribution_data:
                explanations["attribution"] = attribution_data[key]
        
        # Attach explanations to row
        enriched_row = dict(row)
        enriched_row['_explanations'] = explanations
        enriched_rows.append(enriched_row)
    
    # Build explanation schema
    schema = {
        "blocks": include,
        "neighbors_top": neighbors_top if "top_neighbors" in include else None,
    }
    
    return enriched_rows, schema


def _precompute_community_data(
    network: Any,
    rows: List[Dict[str, Any]],
    community_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """Precompute community membership and sizes.
    
    Args:
        network: Multilayer network instance
        rows: Result rows
        community_cfg: Community configuration
        
    Returns:
        Dictionary with community data
    """
    # Try to get partition from network
    partition = None
    
    # Check if network has partition stored
    if hasattr(network, 'partition'):
        partition = network.partition
    elif hasattr(network, 'get_node_partition'):
        # Try to get partition for all nodes
        try:
            partition = {}
            for row in rows:
                node_id = row.get('id')
                layer = row.get('layer')
                if node_id is not None:
                    # Try layer-specific partition first
                    node_key = (node_id, layer) if layer else node_id
                    comm = network.get_node_partition(node_key)
                    partition[node_key] = comm
        except Exception:
            partition = None
    
    if partition is None:
        # No partition available, return empty data
        logger.debug("No community partition available in network")
        return {"partition": {}, "sizes": {}}
    
    # Compute community sizes
    sizes = Counter(partition.values())
    
    return {
        "partition": partition,
        "sizes": sizes,
    }


def _explain_community(
    node_id: str,
    layer: Optional[str],
    community_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate community explanation for a node.
    
    Args:
        node_id: Node identifier
        layer: Layer name (optional)
        community_data: Precomputed community data
        
    Returns:
        Dictionary with community_id and community_size
    """
    partition = community_data.get("partition", {})
    sizes = community_data.get("sizes", {})
    
    # Try layer-specific key first, then global
    node_key = (node_id, layer) if layer else node_id
    community_id = partition.get(node_key)
    
    if community_id is None and layer:
        # Try without layer
        community_id = partition.get(node_id)
    
    if community_id is None:
        return {
            "community_id": None,
            "community_size": None,
        }
    
    community_size = sizes.get(community_id, 0)
    
    return {
        "community_id": community_id,
        "community_size": community_size,
    }


def _explain_top_neighbors(
    network: Any,
    node_id: str,
    layer: Optional[str],
    neighbors_top: int,
    neighbors_cfg: Dict[str, Any],
    cache_dict: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate top neighbors explanation for a node.
    
    Args:
        network: Multilayer network instance
        node_id: Node identifier
        layer: Layer name (optional, used for layer-scoped neighbors)
        neighbors_top: Maximum number of neighbors to return
        neighbors_cfg: Neighbor selection configuration
        cache_dict: Optional cache for neighbor lookups
        
    Returns:
        Dictionary with top_neighbors list
    """
    # Extract configuration
    metric = neighbors_cfg.get("metric", "weight")
    scope = neighbors_cfg.get("scope", "layer")
    direction = neighbors_cfg.get("direction", "both")
    
    # Check cache
    cache_key = None
    if cache_dict is not None:
        cache_key = ("neighbors", node_id, layer, neighbors_top, metric, scope, direction)
        if cache_key in cache_dict:
            return {"top_neighbors": cache_dict[cache_key]}
    
    # Get neighbors from network
    neighbors_list = _get_neighbors_from_network(
        network, node_id, layer, scope, direction
    )
    
    # Rank neighbors
    ranked = _rank_neighbors(network, node_id, layer, neighbors_list, metric)
    
    # Take top-k
    top_k = ranked[:neighbors_top]
    
    # Format as list of dicts
    result = []
    for neighbor_info in top_k:
        result.append({
            "neighbor_id": neighbor_info["id"],
            "neighbor_layer": neighbor_info.get("layer"),
            "edge_weight": neighbor_info.get("weight", 1.0),
            "score": neighbor_info.get("score", 1.0),
        })
    
    # Cache result
    if cache_dict is not None and cache_key is not None:
        cache_dict[cache_key] = result
    
    return {"top_neighbors": result}


def _get_neighbors_from_network(
    network: Any,
    node_id: str,
    layer: Optional[str],
    scope: str,
    direction: str,
) -> List[Tuple[str, Optional[str], float]]:
    """Get neighbors from the network.

    Use the strongest matching parallel edge for each neighbor.

    Args:
        network: Multilayer network instance
        node_id: Node identifier
        layer: Layer name (optional)
        scope: "layer" (layer-scoped) or "global" (all layers)
        direction: "out", "in", or "both"
        
    Returns:
        List of (neighbor_id, neighbor_layer, weight) tuples
    """
    G = getattr(network, "core_network", None)
    if G is None:
        return []

    if scope == "layer" and layer is not None:
        node_keys = [(node_id, layer)]
    else:
        node_keys = [node for node in G if node == node_id or (
            isinstance(node, tuple) and node[0] == node_id
        )]

    neighbors = []
    for node in node_keys:
        if node not in G:
            continue
        weights = {}
        edge_sources = []
        if not G.is_directed() or direction in ("out", "both"):
            edge_sources.append((neighbor, G.get_edge_data(node, neighbor)) for neighbor in G[node])
        if G.is_directed() and direction in ("in", "both"):
            edge_sources.append(
                (neighbor, G.get_edge_data(neighbor, node)) for neighbor in G.predecessors(node)
            )
        for edges in edge_sources:
            for neighbor, data in edges:
                if G.is_multigraph():
                    weight = max(attrs.get("weight", 1.0) for attrs in data.values())
                else:
                    weight = data.get("weight", 1.0)
                if neighbor not in weights or weight > weights[neighbor]:
                    weights[neighbor] = weight
        for neighbor, weight in weights.items():
            if isinstance(neighbor, tuple) and len(neighbor) >= 2:
                neighbors.append((neighbor[0], neighbor[1], weight))
            else:
                neighbors.append((neighbor, None, weight))
    return neighbors


def _rank_neighbors(
    network: Any,
    node_id: str,
    layer: Optional[str],
    neighbors_list: List[Tuple[str, Optional[str], float]],
    metric: str,
) -> List[Dict[str, Any]]:
    """Rank neighbors by the specified metric.
    
    Args:
        network: Multilayer network instance
        node_id: Source node identifier
        layer: Source node layer
        neighbors_list: List of (neighbor_id, neighbor_layer, weight) tuples
        metric: Ranking metric ("weight" or "degree")
        
    Returns:
        Sorted list of neighbor info dicts
    """
    neighbor_data = []
    
    for nbr_id, nbr_layer, weight in neighbors_list:
        if metric == "weight":
            score = weight
        elif metric == "degree":
            # Get neighbor degree
            score = _get_node_degree(network, nbr_id, nbr_layer)
        else:
            # Unknown metric, use weight as fallback
            score = weight
        
        neighbor_data.append({
            "id": nbr_id,
            "layer": nbr_layer,
            "weight": weight,
            "score": score,
        })
    
    # Sort by score (descending), then by neighbor_id for deterministic ordering
    neighbor_data.sort(key=lambda x: (-x["score"], str(x["id"]), str(x["layer"])))
    
    return neighbor_data


def _get_node_degree(network: Any, node_id: str, layer: Optional[str]) -> int:
    """Get the degree of a node.
    
    Args:
        network: Multilayer network instance
        node_id: Node identifier
        layer: Layer name (optional)
        
    Returns:
        Node degree
    """
    if hasattr(network, 'core_network'):
        G = network.core_network
        node_key = (node_id, layer) if layer else node_id
        if node_key in G:
            return G.degree(node_key)
    
    return 0


def _precompute_layer_footprint(
    network: Any,
    rows: List[Dict[str, Any]],
    layer_footprint_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """Precompute layer footprint for all nodes in result set.
    
    Args:
        network: Multilayer network instance
        rows: Result rows
        layer_footprint_cfg: Configuration
        
    Returns:
        Dictionary mapping node_id -> layer_footprint data
    """
    footprint_map = {}
    
    if hasattr(network, 'core_network'):
        G = network.core_network
        
        # Extract unique node IDs from rows
        node_ids = set(row.get('id') for row in rows if row.get('id') is not None)
        
        for node_id in node_ids:
            # Find all layers this node appears in
            layers = []
            layer_degrees = {}
            
            for node_key in G.nodes():
                if isinstance(node_key, tuple) and len(node_key) >= 2:
                    if node_key[0] == node_id:
                        layer_name = node_key[1]
                        layers.append(layer_name)
                        layer_degrees[layer_name] = G.degree(node_key)
                elif node_key == node_id:
                    # Node without layer info
                    layers.append(None)
            
            footprint_map[node_id] = {
                "layers": sorted(layers) if layers else [],
                "layer_degrees": layer_degrees,
            }
    
    return footprint_map


def _explain_layer_footprint(
    node_id: str,
    layer_footprint_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate layer footprint explanation for a node.
    
    Args:
        node_id: Node identifier
        layer_footprint_data: Precomputed footprint data
        
    Returns:
        Dictionary with layers_present and n_layers_present
    """
    footprint = layer_footprint_data.get(node_id, {})
    layers = footprint.get("layers", [])
    
    return {
        "layers_present": layers,
        "n_layers_present": len(layers),
    }


def _precompute_attribution(
    network: Any,
    rows: List[Dict[str, Any]],
    attribution_cfg: Dict[str, Any],
    metric_values: Optional[Dict[str, Dict[Any, Any]]],
    context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Precompute attribution explanations for all rows.
    
    This function integrates with the attribution module to compute
    Shapley-based explanations.
    
    Args:
        network: Multilayer network instance
        rows: Result rows
        attribution_cfg: Attribution configuration dict
        metric_values: Dictionary of computed metric values
        context: Query context (for inferring metric, limit, etc.)
        
    Returns:
        Dictionary mapping item identifiers to attribution results
    """
    from py3plex.dsl.attribution import AttributionConfig, compute_attribution_for_rows
    
    config = AttributionConfig(**attribution_cfg)
    enriched_rows, _ = compute_attribution_for_rows(
        network, rows, metric_values or {}, config, context or {}
    )
    return {(row["id"], row["layer"]): row["attribution"] for row in enriched_rows}

"""
Ergonomic Helper Utilities for py3plex
========================================

This module provides convenience functions to reduce friction in common tasks.
These helpers wrap complex operations into simple, intuitive functions that
improve the user experience without changing the core API.

Example usage:
    >>> from py3plex.ergonomics import quick_network, quick_analysis
    >>> net = quick_network(people=['Alice', 'Bob'], layers=['work', 'social'])
    >>> results = quick_analysis(net, metrics=['degree', 'betweenness'])
"""

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union

from py3plex.core import multinet
from py3plex.dsl import L, Q

IntraLayerConnection = Tuple[str, str, str]
InterLayerConnection = Tuple[str, str, str, str]
Connection = Union[IntraLayerConnection, InterLayerConnection]


def _extract_layer_names(network: Any) -> List[str]:
    """Extract layer names from different `get_layers()` return shapes."""
    layers = network.get_layers()
    if isinstance(layers, tuple):
        candidate = layers[0]
    else:
        candidate = layers

    return list(candidate) if candidate is not None else []


def quick_network(
    people: List[str],
    layers: List[str],
    connections: Optional[List[Connection]] = None,
    directed: bool = False,
) -> Any:
    """
    Quickly create a multilayer network from simple inputs.

    This helper eliminates boilerplate code for creating basic networks.
    Instead of manually creating node and edge dicts, just provide lists.

    Parameters
    ----------
    people : List[str]
        List of person/node names
    layers : List[str]
        List of layer names
    connections : Optional[List[tuple]]
        List of (source, target, layer) tuples. If None, creates empty network.
    directed : bool
        Whether the network is directed (default: False)

    Returns
    -------
    multi_layer_network
        A py3plex multilayer network ready to use

    Examples
    --------
    Basic Usage:
    >>> from py3plex.ergonomics import quick_network
    >>>
    >>> # Create empty network with nodes
    >>> net = quick_network(
    ...     people=['Alice', 'Bob', 'Carol'],
    ...     layers=['work', 'social']
    ... )
    >>>
    >>> # Create network with connections (intra-layer)
    >>> net = quick_network(
    ...     people=['Alice', 'Bob', 'Carol'],
    ...     layers=['work', 'social'],
    ...     connections=[
    ...         ('Alice', 'Bob', 'work'),      # Alice-Bob in work layer
    ...         ('Bob', 'Carol', 'social'),    # Bob-Carol in social layer
    ...     ]
    ... )

    Advanced Usage (Inter-layer edges):
    >>> # Create network with inter-layer connections (4-tuples)
    >>> net = quick_network(
    ...     people=['Alice', 'Bob'],
    ...     layers=['work', 'social'],
    ...     connections=[
    ...         ('Alice', 'Bob', 'work', 'work'),      # Same layer
    ...         ('Alice', 'Bob', 'work', 'social'),    # Cross-layer
    ...     ]
    ... )

    Ergonomic Improvement
    ---------------------
    Before:
        net = multinet.multi_layer_network(directed=False)
        nodes = [{'source': person, 'type': layer}
                 for person in people for layer in layers]
        net.add_nodes(nodes)
        edges = [{'source': s, 'target': t,
                  'source_type': l, 'target_type': l}
                 for s, t, l in connections]
        net.add_edges(edges)

    After:
        net = quick_network(people, layers, connections)
    """
    net = multinet.multi_layer_network(directed=directed, verbose=False)

    # Add all nodes across all layers
    nodes = [{"source": person, "type": layer} for person in people for layer in layers]
    if nodes:
        net.add_nodes(nodes)

    # Add connections if provided
    if connections:
        edges = []
        for conn in connections:
            if len(conn) == 3:
                source, target, layer = conn
                edges.append({
                    "source": source,
                    "target": target,
                    "source_type": layer,
                    "target_type": layer,
                })
            elif len(conn) == 4:
                source, target, src_layer, tgt_layer = conn
                edges.append({
                    "source": source,
                    "target": target,
                    "source_type": src_layer,
                    "target_type": tgt_layer,
                })
            else:
                raise ValueError(
                    "Connections must be 3-tuples (source, target, layer) or "
                    "4-tuples (source, target, source_layer, target_layer)."
                )
        if edges:
            net.add_edges(edges)

    return net


def quick_analysis(
    network: Any,
    metrics: Optional[List[str]] = None,
    layers: Optional[List[str]] = None,
    top_k: Optional[int] = None,
    min_degree: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Quickly analyze a network and get common metrics.

    This helper wraps DSL queries into a simple function call that returns
    a dictionary of results for easy inspection and further analysis.

    Parameters
    ----------
    network : multi_layer_network
        The network to analyze
    metrics : List[str], optional
        List of metrics to compute (default: ['degree'])
    layers : List[str], optional
        Specific layers to analyze (default: all layers)
    top_k : int, optional
        Return only top K nodes by first metric (default: all)
    min_degree : int, optional
        Filter to nodes with degree >= min_degree (default: no filter)

    Returns
    -------
    Dict[str, Any]
        Dictionary with keys: 'dataframe', 'count', 'network_stats'

    Examples
    --------
    Basic Usage:
    >>> from py3plex.ergonomics import quick_network, quick_analysis
    >>>
    >>> net = quick_network(['Alice', 'Bob'], ['work'])
    >>> results = quick_analysis(net, metrics=['degree'])
    >>> print(results['dataframe'])

    Filter and Order:
    >>> # Get top 10 high-degree nodes
    >>> results = quick_analysis(
    ...     net,
    ...     metrics=['degree', 'betweenness_centrality'],
    ...     min_degree=2,
    ...     top_k=10
    ... )
    >>> print(f"Found {results['count']} nodes")

    Multi-layer Analysis:
    >>> # Analyze specific layers only
    >>> results = quick_analysis(
    ...     net,
    ...     metrics=['pagerank', 'clustering'],
    ...     layers=['social', 'work']  # Analyze only these layers
    ... )

    Common Patterns:
    >>> # Pattern 1: Quick degree distribution
    >>> results = quick_analysis(net, metrics=['degree'])
    >>> df = results['dataframe']
    >>> print(df['degree'].describe())  # Mean, std, quartiles
    >>>
    >>> # Pattern 2: Find hubs (high betweenness)
    >>> results = quick_analysis(
    ...     net,
    ...     metrics=['betweenness_centrality'],
    ...     top_k=20
    ... )
    >>>
    >>> # Pattern 3: Filter by degree and get multiple metrics
    >>> results = quick_analysis(
    ...     net,
    ...     metrics=['degree', 'clustering', 'betweenness_centrality'],
    ...     min_degree=5
    ... )

    Ergonomic Improvement
    ---------------------
    Before:
        result = (Q.nodes()
                  .from_layers(L[layers])
                  .compute(*metrics)
                  .where(degree__gt=min_degree)
                  .order_by(metrics[0], desc=True)
                  .limit(top_k)
                  .execute(network))
        df = result.to_pandas()

    After:
        results = quick_analysis(network, metrics, top_k=10, min_degree=2)
        df = results['dataframe']
    """
    if metrics is None:
        metrics = ["degree"]
    if not metrics:
        raise ValueError("metrics must contain at least one metric name.")

    # Build query
    query = Q.nodes()

    # Add layer filtering
    if layers:
        layer_expr = L[layers[0]]
        for layer in layers[1:]:
            layer_expr = layer_expr + L[layer]
        query = query.from_layers(layer_expr)

    # Compute metrics
    query = query.compute(*metrics)

    # Add filtering
    if min_degree is not None:
        query = query.where(degree__gt=min_degree - 1)  # >= min_degree

    # Add ordering and limiting
    if top_k is not None:
        query = query.order_by(metrics[0], desc=True).limit(top_k)

    # Execute
    result = query.execute(network)

    return {
        "dataframe": result.to_pandas(),
        "count": result.count,
        "network_stats": {
            "nodes": len(list(network.get_nodes())),
            "edges": len(list(network.get_edges())),
            "layers": len(_extract_layer_names(network)),
        },
    }


def quick_communities(
    network: Any,
    algorithm: str = "louvain",
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Quickly detect communities in a multilayer network.

    This helper simplifies community detection by wrapping algorithm
    imports and providing sensible defaults.

    Parameters
    ----------
    network : multi_layer_network
        The network to analyze
    algorithm : str
        Algorithm to use: 'louvain' or 'leiden' (default: 'louvain')
    seed : int
        Random seed for reproducibility (default: 42)

    Returns
    -------
    Dict[str, Any]
        Dictionary with keys: 'communities', 'n_communities', 'sizes'

    Examples
    --------
    >>> from py3plex.ergonomics import quick_network, quick_communities
    >>>
    >>> net = quick_network(['A', 'B', 'C'], ['work'])
    >>> results = quick_communities(net)
    >>> print(f"Found {results['n_communities']} communities")
    >>> print(results['sizes'])

    Ergonomic Improvement
    ---------------------
    Before:
        from py3plex.algorithms.community_detection import louvain_multilayer
        communities = louvain_multilayer(network, random_state=42)
        from collections import Counter
        sizes = Counter(communities.values())
        n_communities = len(sizes)

    After:
        results = quick_communities(network)
        communities = results['communities']
        n_communities = results['n_communities']
    """
    normalized_algorithm = algorithm.strip().lower()
    if normalized_algorithm == "louvain":
        from py3plex.algorithms.community_detection import louvain_multilayer

        communities = louvain_multilayer(network, random_state=seed)
    elif normalized_algorithm == "leiden":
        from py3plex.algorithms.community_detection import leiden_multilayer

        communities = leiden_multilayer(network, random_state=seed)
    else:
        raise ValueError(
            f"Unknown algorithm: {algorithm}. Use 'louvain' or 'leiden'"
        )

    sizes = Counter(communities.values())

    return {
        "communities": communities,
        "n_communities": len(sizes),
        "sizes": dict(sizes),
    }


def show_network_summary(network: Any) -> None:
    """
    Display a nicely formatted summary of a network.

    This helper prints a clear, readable summary of network structure
    that's more informative than the default __repr__.

    Parameters
    ----------
    network : multi_layer_network
        The network to summarize

    Examples
    --------
    >>> from py3plex.ergonomics import quick_network, show_network_summary
    >>>
    >>> net = quick_network(['Alice', 'Bob'], ['work', 'social'])
    >>> show_network_summary(net)

    Ergonomic Improvement
    ---------------------
    Provides a formatted, easy-to-read summary instead of manual inspection.
    """
    print("=" * 60)
    print("NETWORK SUMMARY")
    print("=" * 60)

    nodes = list(network.get_nodes())
    edges = list(network.get_edges())
    layers = _extract_layer_names(network)

    print("\nStructure:")
    print(f"  • Nodes (replicas): {len(nodes)}")
    print(f"  • Physical nodes: {len({n[0] for n in nodes})}")
    print(f"  • Edges: {len(edges)}")
    print(f"  • Layers: {len(layers)}")

    print("\nLayers:")
    for layer in layers:
        layer_nodes = [n for n in nodes if n[1] == layer]
        # Edge format: ((source, src_layer), (target, tgt_layer))
        layer_edges = [e for e in edges
                       if len(e) >= 2 and e[0][1] == layer and e[1][1] == layer]  # intra-layer
        print(f"  • {layer}: {len(layer_nodes)} nodes, {len(layer_edges)} intra-layer edges")

    # Count inter-layer edges
    inter_edges = [e for e in edges if len(e) >= 2 and e[0][1] != e[1][1]]
    if inter_edges:
        print(f"\n  • Inter-layer edges: {len(inter_edges)}")

    print("=" * 60)


# Export all helpers
__all__ = [
    "quick_network",
    "quick_analysis",
    "quick_communities",
    "show_network_summary",
]

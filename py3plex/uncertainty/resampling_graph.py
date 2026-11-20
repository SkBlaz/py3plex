"""Graph resampling utilities for structural uncertainty quantification.

This module provides safe, immutable graph resampling operations for
distributional community detection and other structural UQ tasks.

Key principles:
- **Never mutate input networks** - always return new copies
- **Preserve node set and layer structure** - only perturb edges
- **Preserve directed/undirected semantics**
- **Deterministic seeding** - same seed => identical output

Examples
--------
>>> from py3plex.core import multinet
>>> from py3plex.uncertainty.resampling_graph import perturb_network_edges
>>> 
>>> net = multinet.multi_layer_network(directed=False)
>>> _ = net.add_edges([
...     ['A', 'L1', 'B', 'L1', 1],
...     ['B', 'L1', 'C', 'L1', 1],
... ], input_type='list')
>>> 
>>> perturbed = perturb_network_edges(net, edge_drop_p=0.1, seed=42)
>>> # Original net is unchanged
"""

from __future__ import annotations

from typing import Optional

import networkx as nx
import numpy as np

from py3plex.core import multinet
from py3plex.exceptions import AlgorithmError


def perturb_network_edges(
    network: multinet.multi_layer_network,
    *,
    edge_drop_p: float,
    seed: Optional[int] = None,
    preserve_layers: bool = True,
) -> multinet.multi_layer_network:
    """Perturb network by randomly dropping edges.
    
    Creates a new network by dropping interactions independently. All
    replicas and their attributes remain, and multiplex coupling is retained.
    Useful for structural uncertainty quantification via edge perturbation.
    
    **Never modifies the input network** - returns a new copy.
    
    Parameters
    ----------
    network : multi_layer_network
        Input network to perturb (will not be modified).
    edge_drop_p : float
        Probability of dropping each edge, in [0, 1].
        - 0.0: No edges dropped (returns exact copy)
        - 1.0: All edges dropped (retains nodes and multiplex coupling)
    seed : int, optional
        Random seed for reproducibility.
    preserve_layers : bool, default=True
        If True, preserve layer labels and structure.
        If False, allow layer simplification (not recommended).
    
    Returns
    -------
    multi_layer_network
        New network with randomly dropped edges.
    
    Raises
    ------
    AlgorithmError
        If edge_drop_p is not in [0, 1].
    
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.uncertainty.resampling_graph import perturb_network_edges
    >>> 
    >>> net = multinet.multi_layer_network(directed=False)
    >>> _ = net.add_edges([
    ...     ['A', 'L1', 'B', 'L1', 1],
    ...     ['B', 'L1', 'C', 'L1', 1],
    ...     ['C', 'L1', 'A', 'L1', 1],
    ... ], input_type='list')
    >>> 
    >>> # Drop 20% of edges
    >>> perturbed = perturb_network_edges(net, edge_drop_p=0.2, seed=0)
    >>> # Original net unchanged
    >>> len(list(net.get_edges()))
    3
    >>> len(list(perturbed.get_edges()))
    2
    """
    # Validate parameters
    if not 0.0 <= edge_drop_p <= 1.0:
        raise AlgorithmError(
            f"edge_drop_p must be in [0, 1], got {edge_drop_p}",
            suggestions=["Set edge_drop_p between 0.0 (no drop) and 1.0 (drop all)"]
        )
    
    sample, edges = _edge_sample_base(network)
    rng = np.random.default_rng(seed)
    for source, target, key, attrs in edges:
        if rng.random() >= edge_drop_p:
            _add_sample_edge(sample.core_network, source, target, key, attrs)
    return sample


def bootstrap_network_edges(
    network: multinet.multi_layer_network,
    *,
    seed: Optional[int] = None,
    preserve_layers: bool = True,
) -> multinet.multi_layer_network:
    """Bootstrap resample network edges with replacement.
    
    Creates a new network by sampling edges with replacement from the
    original network. Each sampled interaction retains its attributes.
    The interaction count is preserved, and multiplex coupling is retained.
    
    **Never modifies the input network** - returns a new copy.
    
    Parameters
    ----------
    network : multi_layer_network
        Input network to resample (will not be modified).
    seed : int, optional
        Random seed for reproducibility.
    preserve_layers : bool, default=True
        If True, preserve layer labels and structure.
    
    Returns
    -------
    multi_layer_network
        New network with bootstrapped edges.
    
    Notes
    -----
    For undirected networks, each undirected edge is treated as a single
    unit for resampling (not resampled twice as two directed edges).
    
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.uncertainty.resampling_graph import bootstrap_network_edges
    >>> 
    >>> net = multinet.multi_layer_network(directed=False)
    >>> _ = net.add_edges([
    ...     ['A', 'L1', 'B', 'L1', 1],
    ...     ['B', 'L1', 'C', 'L1', 1],
    ... ], input_type='list')
    >>> 
    >>> boot = bootstrap_network_edges(net, seed=42)
    >>> # Some edges may be duplicated, some omitted
    """
    sample, edges = _edge_sample_base(network, bootstrap=True)
    if not edges:
        return sample

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(edges), size=len(edges))
    counts = {}
    for index in draws:
        counts[index] = counts.get(index, 0) + 1
    # Reserve every original key before allocating keys for repeated draws.
    for index in counts:
        _add_sample_edge(sample.core_network, *edges[index])
    for index, count in counts.items():
        source, target, _, attrs = edges[index]
        for _ in range(count - 1):
            _add_sample_edge(sample.core_network, source, target, None, attrs)
    return sample


def _add_sample_edge(graph, source, target, key, attrs):
    if graph.is_multigraph():
        key = graph.add_edge(source, target, key=key)
        graph.edges[source, target, key].update(attrs)
    else:
        graph.add_edge(source, target)
        graph.edges[source, target].update(attrs)


def _edge_sample_base(network, bootstrap=False):
    """Copy all nodes and retain multiplex coupling outside the sampling pool."""
    graph = network.core_network
    sample = multinet.multi_layer_network(
        directed=graph.is_directed() if graph is not None else network.directed,
        network_type=network.network_type,
        coupling_weight=network.coupling_weight,
        dummy_layer=network.dummy_layer,
        label_delimiter=network.label_delimiter,
        verbose=network.verbose,
    )
    if graph is None:
        sample._initiate_network()
        return sample, []

    sample.core_network = nx.create_empty_copy(graph, with_data=True)
    if bootstrap and not graph.is_multigraph():
        graph_type = nx.MultiDiGraph if graph.is_directed() else nx.MultiGraph
        sample.core_network = graph_type(sample.core_network)

    if graph.is_multigraph():
        records = graph.edges(keys=True, data=True)
    else:
        records = ((u, v, None, attrs) for u, v, attrs in graph.edges(data=True))
    edges = []
    for source, target, key, attrs in records:
        if network.network_type == "multiplex" and attrs.get("type") == "coupling":
            _add_sample_edge(sample.core_network, source, target, key, attrs)
        else:
            edges.append((source, target, key, attrs))
    return sample, edges


def resample_network_nodes(
    network: multinet.multi_layer_network,
    *,
    seed: Optional[int] = None,
    preserve_layers: bool = True,
) -> multinet.multi_layer_network:
    """Bootstrap resample network nodes with replacement.
    
    Creates a new network by sampling nodes with replacement, including
    their incident edges. Less commonly used than edge resampling for
    community detection UQ.
    
    **Never modifies the input network** - returns a new copy.
    
    Parameters
    ----------
    network : multi_layer_network
        Input network to resample (will not be modified).
    seed : int, optional
        Random seed for reproducibility.
    preserve_layers : bool, default=True
        If True, preserve layer labels.
    
    Returns
    -------
    multi_layer_network
        New network with bootstrapped nodes and their edges.
    
    Notes
    -----
    This resampling can significantly change network structure and is
    less suitable for community detection than edge resampling.
    
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.uncertainty.resampling_graph import resample_network_nodes
    >>> 
    >>> net = multinet.multi_layer_network(directed=False)
    >>> _ = net.add_edges([
    ...     ['A', 'L1', 'B', 'L1', 1],
    ...     ['B', 'L1', 'C', 'L1', 1],
    ... ], input_type='list')
    >>> 
    >>> boot = resample_network_nodes(net, seed=42)
    """
    # Create RNG
    rng = np.random.default_rng(seed)
    
    # Get all nodes
    nodes = list(network.get_nodes())
    n_nodes = len(nodes)
    
    if n_nodes == 0:
        return multinet.multi_layer_network(directed=network.directed)
    
    # Sample nodes with replacement
    sampled_indices = rng.integers(0, n_nodes, size=n_nodes)
    sampled_nodes = [nodes[i] for i in sampled_indices]
    sampled_node_set = set(sampled_nodes)
    
    # Create new network
    new_net = multinet.multi_layer_network(directed=network.directed)
    
    # Get edges where both endpoints are in sampled set
    edges = list(network.get_edges())
    kept_edges = []
    
    for edge in edges:
        if len(edge) == 2:
            node1, node2 = edge
            if node1 in sampled_node_set and node2 in sampled_node_set:
                (n1, l1), (n2, l2) = node1, node2
                kept_edges.append([n1, l1, n2, l2, 1.0])
    
    # Add edges (which will create nodes)
    if kept_edges:
        new_net.add_edges(kept_edges, input_type='list')
    
    return new_net

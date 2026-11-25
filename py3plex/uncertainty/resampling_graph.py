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

from dataclasses import dataclass
from typing import Any, Optional

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
    return _bootstrap_edges(network, np.random.default_rng(seed))


def _bootstrap_edges(network, rng, pool=None):
    sample, edges = _edge_sample_base(network, bootstrap=True, pool=pool)
    if not edges:
        return sample

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


def _edge_sample_base(network, bootstrap=False, pool=None):
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

    edges, coupling = _edge_pool(network) if pool is None else pool
    for record in coupling:
        _add_sample_edge(sample.core_network, *record)
    return sample, edges


def _edge_pool(network):
    """Separate fixed coupling edges from interactions once per serial run."""
    graph = network.core_network
    if graph is None:
        return [], []
    if graph.is_multigraph():
        records = graph.edges(keys=True, data=True)
    else:
        records = ((u, v, None, attrs) for u, v, attrs in graph.edges(data=True))
    if network.network_type != "multiplex":
        return list(records), []
    edges, coupling = [], []
    for record in records:
        if record[3].get("type") == "coupling":
            coupling.append(record)
        else:
            edges.append(record)
    return edges, coupling


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
    return _bootstrap_units(network, "nodes", np.random.default_rng(seed))


@dataclass(frozen=True)
class _BootstrapReplica:
    original: Any
    occurrence: int


def _bootstrap_units(network, unit, rng):
    """Build an induced bootstrap graph, retaining the multiplicity of draws."""
    sample, _ = _edge_sample_base(network, bootstrap=True)
    graph = network.core_network
    if graph is None or len(graph) == 0:
        return sample

    result = sample.core_network
    result.remove_nodes_from(list(result))
    units = list(graph) if unit == "nodes" else list(dict.fromkeys(node[1] for node in graph))
    counts = dict.fromkeys(units, 0)
    for index in rng.integers(0, len(units), size=len(units)):
        counts[units[index]] += 1

    copies = {}
    for replica, attrs in graph.nodes(data=True):
        physical, layer = replica
        count = counts[replica if unit == "nodes" else layer]
        replicas = [replica] if count else []
        for occurrence in range(1, count):
            if unit == "nodes":
                replicas.append((_BootstrapReplica(replica, occurrence), layer))
            else:
                replicas.append((physical, _BootstrapReplica(layer, occurrence)))
        copies[replica] = replicas
        for copied in replicas:
            result.add_node(copied)
            result.nodes[copied].update(attrs)

    records = (graph.edges(keys=True, data=True) if graph.is_multigraph()
               else ((u, v, None, attrs) for u, v, attrs in graph.edges(data=True)))
    for u, v, key, attrs in records:
        if u == v or (unit == "layers" and u[1] == v[1]):
            pairs = zip(copies[u], copies[v])
        else:
            pairs = ((a, b) for a in copies[u] for b in copies[v])
        for source, target in pairs:
            _add_sample_edge(result, source, target, key, attrs)
    return sample

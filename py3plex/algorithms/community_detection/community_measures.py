"""
Community quality measures and metrics.

This module provides various measures for assessing the quality of community
partitions in networks, including modularity, size distribution, and other
statistical metrics.
"""

from itertools import product
from typing import Any, Dict, List

import networkx as nx
import numpy as np


def modularity(
    G: nx.Graph, communities: Dict[Any, List[Any]], weight: str = "weight"
) -> float:
    """
    Calculate modularity of a graph partition.

    Args:
        G: NetworkX graph
        communities: Dictionary mapping community IDs to node lists
        weight: Edge weight attribute (default: "weight")

    Returns:
        Modularity value
    """

    communities_list: List[List[Any]] = list(communities.values())
    multigraph = G.is_multigraph()
    directed = G.is_directed()
    m = G.size(weight=weight)
    if directed:
        out_degree = dict(G.out_degree(weight=weight))
        in_degree = dict(G.in_degree(weight=weight))
        norm = 1 / m
    else:
        out_degree = dict(G.degree(weight=weight))
        in_degree = out_degree
        norm = 1 / (2 * m)

    def val(u, v):
        try:
            if multigraph:
                w = sum(d.get(weight, 1) for k, d in G[u][v].items())
            else:
                w = G[u][v].get(weight, 1)
        except KeyError:
            w = 0
        # Double count self-loops if the graph is undirected.
        if u == v and not directed:
            w *= 2
        return w - in_degree[u] * out_degree[v] * norm

    Q: float = np.sum(
        [val(u, v) for c in communities_list for u, v in product(c, repeat=2)]
    )
    return float(Q * norm)


def size_distribution(network_partition: Dict[Any, List[Any]]) -> np.ndarray:
    """
    Calculate size distribution of communities.

    Args:
        network_partition: Dictionary mapping community IDs to node lists

    Returns:
        Array of community sizes
    """
    result: np.ndarray = np.array([len(x) for x in network_partition.values()])
    return result


def number_of_communities(network_partition: Dict[Any, List[Any]]) -> int:
    """
    Count number of communities in a partition.

    Args:
        network_partition: Dictionary mapping community IDs to node lists

    Returns:
        Number of communities
    """
    return len(network_partition)

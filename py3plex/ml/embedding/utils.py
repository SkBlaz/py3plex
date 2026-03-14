"""Utilities for embedding backends."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np


NodeId = Any
_EPSILON = 1e-6
_MAX_BIAS_WEIGHT = 1e3


def as_node_layer(node: Any) -> Any:
    """Return canonical node id used by embedding models."""
    return node


def build_graph_from_network(
    network: Any,
    nodes: Optional[Sequence[Any]] = None,
    directed: bool = False,
) -> nx.Graph:
    """Build a NetworkX graph view from a py3plex network."""
    G = nx.DiGraph() if directed else nx.Graph()

    node_set = set(nodes) if nodes is not None else None

    if nodes is not None:
        for n in nodes:
            G.add_node(as_node_layer(n))

    for edge in network.get_edges(data=True):
        if len(edge) < 2:
            continue
        u = as_node_layer(edge[0])
        v = as_node_layer(edge[1])

        if node_set is not None and (u not in node_set or v not in node_set):
            continue

        weight = 1.0
        if len(edge) >= 3 and isinstance(edge[-1], dict):
            weight = float(edge[-1].get("weight", 1.0))
        G.add_edge(u, v, weight=weight)
    return G


def random_walk(
    G: nx.Graph,
    start: Any,
    walk_length: int,
    rng: np.random.Generator,
) -> List[Any]:
    """Generate an unbiased random walk."""
    walk = [start]
    current = start
    for _ in range(max(0, walk_length - 1)):
        neighbors = list(G.neighbors(current))
        if not neighbors:
            break
        current = neighbors[int(rng.integers(0, len(neighbors)))]
        walk.append(current)
    return walk


def node2vec_walk(
    G: nx.Graph,
    start: Any,
    walk_length: int,
    p: float,
    q: float,
    rng: np.random.Generator,
) -> List[Any]:
    """Generate a node2vec-style biased random walk."""
    walk = [start]
    if walk_length <= 1:
        return walk

    neighbors = list(G.neighbors(start))
    if not neighbors:
        return walk
    current = neighbors[int(rng.integers(0, len(neighbors)))]
    walk.append(current)

    def _inv_bias(val: float) -> float:
        return min(1.0 / max(val, _EPSILON), _MAX_BIAS_WEIGHT)

    for _ in range(max(0, walk_length - 2)):
        neigh = list(G.neighbors(current))
        if not neigh:
            break
        prev = walk[-2]

        weights = []
        for dst in neigh:
            if dst == prev:
                weights.append(_inv_bias(p))
            elif G.has_edge(dst, prev) or G.has_edge(prev, dst):
                weights.append(1.0)
            else:
                weights.append(_inv_bias(q))
        probs = np.array(weights, dtype=np.float64)
        probs = probs / probs.sum()
        idx = int(rng.choice(len(neigh), p=probs))
        current = neigh[idx]
        walk.append(current)
    return walk


def cooccurrence_matrix(
    walks: Sequence[Sequence[Any]],
    node_to_idx: Dict[Any, int],
    window_size: int,
) -> np.ndarray:
    """Build a simple co-occurrence matrix from random walks."""
    n = len(node_to_idx)
    mat = np.zeros((n, n), dtype=np.float32)
    for walk in walks:
        for i, node in enumerate(walk):
            if node not in node_to_idx:
                continue
            src = node_to_idx[node]
            left = max(0, i - window_size)
            right = min(len(walk), i + window_size + 1)
            for j in range(left, right):
                if j == i:
                    continue
                other = walk[j]
                if other not in node_to_idx:
                    continue
                dst = node_to_idx[other]
                mat[src, dst] += 1.0
    return mat


def truncated_svd_embedding(matrix: np.ndarray, dim: int) -> np.ndarray:
    """Compute SVD-based embedding from a matrix."""
    if matrix.size == 0:
        return np.empty((0, dim), dtype=np.float32)
    n = matrix.shape[0]
    k = max(1, min(dim, n))
    U, S, _ = np.linalg.svd(matrix, full_matrices=False)
    emb = U[:, :k] * np.sqrt(np.maximum(S[:k], 0.0))
    if k < dim:
        emb = np.pad(emb, ((0, 0), (0, dim - k)))
    return emb.astype(np.float32, copy=False)

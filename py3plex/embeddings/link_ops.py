"""Link feature operators for deriving edge embeddings from node embeddings.

Given a node embedding matrix, these operators combine source and target
node vectors to produce a single vector per edge.

Supported operators
-------------------
``hadamard``    Element-wise product.
``concat``      Concatenation (doubles the dimensionality).
``l1``          Absolute difference.
``l2``          Squared difference.
``dot``         Dot product (scalar, repeated to dim).
``cosine``      Cosine similarity (scalar, repeated to dim).
``avg``         Element-wise average.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base import EmbeddingResult
from py3plex.exceptions import EmbeddingError


def _get_vec(
    node_id: Any, id_to_idx: Dict[Any, int], matrix: np.ndarray
) -> np.ndarray:
    """Retrieve the embedding vector for *node_id*."""
    if node_id not in id_to_idx:
        raise EmbeddingError(
            f"Node '{node_id}' not found in node embedding. "
            "Ensure the edge's source/target node is included in the node query."
        )
    return matrix[id_to_idx[node_id]]


def _hadamard(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return u * v


def _concat(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return np.concatenate([u, v])


def _l1(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return np.abs(u - v)


def _l2(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return (u - v) ** 2


def _avg(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return (u + v) / 2.0


def _dot(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    val = float(np.dot(u, v))
    return np.full(u.shape, val, dtype=u.dtype)


def _cosine(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(u) * np.linalg.norm(v)
    val = float(np.dot(u, v) / max(norm, 1e-12))
    return np.full(u.shape, val, dtype=u.dtype)


# Registry of supported operators
_OP_FUNCS = {
    "hadamard": _hadamard,
    "concat": _concat,
    "l1": _l1,
    "l2": _l2,
    "avg": _avg,
    "dot": _dot,
    "cosine": _cosine,
}

#: Public set of supported link operator names.
LINK_OPS = frozenset(_OP_FUNCS)


def apply_link_op(
    node_embedding: EmbeddingResult,
    edge_ids: List[Tuple[Any, Any, Any, Any]],
    op: str = "hadamard",
) -> EmbeddingResult:
    """Derive edge embeddings from node embeddings using a binary operator.

    Args:
        node_embedding: Node-level EmbeddingResult.
        edge_ids: Ordered list of edge tuples
            ``(src_id, dst_id, src_layer, dst_layer)`` or
            ``(src_id, dst_id)`` pairs.
        op: Operator name.  One of :data:`LINK_OPS`.

    Returns:
        EmbeddingResult aligned to *edge_ids*.

    Raises:
        EmbeddingError: If an unknown operator is requested or a node
            referenced by an edge is missing from the node embedding.
    """
    if op not in _OP_FUNCS:
        raise EmbeddingError(
            f"Unknown link operator '{op}'. "
            f"Supported operators: {sorted(LINK_OPS)}"
        )

    fn = _OP_FUNCS[op]
    id_to_idx: Dict[Any, int] = {
        iid: i for i, iid in enumerate(node_embedding.item_ids)
    }

    rows: List[np.ndarray] = []
    for edge in edge_ids:
        # Support both 2-tuple and 4-tuple edge formats
        if len(edge) >= 4:
            src, dst, src_layer, dst_layer = edge[0], edge[1], edge[2], edge[3]
            src_key: Any = (src, src_layer)
            dst_key: Any = (dst, dst_layer)
        else:
            src, dst = edge[0], edge[1]
            src_key = src
            dst_key = dst

        # Try (id, layer) tuple first, fall back to plain id
        if src_key not in id_to_idx:
            src_key = src
        if dst_key not in id_to_idx:
            dst_key = dst

        u = _get_vec(src_key, id_to_idx, node_embedding.matrix)
        v = _get_vec(dst_key, id_to_idx, node_embedding.matrix)
        rows.append(fn(u, v))

    if rows:
        matrix = np.stack(rows, axis=0).astype(np.float32)
    else:
        # Empty edge set
        sample_dim = node_embedding.dim if op != "concat" else node_embedding.dim * 2
        matrix = np.empty((0, sample_dim), dtype=np.float32)

    return EmbeddingResult(
        matrix=matrix,
        item_ids=list(edge_ids),
        method=f"link:{op}",
        meta={
            "op": op,
            "source_method": node_embedding.method,
            "source_dim": node_embedding.dim,
        },
    )

"""NetMF node embedding implementation.

Reference:
    Qiu et al. (2018) "Network Embedding as Matrix Factorization:
    Unifying DeepWalk, LINE, PTE, and node2vec".
    https://arxiv.org/abs/1710.02971

The implementation follows the large-scale variant that avoids forming the
full |V|×|V| matrix by applying randomised or eigen-based SVD directly on a
normalised sparse representation of the PMI matrix.

Multilayer modes
----------------
``union``
    Merge all selected layers into a single undirected graph whose node
    set is the set of unique *physical* node ids (the first element of
    each ``(node_id, layer)`` tuple).  Parallel edges are summed.
``supra``
    Treat each ``(node_id, layer)`` pair as a distinct supra-node.  Add
    coupling edges of weight *gamma* between the same physical node across
    layers (identity coupling).  All intra-layer edges are preserved.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

from .base import EmbeddingResult
from py3plex.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graph construction helpers
# ---------------------------------------------------------------------------


def _build_union_adjacency(
    network: Any,
    node_ids: List[Any],
) -> Tuple[sp.csr_matrix, List[Any]]:
    """Build a sparse adjacency for the *union* multilayer mode.

    Physical node id is the first element of a ``(id, layer)`` tuple, or
    the id itself for single-layer networks.

    Args:
        network: py3plex network object.
        node_ids: List of ``(node_id, layer)`` tuples or plain node ids.

    Returns:
        Tuple of (adjacency csr_matrix, list of physical node ids).
    """
    # Determine physical ids
    def _phys(nid: Any) -> Any:
        return nid[0] if isinstance(nid, tuple) else nid

    phys_nodes: List[Any] = list(dict.fromkeys(_phys(n) for n in node_ids))
    phys_index: Dict[Any, int] = {n: i for i, n in enumerate(phys_nodes)}
    n = len(phys_nodes)

    rows: List[int] = []
    cols: List[int] = []
    data_vals: List[float] = []

    # Map query node_ids to physical index set (for filtering edges)
    query_phys: Set[Any] = set(phys_nodes)

    try:
        raw_edges = list(network.get_edges())
    except Exception as exc:  # noqa: BLE001
        raise EmbeddingError(f"Failed to retrieve edges from network: {exc}") from exc

    for edge in raw_edges:
        # Edge may be (src, dst, src_layer, dst_layer) or (src, dst, src_layer, dst_layer, weight)
        if len(edge) >= 4:
            src_id, dst_id = edge[0], edge[1]
        elif len(edge) == 2:
            src_id, dst_id = edge[0], edge[1]
        else:
            continue

        ps = _phys(src_id) if not isinstance(src_id, tuple) else src_id[0]
        pd = _phys(dst_id) if not isinstance(dst_id, tuple) else dst_id[0]

        if ps not in query_phys or pd not in query_phys:
            continue

        weight = float(edge[4]) if len(edge) >= 5 and edge[4] is not None else 1.0
        i, j = phys_index[ps], phys_index[pd]
        rows.append(i)
        cols.append(j)
        data_vals.append(weight)
        if i != j:
            rows.append(j)
            cols.append(i)
            data_vals.append(weight)

    adj = sp.csr_matrix(
        (data_vals, (rows, cols)), shape=(n, n), dtype=np.float32
    )
    return adj, phys_nodes


def _build_supra_adjacency(
    network: Any,
    node_ids: List[Any],
    gamma: float = 1.0,
) -> Tuple[sp.csr_matrix, List[Any]]:
    """Build a sparse adjacency for the *supra* multilayer mode.

    Each ``(node_id, layer)`` tuple becomes a distinct supra-node.  Coupling
    edges of weight *gamma* are added between the same physical node across
    layers.

    Args:
        network: py3plex network object.
        node_ids: List of ``(node_id, layer)`` tuples.
        gamma: Interlayer coupling weight.

    Returns:
        Tuple of (adjacency csr_matrix, ordered list of supra-node ids).
    """
    supra_nodes: List[Any] = list(dict.fromkeys(node_ids))
    supra_index: Dict[Any, int] = {n: i for i, n in enumerate(supra_nodes)}
    n = len(supra_nodes)
    query_set: Set[Any] = set(supra_nodes)

    rows: List[int] = []
    cols: List[int] = []
    data_vals: List[float] = []

    # Intra-layer edges
    try:
        raw_edges = list(network.get_edges())
    except Exception as exc:  # noqa: BLE001
        raise EmbeddingError(f"Failed to retrieve edges from network: {exc}") from exc

    for edge in raw_edges:
        if len(edge) >= 4:
            src_id, dst_id, src_layer, dst_layer = edge[0], edge[1], edge[2], edge[3]
        else:
            continue

        src_supra = (src_id, src_layer)
        dst_supra = (dst_id, dst_layer)

        if src_supra not in query_set or dst_supra not in query_set:
            continue

        weight = float(edge[4]) if len(edge) >= 5 and edge[4] is not None else 1.0
        i, j = supra_index[src_supra], supra_index[dst_supra]
        rows.append(i)
        cols.append(j)
        data_vals.append(weight)
        if i != j:
            rows.append(j)
            cols.append(i)
            data_vals.append(weight)

    # Coupling edges (identity coupling across layers)
    from collections import defaultdict

    phys_to_supra: Dict[Any, List[Any]] = defaultdict(list)
    for sn in supra_nodes:
        if isinstance(sn, tuple):
            phys_to_supra[sn[0]].append(sn)
        else:
            phys_to_supra[sn].append(sn)

    for phys, replicas in phys_to_supra.items():
        for a in range(len(replicas)):
            for b in range(a + 1, len(replicas)):
                i = supra_index[replicas[a]]
                j = supra_index[replicas[b]]
                rows.extend([i, j])
                cols.extend([j, i])
                data_vals.extend([gamma, gamma])

    adj = sp.csr_matrix(
        (data_vals, (rows, cols)), shape=(n, n), dtype=np.float32
    )
    return adj, supra_nodes


# ---------------------------------------------------------------------------
# NetMF core
# ---------------------------------------------------------------------------


def _netmf_embed(
    adj: sp.spmatrix,
    *,
    dim: int,
    window: int,
    negative: float,
    approx: str,
    seed: Optional[int],
) -> np.ndarray:
    """Compute NetMF embeddings from a sparse adjacency matrix.

    Args:
        adj: Symmetric sparse adjacency (n×n).
        dim: Embedding dimensionality.
        window: Context window size T for random-walk PMI.
        negative: Negative sampling noise ratio (b in the paper).
        approx: Approximation method: "randomized_svd" | "eigsh".
        seed: Random seed for reproducibility.

    Returns:
        Embedding matrix of shape (n, dim).
    """
    rng = np.random.default_rng(seed)
    n = adj.shape[0]

    if n < 2:
        raise EmbeddingError(
            f"Network has only {n} node(s) in the selected subgraph; "
            "cannot compute embeddings.  Use a larger network or relax filters."
        )

    # Row-normalise to obtain transition matrix P
    deg = np.asarray(adj.sum(axis=1)).ravel()
    deg_safe = np.where(deg == 0, 1.0, deg)
    d_inv = sp.diags(1.0 / deg_safe)
    P = d_inv.dot(adj)  # row-stochastic

    # Compute sum_{r=1}^{T} P^r (DeepWalk PMI approximation)
    vol = float(adj.sum())
    PT_sum = P.copy()
    Pk = P.copy()
    for _ in range(1, window):
        Pk = Pk.dot(P)
        PT_sum = PT_sum + Pk

    PT_sum = PT_sum / window

    # M = (vol / (negative * T)) * D * PT_sum
    # where D is the degree diagonal; we work with the normalised version.
    scale = vol / max(negative, 1e-12)
    # M_ij = scale * (d_i / vol) * PT_sum_ij
    #       = scale * PT_sum_ij / deg_safe_i  (already divided by deg in P)
    # Full PMI_ij = log(M_ij); clamp negatives to 0 (PPMI)
    M_dense: np.ndarray = np.asarray(PT_sum.todense()) * scale

    # Log + PPMI
    with np.errstate(divide="ignore", invalid="ignore"):
        log_M = np.log(np.maximum(M_dense, 1e-30))
    log_M = np.maximum(log_M, 0.0)  # PPMI clamp

    # Symmetric so use real symmetric decomposition
    if approx == "randomized_svd":
        try:
            from sklearn.utils.extmath import randomized_svd  # type: ignore

            U, s, _ = randomized_svd(
                log_M,
                n_components=dim,
                random_state=int(rng.integers(0, 2**31)),
            )
        except ImportError:
            logger.warning(
                "scikit-learn not available; falling back to eigsh for SVD."
            )
            approx = "eigsh"

    if approx == "eigsh":
        k = min(dim, n - 2)
        if k < 1:
            raise EmbeddingError(
                f"Requested dim={dim} too large for network of size {n}."
            )
        # eigsh on symmetric PPMI matrix
        sym_M = (log_M + log_M.T) / 2.0
        eigenvalues, U = eigsh(sp.csr_matrix(sym_M), k=k)
        # Sort by descending eigenvalue magnitude
        order = np.argsort(-np.abs(eigenvalues))
        eigenvalues = eigenvalues[order]
        U = U[:, order]
        s = np.sqrt(np.abs(eigenvalues))

    # Embedding: U * sqrt(S)
    embeddings = U[:, :dim] * np.sqrt(np.maximum(s[:dim], 0.0))
    return embeddings.astype(np.float32)


# ---------------------------------------------------------------------------
# Public embedder class
# ---------------------------------------------------------------------------


class NetMFEmbedder:
    """NetMF node embedder.

    Attributes:
        dim: Embedding dimensionality.
        multilayer: Multilayer mode ("union" | "supra").
        window: Context window size.
        negative: Negative sampling ratio.
        approx: Approximation method ("randomized_svd" | "eigsh").
        gamma: Interlayer coupling weight (supra mode only).
        seed: Random seed for reproducibility.
    """

    def __init__(
        self,
        *,
        dim: int = 128,
        multilayer: str = "supra",
        window: int = 10,
        negative: float = 1.0,
        approx: str = "randomized_svd",
        gamma: float = 1.0,
        seed: Optional[int] = None,
    ) -> None:
        """Initialise NetMFEmbedder.

        Args:
            dim: Embedding dimensionality.
            multilayer: Multilayer mode ("union" | "supra").
            window: Random-walk window size T.
            negative: Negative sampling noise ratio b.
            approx: SVD approximation ("randomized_svd" | "eigsh").
            gamma: Interlayer coupling weight for supra mode.
            seed: Random seed.
        """
        if multilayer not in ("union", "supra"):
            raise NotImplementedError(
                f"multilayer='{multilayer}' is not supported. "
                "Supported modes: 'union', 'supra'. "
                "'per_layer' and 'rw_coupled' are not yet implemented."
            )
        self.dim = dim
        self.multilayer = multilayer
        self.window = window
        self.negative = negative
        self.approx = approx
        self.gamma = gamma
        self.seed = seed

    # ------------------------------------------------------------------
    def fit_transform(
        self,
        network: Any,
        *,
        item_ids: List[Any],
        dim: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> EmbeddingResult:
        """Compute NetMF embeddings for the given node ids.

        Args:
            network: py3plex network object with ``get_edges()`` method.
            item_ids: Ordered list of ``(node_id, layer)`` tuples to embed.
            dim: Override dimensionality (falls back to ``self.dim``).
            seed: Override random seed.

        Returns:
            EmbeddingResult aligned to *item_ids*.
        """
        _dim = dim if dim is not None else self.dim
        _seed = seed if seed is not None else self.seed

        if not item_ids:
            raise EmbeddingError("Cannot embed an empty item set.")

        if self.multilayer == "union":
            adj, ordered_ids = _build_union_adjacency(network, item_ids)
        else:  # supra
            adj, ordered_ids = _build_supra_adjacency(
                network, item_ids, gamma=self.gamma
            )

        logger.debug(
            "NetMF: n=%d, dim=%d, window=%d, approx=%s, mode=%s",
            adj.shape[0],
            _dim,
            self.window,
            self.approx,
            self.multilayer,
        )

        matrix = _netmf_embed(
            adj,
            dim=_dim,
            window=self.window,
            negative=self.negative,
            approx=self.approx,
            seed=_seed,
        )

        result = EmbeddingResult(
            matrix=matrix,
            item_ids=ordered_ids,
            method="netmf",
            meta={
                "multilayer_mode": self.multilayer,
                "dim": _dim,
                "window": self.window,
                "negative": self.negative,
                "approx": self.approx,
                "gamma": self.gamma,
                "seed": _seed,
            },
        )

        # Re-order to match requested item_ids (supra keeps them; union may differ)
        if ordered_ids != item_ids:
            # Best-effort reorder; items not in ordered_ids are skipped
            available = set(ordered_ids)
            requested = [iid for iid in item_ids if iid in available]
            if requested:
                result = result.reorder(requested)

        return result

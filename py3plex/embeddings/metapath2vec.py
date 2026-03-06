"""MetaPath2Vec embedding for heterogeneous/multilayer networks.

Implements metapath-constrained random walks followed by skip-gram training
with negative sampling using a pure-NumPy backend (no mandatory heavy deps).

Reference:
    Dong et al. (2017) "metapath2vec: Scalable Representation Learning for
    Heterogeneous Networks". KDD 2017.

Usage::

    from py3plex.embeddings.metapath2vec import MetaPath2VecEmbedder

    embedder = MetaPath2VecEmbedder(
        metapaths=[["author", "paper", "author"]],
        dim=64,
        walk_length=40,
        num_walks=5,
        seed=42,
    )
    result = embedder.fit_transform(network, item_ids=net.get_nodes())
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base import EmbeddingResult
from py3plex.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _node_token(node_id: Any) -> str:
    """Convert a node id (possibly a tuple) to a stable string token.

    Args:
        node_id: Either a ``(physical_id, layer)`` tuple or a plain id.

    Returns:
        A string like ``"Alice|social"`` or ``"Alice"``.
    """
    if isinstance(node_id, tuple) and len(node_id) == 2:
        return f"{node_id[0]}|{node_id[1]}"
    return str(node_id)


def _node_layer(node_id: Any) -> Optional[str]:
    """Extract the layer part of a node id, or ``None`` for plain ids.

    Args:
        node_id: Either a ``(physical_id, layer)`` tuple or a plain id.

    Returns:
        Layer string or ``None``.
    """
    if isinstance(node_id, tuple) and len(node_id) == 2:
        return str(node_id[1])
    return None


# ---------------------------------------------------------------------------
# Transition index
# ---------------------------------------------------------------------------


def _build_transition_index(
    network: Any,
    metapath: List[str],
) -> Dict[Tuple[Any, str], List[Any]]:
    """Precompute allowed next-step neighbors for each metapath transition.

    For each ``(node, current_layer)`` pair at step ``t``, the transition
    index stores which neighbors have the layer expected at step ``t+1``.

    Args:
        network: A py3plex ``multi_layer_network`` instance.
        metapath: Ordered list of layer names forming the metapath.

    Returns:
        Dict mapping ``(node_id, next_layer)`` to list of neighbor node ids.
        Only ``(node_id, layer)`` tuples whose layer is in the metapath are
        indexed.
    """
    try:
        raw_edges = list(network.get_edges())
    except Exception as exc:
        raise EmbeddingError(
            f"Failed to retrieve edges from network: {exc}"
        ) from exc

    # Directed flag
    directed = getattr(network, "directed", False)

    # index[node_id][target_layer] -> list of neighbor nodes (tuples or plain)
    index: Dict[Any, Dict[str, List[Any]]] = {}
    metapath_layers = set(metapath)

    for edge in raw_edges:
        # Support two edge formats:
        #   1. py3plex native: ((src_id, src_layer), (dst_id, dst_layer))
        #   2. flat 4-tuple:   (src_id, dst_id, src_layer, dst_layer[, weight])
        if (
            len(edge) == 2
            and isinstance(edge[0], tuple)
            and isinstance(edge[1], tuple)
        ):
            src_tuple, dst_tuple = edge[0], edge[1]
            if len(src_tuple) < 2 or len(dst_tuple) < 2:
                continue
            src, src_layer = src_tuple[0], str(src_tuple[1])
            dst, dst_layer = dst_tuple[0], str(dst_tuple[1])
            # Normalise to (id, str_layer) so later comparisons are consistent
            src_tuple = (src, src_layer)
            dst_tuple = (dst, dst_layer)  # layers from nested tuples may not be str yet
        elif len(edge) >= 4:
            src, dst, src_layer, dst_layer = edge[0], edge[1], edge[2], edge[3]
            src_layer, dst_layer = str(src_layer), str(dst_layer)
            src_tuple = (src, src_layer)
            dst_tuple = (dst, dst_layer)
        else:
            continue
        # Only index layers that appear in at least one metapath

        if src_layer in metapath_layers and dst_layer in metapath_layers:
            # Forward: src -> dst
            if src_tuple not in index:
                index[src_tuple] = {}
            if dst_layer not in index[src_tuple]:
                index[src_tuple][dst_layer] = []
            index[src_tuple][dst_layer].append(dst_tuple)

            if not directed:
                # Reverse: dst -> src
                if dst_tuple not in index:
                    index[dst_tuple] = {}
                if src_layer not in index[dst_tuple]:
                    index[dst_tuple][src_layer] = []
                index[dst_tuple][src_layer].append(src_tuple)

    return index


# ---------------------------------------------------------------------------
# Walk generation
# ---------------------------------------------------------------------------


def _generate_walks(
    nodes: List[Any],
    metapath: List[str],
    transition_index: Dict[Any, Dict[str, List[Any]]],
    walk_length: int,
    num_walks: int,
    rng: np.random.Generator,
) -> List[List[str]]:
    """Generate metapath-constrained random walks.

    Args:
        nodes: Start-node candidates (``(node_id, layer)`` tuples).
        metapath: Ordered layer sequence for constraining transitions.
        transition_index: Precomputed neighbor index from
            :func:`_build_transition_index`.
        walk_length: Maximum number of steps per walk.
        num_walks: Number of walks per start node.
        rng: NumPy random generator for reproducibility.

    Returns:
        List of walks; each walk is a list of string tokens.
    """
    mp_len = len(metapath)
    walks: List[List[str]] = []

    # Filter start nodes to those whose layer matches the first metapath step
    start_layer = metapath[0]
    valid_starts = [n for n in nodes if _node_layer(n) == start_layer]

    if not valid_starts:
        logger.warning(
            "No start nodes found for metapath starting with layer '%s'. "
            "Check metapath definition and network layers.",
            start_layer,
        )
        return walks

    for _ in range(num_walks):
        # Shuffle start-node order for each walk pass
        order = rng.permutation(len(valid_starts))
        for idx in order:
            current = valid_starts[int(idx)]
            walk: List[str] = [_node_token(current)]
            step = 1  # we've consumed position 0 of the metapath

            for _ in range(walk_length - 1):
                next_layer = metapath[step % mp_len]
                neighbors_by_layer = transition_index.get(current, {})
                candidates = neighbors_by_layer.get(next_layer, [])
                if not candidates:
                    break  # dead end – terminate walk early
                # Sample uniformly
                chosen_idx = int(rng.integers(0, len(candidates)))
                current = candidates[chosen_idx]
                walk.append(_node_token(current))
                step += 1

            if len(walk) >= 2:
                walks.append(walk)

    return walks


# ---------------------------------------------------------------------------
# Vocabulary + negative sampling distribution
# ---------------------------------------------------------------------------


def _build_vocabulary(
    walks: List[List[str]],
    min_count: int = 1,
    subsampling: Optional[float] = None,
) -> Tuple[Dict[str, int], List[str], np.ndarray]:
    """Build vocabulary and negative-sampling distribution.

    Args:
        walks: List of tokenised walks.
        min_count: Minimum token frequency to include in vocabulary.
        subsampling: If set, the threshold *t* for subsampling frequent
            tokens.  Tokens with frequency ``f > t`` are downsampled
            with probability ``1 - sqrt(t/f)``.

    Returns:
        Tuple of ``(token_to_idx, idx_to_token, neg_dist)`` where
        ``neg_dist`` is a probability vector for negative sampling
        (unigram^0.75, normalised).
    """
    counts: Dict[str, int] = {}
    for walk in walks:
        for token in walk:
            counts[token] = counts.get(token, 0) + 1

    # Filter by min_count
    vocab_tokens = sorted(t for t, c in counts.items() if c >= min_count)
    if not vocab_tokens:
        raise EmbeddingError(
            "Empty vocabulary after min_count filtering. "
            "Consider lowering min_count or increasing num_walks/walk_length."
        )

    token_to_idx: Dict[str, int] = {t: i for i, t in enumerate(vocab_tokens)}
    freq = np.array([counts[t] for t in vocab_tokens], dtype=np.float32)

    # Unigram^0.75 negative-sampling distribution
    neg_dist = freq ** 0.75
    neg_dist /= neg_dist.sum()

    return token_to_idx, vocab_tokens, neg_dist


# ---------------------------------------------------------------------------
# Skip-gram training (pure NumPy)
# ---------------------------------------------------------------------------


def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid."""
    pos = x >= 0
    result = np.empty_like(x)
    result[pos] = 1.0 / (1.0 + np.exp(-x[pos]))
    exp_x = np.exp(x[~pos])
    result[~pos] = exp_x / (1.0 + exp_x)
    return result


def _skipgram_train(
    walks: List[List[str]],
    token_to_idx: Dict[str, int],
    neg_dist: np.ndarray,
    vocab_size: int,
    dim: int,
    window_size: int,
    negative_samples: int,
    epochs: int,
    lr: float,
    rng: np.random.Generator,
    min_count: int = 1,
    subsampling: Optional[float] = None,
) -> np.ndarray:
    """Train skip-gram with negative sampling using NumPy SGD.

    Args:
        walks: Tokenised walk corpus.
        token_to_idx: Vocabulary mapping.
        neg_dist: Probability distribution for negative sampling.
        vocab_size: Size of vocabulary.
        dim: Embedding dimensionality.
        window_size: Context window radius.
        negative_samples: Number of negative samples per positive pair.
        epochs: Training epochs.
        lr: Initial learning rate.
        rng: Reproducible NumPy generator.
        min_count: Minimum frequency (used for reference only here).
        subsampling: Subsampling threshold for frequent tokens.

    Returns:
        W_in array of shape ``(vocab_size, dim)`` – the final embeddings.
    """
    # Initialise embeddings
    W_in = (rng.standard_normal((vocab_size, dim)) / dim).astype(np.float32)
    W_out = np.zeros((vocab_size, dim), dtype=np.float32)

    # Pre-compute subsampling keep probabilities
    total_tokens = neg_dist.sum()  # already normalised, so sum=1
    # Recompute from neg_dist^(1/0.75) to get original proportions
    # (approximate; good enough for subsampling)
    if subsampling is not None:
        freq_est = neg_dist ** (1.0 / 0.75)
        freq_est /= freq_est.sum()
        keep_prob = np.minimum(1.0, np.sqrt(subsampling / np.maximum(freq_est, 1e-12)))
    else:
        keep_prob = None

    for epoch in range(epochs):
        current_lr = lr * (1.0 - epoch / (epochs + 1))
        current_lr = max(current_lr, lr * 0.0001)

        for walk in walks:
            # Convert tokens to indices, optionally applying subsampling
            indices: List[int] = []
            for token in walk:
                idx = token_to_idx.get(token)
                if idx is None:
                    continue
                if keep_prob is not None and rng.random() > keep_prob[idx]:
                    continue
                indices.append(idx)

            n = len(indices)
            if n < 2:
                continue

            for pos, center_idx in enumerate(indices):
                # Context window
                w_start = max(0, pos - window_size)
                w_end = min(n, pos + window_size + 1)

                for ctx_pos in range(w_start, w_end):
                    if ctx_pos == pos:
                        continue
                    context_idx = indices[ctx_pos]

                    # Positive pair
                    score = np.dot(W_in[center_idx], W_out[context_idx])
                    grad = (1.0 - _sigmoid(np.float32(score))) * current_lr

                    # Negative samples
                    neg_indices = rng.choice(
                        vocab_size, size=negative_samples, p=neg_dist
                    )

                    # Accumulate gradient for W_in[center_idx]
                    grad_in = grad * W_out[context_idx]
                    # Update W_out[context_idx] (positive)
                    W_out[context_idx] += grad * W_in[center_idx]

                    for neg_idx in neg_indices:
                        neg_score = np.dot(W_in[center_idx], W_out[neg_idx])
                        neg_grad = (0.0 - _sigmoid(np.float32(neg_score))) * current_lr
                        grad_in += neg_grad * W_out[neg_idx]
                        W_out[neg_idx] += neg_grad * W_in[center_idx]

                    W_in[center_idx] += grad_in

    return W_in


# ---------------------------------------------------------------------------
# Public embedder class
# ---------------------------------------------------------------------------


class MetaPath2VecEmbedder:
    """MetaPath2Vec embedder for py3plex multilayer networks.

    Generates metapath-constrained random walks and trains skip-gram
    embeddings using a deterministic pure-NumPy backend.

    Args:
        metapaths: List of metapath layer sequences, e.g.
            ``[["author", "paper", "author"]]``.
        dim: Embedding dimensionality.
        walk_length: Maximum steps per walk.
        num_walks: Number of walks per start node.
        window_size: Skip-gram context window radius.
        negative_samples: Number of negative samples per positive pair.
        epochs: Training epochs.
        lr: Initial learning rate (linearly decayed to ``lr * 0.0001``).
        min_count: Minimum token frequency to include in vocabulary.
        subsampling: Subsampling threshold *t* for frequent tokens.
            Set to ``None`` (default) to disable.
        normalize: If ``True``, L2-normalise output embeddings.
        seed: Random seed for reproducibility.
    """

    def __init__(
        self,
        metapaths: Optional[List[List[str]]] = None,
        dim: int = 128,
        walk_length: int = 80,
        num_walks: int = 10,
        window_size: int = 5,
        negative_samples: int = 5,
        epochs: int = 5,
        lr: float = 0.025,
        min_count: int = 1,
        subsampling: Optional[float] = None,
        normalize: bool = True,
        seed: Optional[int] = None,
    ) -> None:
        if metapaths is None:
            metapaths = []
        if not metapaths:
            raise EmbeddingError(
                "At least one metapath must be provided. "
                "Example: metapaths=[['author', 'paper', 'author']]"
            )
        for mp in metapaths:
            if len(mp) < 2:
                raise EmbeddingError(
                    f"Metapath must have at least 2 layers, got: {mp}"
                )
        self.metapaths = metapaths
        self.dim = dim
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.window_size = window_size
        self.negative_samples = negative_samples
        self.epochs = epochs
        self.lr = lr
        self.min_count = min_count
        self.subsampling = subsampling
        self.normalize = normalize
        self.seed = seed

    def fit_transform(
        self,
        network: Any,
        *,
        item_ids: Optional[List[Any]] = None,
        dim: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> EmbeddingResult:
        """Compute MetaPath2Vec embeddings on *network*.

        Args:
            network: A py3plex ``multi_layer_network`` instance.
            item_ids: Optional list of ``(node_id, layer)`` tuples to embed.
                Defaults to all nodes in the network.
            dim: Override embedding dimensionality (default: ``self.dim``).
            seed: Override random seed (default: ``self.seed``).

        Returns:
            :class:`~py3plex.embeddings.base.EmbeddingResult` with one row
            per node.

        Raises:
            EmbeddingError: On invalid metapaths, empty vocabulary, or
                training failures.
        """
        t_start = _time.perf_counter()

        _dim = dim if dim is not None else self.dim
        _seed = seed if seed is not None else self.seed
        rng = np.random.default_rng(_seed)

        # Resolve item_ids – always materialize to a list so len() works
        if item_ids is None:
            try:
                item_ids = list(network.get_nodes())
            except Exception as exc:
                raise EmbeddingError(
                    f"Failed to retrieve nodes from network: {exc}"
                ) from exc

        # Ensure item_ids is a list (caller may pass a generator/iterator)
        if not isinstance(item_ids, list):
            item_ids = list(item_ids)

        if not item_ids:
            raise EmbeddingError("No nodes available for embedding.")

        all_walks: List[List[str]] = []
        t_walks_start = _time.perf_counter()

        for metapath in self.metapaths:
            # Validate all metapath layers exist in network
            try:
                net_layers = set(network.get_layers())
            except Exception:
                net_layers = set()
            if net_layers:
                missing = [l for l in metapath if l not in net_layers]
                if missing:
                    raise EmbeddingError(
                        f"Metapath references unknown layers: {missing}. "
                        f"Available layers: {sorted(net_layers)}"
                    )

            trans_index = _build_transition_index(network, metapath)
            mp_walks = _generate_walks(
                nodes=item_ids,
                metapath=metapath,
                transition_index=trans_index,
                walk_length=self.walk_length,
                num_walks=self.num_walks,
                rng=rng,
            )
            all_walks.extend(mp_walks)

        walks_ms = (_time.perf_counter() - t_walks_start) * 1000.0
        logger.debug("MetaPath2Vec: generated %d walks in %.1f ms", len(all_walks), walks_ms)

        if not all_walks:
            raise EmbeddingError(
                "No valid walks generated. Check that metapath layers "
                "are connected in the network and that start nodes exist."
            )

        # Build vocabulary
        try:
            token_to_idx, idx_to_token, neg_dist = _build_vocabulary(
                all_walks,
                min_count=self.min_count,
                subsampling=self.subsampling,
            )
        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError(f"Vocabulary construction failed: {exc}") from exc

        vocab_size = len(idx_to_token)
        logger.debug("MetaPath2Vec: vocabulary size = %d", vocab_size)

        # Train skip-gram
        t_train_start = _time.perf_counter()
        try:
            W_in = _skipgram_train(
                walks=all_walks,
                token_to_idx=token_to_idx,
                neg_dist=neg_dist,
                vocab_size=vocab_size,
                dim=_dim,
                window_size=self.window_size,
                negative_samples=self.negative_samples,
                epochs=self.epochs,
                lr=self.lr,
                rng=rng,
                min_count=self.min_count,
                subsampling=self.subsampling,
            )
        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError(f"Skip-gram training failed: {exc}") from exc

        train_ms = (_time.perf_counter() - t_train_start) * 1000.0
        logger.debug("MetaPath2Vec: training completed in %.1f ms", train_ms)

        # Optionally L2-normalise
        if self.normalize:
            norms = np.linalg.norm(W_in, axis=1, keepdims=True)
            norms = np.where(norms < 1e-12, 1.0, norms)
            W_in = W_in / norms

        # Map item_ids to matrix rows; items missing from vocab get zeros
        token_set = set(token_to_idx.keys())
        matrix = np.zeros((len(item_ids), _dim), dtype=np.float32)
        for i, node_id in enumerate(item_ids):
            tok = _node_token(node_id)
            if tok in token_to_idx:
                matrix[i] = W_in[token_to_idx[tok]]

        total_ms = (_time.perf_counter() - t_start) * 1000.0
        return EmbeddingResult(
            matrix=matrix,
            item_ids=list(item_ids),
            method="metapath2vec",
            meta={
                "metapaths": self.metapaths,
                "dim": _dim,
                "walk_length": self.walk_length,
                "num_walks": self.num_walks,
                "window_size": self.window_size,
                "negative_samples": self.negative_samples,
                "epochs": self.epochs,
                "lr": self.lr,
                "min_count": self.min_count,
                "subsampling": self.subsampling,
                "normalize": self.normalize,
                "seed": _seed,
                "n_walks": len(all_walks),
                "vocab_size": vocab_size,
                "walks_ms": walks_ms,
                "train_ms": train_ms,
                "total_ms": total_ms,
            },
        )

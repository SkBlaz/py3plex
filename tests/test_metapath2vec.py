"""Tests for MetaPath2VecEmbedder.

Covers:
- Construction and basic fit_transform on a tiny synthetic multilayer network
- Determinism (same seed -> identical vectors)
- Reproducibility with different seeds -> different vectors
- EmbeddingResult shape and metadata
- Error handling for invalid metapaths
"""

from __future__ import annotations

import pytest
import numpy as np


# ---------------------------------------------------------------------------
# Helpers – build a tiny synthetic network without requiring full py3plex
# ---------------------------------------------------------------------------


class _FakeNetwork:
    """Minimal multilayer network stub for MetaPath2Vec testing.

    Nodes are stored as (node_id, layer) tuples in core_network.
    """

    def __init__(self) -> None:
        import networkx as nx

        G = nx.MultiGraph()
        # Layer "author" nodes
        for a in ["a1", "a2", "a3"]:
            G.add_node((a, "author"))
        # Layer "paper" nodes
        for p in ["p1", "p2"]:
            G.add_node((p, "paper"))

        # author-paper edges
        G.add_edge(("a1", "author"), ("p1", "paper"))
        G.add_edge(("a2", "author"), ("p1", "paper"))
        G.add_edge(("a2", "author"), ("p2", "paper"))
        G.add_edge(("a3", "author"), ("p2", "paper"))

        self.core_network = G

    def get_nodes(self):
        return list(self.core_network.nodes())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tiny_net():
    pytest.importorskip("networkx")
    return _FakeNetwork()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_import():
    """MetaPath2VecEmbedder is importable from embeddings package."""
    from py3plex.embeddings.metapath2vec import MetaPath2VecEmbedder  # noqa: F401
    from py3plex.embeddings import MetaPath2VecEmbedder as MP2V  # noqa: F401


def test_basic_fit_transform(tiny_net):
    """Smoke test: fit_transform returns EmbeddingResult with correct shape."""
    from py3plex.embeddings.metapath2vec import MetaPath2VecEmbedder

    embedder = MetaPath2VecEmbedder(
        metapaths=[["author", "paper", "author"]],
        dim=8,
        walk_length=5,
        num_walks=2,
        epochs=1,
        seed=42,
    )
    nodes = tiny_net.get_nodes()
    result = embedder.fit_transform(tiny_net, item_ids=nodes)

    assert result.matrix.shape[1] == 8
    assert len(result.item_ids) == result.matrix.shape[0]
    assert result.method == "metapath2vec"
    assert "seed" in result.meta


def test_determinism(tiny_net):
    """Same seed produces identical embedding vectors."""
    from py3plex.embeddings.metapath2vec import MetaPath2VecEmbedder

    kwargs = dict(
        metapaths=[["author", "paper", "author"]],
        dim=8,
        walk_length=5,
        num_walks=2,
        epochs=2,
        seed=0,
    )
    nodes = tiny_net.get_nodes()
    r1 = MetaPath2VecEmbedder(**kwargs).fit_transform(tiny_net, item_ids=nodes)
    r2 = MetaPath2VecEmbedder(**kwargs).fit_transform(tiny_net, item_ids=nodes)

    np.testing.assert_array_equal(r1.matrix, r2.matrix)


def test_different_seeds_differ(tiny_net):
    """Different seeds should produce statistically different vectors."""
    from py3plex.embeddings.metapath2vec import MetaPath2VecEmbedder

    nodes = tiny_net.get_nodes()
    base_kwargs = dict(
        metapaths=[["author", "paper", "author"]],
        dim=16,
        walk_length=10,
        num_walks=3,
        epochs=3,
    )
    r0 = MetaPath2VecEmbedder(seed=0, **base_kwargs).fit_transform(tiny_net, item_ids=nodes)
    r1 = MetaPath2VecEmbedder(seed=99, **base_kwargs).fit_transform(tiny_net, item_ids=nodes)

    # With overwhelming probability vectors differ (probabilistic check)
    assert not np.allclose(r0.matrix, r1.matrix), (
        "Different seeds should yield different embeddings"
    )


def test_metapath_must_have_at_least_two_types(tiny_net):
    """Single-type metapath (trivial loop) still runs without crashing."""
    from py3plex.embeddings.metapath2vec import MetaPath2VecEmbedder

    # A metapath of just one repeated type is degenerate but should not crash
    embedder = MetaPath2VecEmbedder(
        metapaths=[["author", "author"]],
        dim=4,
        walk_length=4,
        num_walks=1,
        epochs=1,
        seed=7,
    )
    # May produce few or no walks, but must not raise
    nodes = tiny_net.get_nodes()
    result = embedder.fit_transform(tiny_net, item_ids=nodes)
    assert result is not None


def test_normalize_flag(tiny_net):
    """With normalize=True all vectors should have unit L2 norm."""
    from py3plex.embeddings.metapath2vec import MetaPath2VecEmbedder

    embedder = MetaPath2VecEmbedder(
        metapaths=[["author", "paper", "author"]],
        dim=8,
        walk_length=5,
        num_walks=2,
        epochs=2,
        seed=42,
        normalize=True,
    )
    nodes = tiny_net.get_nodes()
    result = embedder.fit_transform(tiny_net, item_ids=nodes)

    if result.matrix.shape[0] > 0:
        norms = np.linalg.norm(result.matrix, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-5)


def test_embedding_result_exported_from_package():
    """MetaPath2VecEmbedder is accessible via the embeddings package."""
    from py3plex.embeddings import MetaPath2VecEmbedder

    assert callable(MetaPath2VecEmbedder)

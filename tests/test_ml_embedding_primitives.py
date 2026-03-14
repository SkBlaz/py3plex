"""Tests for first-class embedding primitives."""

from __future__ import annotations

import numpy as np

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q
from py3plex.graph_ops import nodes
from py3plex.pipeline import NodeEmbedding, Pipeline, PipelineStep


def _toy_network() -> multi_layer_network:
    net = multi_layer_network(directed=False, network_type="multilayer")
    net.add_edges(
        [
            {
                "source": "Alice",
                "target": "Bob",
                "source_type": "social",
                "target_type": "social",
            },
            {
                "source": "Bob",
                "target": "Carol",
                "source_type": "social",
                "target_type": "social",
            },
            {
                "source": "Alice",
                "target": "Alice",
                "source_type": "social",
                "target_type": "work",
            },
            {
                "source": "Alice",
                "target": "Carol",
                "source_type": "work",
                "target_type": "work",
            },
        ]
    )
    return net


def test_node2vec_embedding():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=3, seed=42)
    assert emb.dimension == 8
    assert len(emb.nodes) == len(list(net.get_nodes()))
    assert emb.to_numpy().shape[1] == 8


def test_deepwalk_embedding():
    net = _toy_network()
    emb = net.embed(method="deepwalk", dimensions=6, walk_length=6, num_walks=2, seed=7)
    assert emb.to_numpy().shape == (len(list(net.get_nodes())), 6)


def test_netmf_embedding():
    net = _toy_network()
    emb = net.embed(method="netmf", dimensions=5, seed=1)
    assert emb.to_numpy().shape == (len(list(net.get_nodes())), 5)
    df = emb.to_pandas()
    assert {"node", "layer", "embedding"}.issubset(df.columns)


def test_embedding_similarity():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=12)
    node_ids = emb.nodes
    sim = emb.similarity(node_ids[0], node_ids[1])
    assert np.isfinite(sim)
    neighbors = emb.most_similar(node_ids[0], k=2)
    assert len(neighbors) <= 2


def test_multiplex_walks():
    net = _toy_network()
    emb = net.embed(
        method="multiplex_node2vec",
        dimensions=4,
        walk_length=6,
        num_walks=2,
        seed=5,
    )
    assert emb.to_numpy().shape[1] == 4
    assert any(isinstance(n, tuple) and len(n) == 2 for n in emb.nodes)


class _LoadToyNetwork(PipelineStep):
    def transform(self, data):
        return _toy_network()


def test_embedding_pipeline():
    pipe = Pipeline(
        [
            ("load", _LoadToyNetwork()),
            ("embed", NodeEmbedding(method="node2vec", dimensions=8, seed=42)),
        ]
    )
    out = pipe.run()
    assert "embedding" in out
    assert out["embedding"].to_numpy().shape[1] == 8


def test_dsl_embed_integration_node2vec():
    net = _toy_network()
    result = Q.nodes().embed("node2vec", dim=8, walk_length=8, num_walks=2, seed=42).execute(net)
    mat = result.to_numpy("embedding")
    assert mat.shape[1] == 8


def test_graph_ops_embed_column():
    net = _toy_network()
    frame = nodes(net).embed(method="node2vec", dim=8, walk_length=8, num_walks=2, seed=42)
    df = frame.to_pandas()
    assert "embedding" in df.columns

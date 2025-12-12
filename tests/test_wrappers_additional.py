"""Additional tests for py3plex.wrappers utilities."""

from pathlib import Path

import networkx as nx
import pytest

from py3plex.core import multinet
from py3plex.exceptions import ExternalToolError
from py3plex.wrappers import train_node2vec_embedding
from py3plex.wrappers.r_interop import (
    export_edgelist,
    export_nodelist,
    get_layer_names,
    get_network_stats,
)


def _simple_multilayer_network():
    """Create a tiny multilayer network with attributes."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "a", "type": "L1", "color": "red"},
            {"source": "b", "type": "L1", "color": "blue"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "a",
                "target": "b",
                "source_type": "L1",
                "target_type": "L1",
                "weight": 0.5,
                "label": "e1",
            }
        ]
    )
    return net


def test_export_nodelist_excludes_attributes_when_disabled():
    net = _simple_multilayer_network()
    nodes = export_nodelist(net, include_attributes=False)
    assert nodes
    assert all(node.keys() == {"id"} for node in nodes)


def test_export_edgelist_drops_attributes_when_disabled():
    net = _simple_multilayer_network()
    edges = export_edgelist(net, include_attributes=False)
    assert edges
    edge = edges[0]
    assert edge["src_layer"]
    assert edge["dst_layer"]
    # Extra attributes such as weight/label should be omitted
    assert "weight" not in edge
    assert "label" not in edge


def test_layer_names_and_stats_from_multilayer_network():
    net = _simple_multilayer_network()
    layers = get_layer_names(net)
    assert set(layers) == {"L1"}

    stats = get_network_stats(net)
    assert stats["num_nodes"] == 2
    assert stats["num_edges"] == 1
    assert stats["num_layers"] == 1
    assert stats["directed"] is False


def test_n2v_embedding_with_specific_parameters(monkeypatch, tmp_path):
    """Explicit p/q values should call the binary exactly once with those parameters."""
    G = nx.Graph()
    G.add_edge("u", "v", weight=1.0)

    calls = []

    def fake_call(input_graph, output_graph, p, q, **kwargs):
        calls.append((input_graph, output_graph, p, q, kwargs))

    monkeypatch.setattr(
        train_node2vec_embedding, "call_node2vec_binary", fake_call
    )

    out_file = tmp_path / "out.emb"
    train_node2vec_embedding.n2v_embedding(
        G,
        targets=[],
        p=0.75,
        q=0.25,
        outfile_name=str(out_file),
        binary_path="node2vec_bin",
        timeout=5,
    )

    assert len(calls) == 1
    _, output_path, p_val, q_val, kwargs = calls[0]
    assert output_path == str(out_file)
    assert p_val == 0.75
    assert q_val == 0.25
    assert kwargs.get("binary") == "node2vec_bin"


def test_n2v_embedding_grid_search_uses_best_parameters(monkeypatch, tmp_path):
    """Grid search should choose parameters that maximize benchmark macro score."""
    G = nx.Graph()
    G.add_edge("u", "v", weight=1.0)

    calls = []

    def fake_call(input_graph, output_graph, p, q, **kwargs):
        calls.append((p, q))
        Path(output_graph).write_text("2 2\n")

    def fake_benchmark(path, core_network, labels_matrix, percent):
        # Use the most recent (p, q) to derive a deterministic macro score
        p_val, q_val = calls[-1]
        macro = p_val + q_val
        return {float(percent): (0.0, macro, 0.0, 0.0)}

    monkeypatch.setattr(
        train_node2vec_embedding, "call_node2vec_binary", fake_call
    )
    monkeypatch.setattr(
        train_node2vec_embedding, "benchmark_node_classification", fake_benchmark
    )

    out_file = tmp_path / "grid.emb"
    train_node2vec_embedding.n2v_embedding(
        G,
        targets=[],
        outfile_name=str(out_file),
        parameter_range=[0.1, 0.2],
        binary_path="node2vec_bin",
        timeout=5,
    )

    # Final call should use the best (highest p+q) combination: 0.2, 0.2
    assert calls[-1] == (0.2, 0.2)
    # Total calls = len(parameter_range)^2 grid search + final call
    assert len(calls) == 5


def test_n2v_embedding_propagates_external_tool_errors(monkeypatch, tmp_path):
    G = nx.Graph()
    G.add_edge("u", "v", weight=1.0)

    def failing_call(*args, **kwargs):
        raise ExternalToolError("binary failed")

    monkeypatch.setattr(
        train_node2vec_embedding, "call_node2vec_binary", failing_call
    )

    with pytest.raises(ExternalToolError, match="binary failed"):
        train_node2vec_embedding.n2v_embedding(
            G,
            targets=[],
            p=1.0,
            q=1.0,
            outfile_name=str(tmp_path / "out.emb"),
            binary_path="node2vec_bin",
            timeout=1,
        )

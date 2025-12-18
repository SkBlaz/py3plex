from __future__ import annotations

import os

import pytest
sklearn = pytest.importorskip("sklearn")

import networkx as nx  # noqa: E402

from py3plex.exceptions import ExternalToolError  # noqa: E402
from py3plex.wrappers import train_node2vec_embedding as n2v  # noqa: E402


def test_call_node2vec_binary_raises_when_binary_missing(tmp_path):
    missing_binary = tmp_path / "node2vec_missing"

    with pytest.raises(ExternalToolError, match="Node2Vec binary not found"):
        n2v.call_node2vec_binary(
            input_graph="graph.txt",
            output_graph="out.emb",
            p=1.0,
            q=1.0,
            binary=str(missing_binary),
            timeout=1,
        )


def test_n2v_embedding_calls_binary_and_cleans_tmp(monkeypatch, tmp_path):
    G = nx.Graph()
    G.add_edge("u", "v", weight=1.0)

    tmp_dir = tmp_path / "tmpdir"

    def fake_mkdtemp(prefix: str):
        tmp_dir.mkdir()
        return str(tmp_dir)

    monkeypatch.setattr(n2v.tempfile, "mkdtemp", fake_mkdtemp)

    calls = {}

    def fake_call(input_graph, output_graph, p, q, directed, weighted, binary, timeout, dimension=128):
        calls["args"] = {
            "input_graph": input_graph,
            "output_graph": output_graph,
            "p": p,
            "q": q,
            "directed": directed,
            "weighted": weighted,
            "binary": binary,
            "timeout": timeout,
            "dimension": dimension,
        }
        assert os.path.exists(input_graph)

    monkeypatch.setattr(n2v, "call_node2vec_binary", fake_call)

    outfile = tmp_path / "out.emb"
    n2v.n2v_embedding(
        G,
        targets=[],
        p=1.5,
        q=0.5,
        outfile_name=str(outfile),
        binary_path="bin_path",
        timeout=2,
    )

    assert calls["args"]["p"] == 1.5
    assert calls["args"]["q"] == 0.5
    assert calls["args"]["binary"] == "bin_path"
    assert calls["args"]["output_graph"] == str(outfile)
    assert not tmp_dir.exists()


def test_learn_embedding_forwards_parsed_parameter_range(monkeypatch, tmp_path):
    recorded = {}

    def fake_n2v_embedding(
        core_network,
        targets,
        sample_size,
        verbose,
        outfile_name,
        p,
        q,
        binary_path,
        parameter_range,
        timeout,
    ):
        recorded["args"] = {
            "targets": targets,
            "sample_size": sample_size,
            "outfile_name": outfile_name,
            "p": p,
            "q": q,
            "binary_path": binary_path,
            "parameter_range": parameter_range,
            "timeout": timeout,
        }

    monkeypatch.setattr(n2v, "n2v_embedding", fake_n2v_embedding)

    G = nx.Graph()
    G.add_edge("u", "v", weight=1.0)
    outfile = tmp_path / "emb.emb"

    method, elapsed = n2v.learn_embedding(
        G,
        labels=[0, 1],
        ssize=0.25,
        embedding_outfile=str(outfile),
        p=0.2,
        q=0.3,
        binary_path="custom_bin",
        parameter_range="[0.1, 0.2]",
        timeout=1,
    )

    assert method == "default_n2v"
    assert "args" in recorded
    assert recorded["args"]["targets"] == [0, 1]
    assert recorded["args"]["sample_size"] == 0.25
    assert recorded["args"]["outfile_name"] == str(outfile)
    assert recorded["args"]["p"] == 0.2
    assert recorded["args"]["q"] == 0.3
    assert recorded["args"]["binary_path"] == "custom_bin"
    assert recorded["args"]["parameter_range"] == [0.1, 0.2]

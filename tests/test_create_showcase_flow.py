import os
from collections import Counter

import matplotlib
import matplotlib.patches as mpatches
from matplotlib.colors import to_hex

# Use a headless backend suitable for CI
matplotlib.use("Agg")

import create_showcase_flow as csf  # noqa: E402


def test_create_showcase_network_structure():
    network = csf.create_showcase_network()

    nodes = list(network.core_network.nodes())
    assert len(nodes) == 21
    assert network.directed is False

    layer_counts = Counter(layer for _, layer in nodes)
    assert layer_counts == {"Social": 8, "Work": 7, "Hobby": 6}

    intra_layer_counts = Counter()
    inter_layer_edges = set()

    for u, v in network.core_network.edges():
        if u[1] == v[1]:
            intra_layer_counts[u[1]] += 1
        else:
            inter_layer_edges.add(frozenset([(u[0], u[1]), (v[0], v[1])]))

    assert intra_layer_counts == {"Social": 12, "Work": 9, "Hobby": 7}

    expected_inter = {
        frozenset([("Alice", "Social"), ("Alice", "Work")]),
        frozenset([("Bob", "Social"), ("Bob", "Work")]),
        frozenset([("Charlie", "Social"), ("Charlie", "Work")]),
        frozenset([("Diana", "Social"), ("Diana", "Work")]),
        frozenset([("Frank", "Social"), ("Frank", "Work")]),
        frozenset([("Grace", "Social"), ("Grace", "Work")]),
        frozenset([("Bob", "Work"), ("Bob", "Hobby")]),
        frozenset([("Charlie", "Work"), ("Charlie", "Hobby")]),
        frozenset([("Diana", "Work"), ("Diana", "Hobby")]),
        frozenset([("Grace", "Work"), ("Grace", "Hobby")]),
    }

    assert inter_layer_edges == expected_inter


def test_create_publication_quality_visualization_draws_and_saves(monkeypatch, capsys):
    draw_calls = {}

    def fake_draw(graphs, multilinks, labels=None, ax=None, **kwargs):
        draw_calls["graphs"] = graphs
        draw_calls["multilinks"] = multilinks
        draw_calls["labels"] = labels
        draw_calls["kwargs"] = kwargs

    monkeypatch.setattr(csf, "draw_multilayer_flow", fake_draw)

    original_savefig = csf.plt.savefig
    saved = {}

    def spy_savefig(path, *args, **kwargs):
        saved["path"] = path
        saved["rectangles"] = [
            patch
            for patch in csf.plt.gca().patches
            if isinstance(patch, mpatches.Rectangle)
        ]
        saved["texts"] = [text.get_text() for text in csf.plt.gca().texts]
        saved["limits"] = {
            "xlim": csf.plt.gca().get_xlim(),
            "ylim": csf.plt.gca().get_ylim(),
        }
        return original_savefig(path, *args, **kwargs)

    monkeypatch.setattr(csf.plt, "savefig", spy_savefig)

    output_path = csf.create_publication_quality_visualization()
    out = capsys.readouterr().out

    assert "Creating publication-quality flow visualization" in out
    assert output_path == "/tmp/multilayer_flow_showcase.png"
    assert draw_calls["labels"] == ["Social", "Work", "Hobby"]
    assert [len(g.nodes()) for g in draw_calls["graphs"]] == [8, 7, 6]
    assert draw_calls["multilinks"]
    assert draw_calls["kwargs"]["display"] is False
    assert draw_calls["kwargs"]["layer_gap"] == 2.2
    assert draw_calls["kwargs"]["node_size"] == 300
    assert draw_calls["kwargs"]["flow_alpha"] == 0.6
    assert draw_calls["kwargs"]["flow_min_width"] == 1.5
    assert draw_calls["kwargs"]["flow_max_width"] == 12.0

    assert saved["path"] == output_path
    assert os.path.exists(output_path) and os.path.getsize(output_path) > 0

    layer_colors = {
        to_hex(rect.get_facecolor())
        for rect in saved["rectangles"]
        if to_hex(rect.get_edgecolor()) == "#666666"
    }
    assert {"#ffe6e6", "#e6f3ff", "#e6ffe6"}.issubset(layer_colors)
    assert {rect.get_width() for rect in saved["rectangles"]} == {8, 7, 6}
    assert all(rect.get_height() == 1.6 for rect in saved["rectangles"])
    assert saved["limits"]["xlim"] == (-1.0, 8.5)
    assert saved["limits"]["ylim"] == (-1.0, 5.5)
    assert any("Multilayer Flow Visualization" in text for text in saved["texts"])
    assert any("Nodes sized and colored by network activity" in text for text in saved["texts"])

    assert csf.plt.get_fignums() == []

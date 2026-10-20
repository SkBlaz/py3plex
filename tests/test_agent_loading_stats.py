"""The agent loader reports graph structure without computing layouts."""

import pytest

from py3plex.agent import load_network_from_path
from py3plex.core import converters


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize(
    "rows, layers, node_count, edge_count",
    [
        ("", [], 0, 0),
        ("a L b L 2\n", ["L"], 2, 1),
        (
            "a social b social 2\na work c work 3\n",
            ["social", "work"],
            4,
            2,
        ),
        (
            "a A b A 1\na B b B 1\na C b C 1\na D b D 1\n",
            ["A", "B", "C", "D"],
            8,
            4,
        ),
    ],
)
def test_agent_loader_reports_exact_structure(
    tmp_path, directed, rows, layers, node_count, edge_count
):
    path = tmp_path / "network.edges"
    path.write_text(rows)
    payload = load_network_from_path(
        str(path), input_type="multiedgelist", directed=directed
    )
    assert payload["status"] == "ok"
    assert payload["result"]["network_stats"] == {
        "node_replicas": node_count,
        "edges": edge_count,
        "layers": layers,
        "layer_count": len(layers),
    }
    net = payload["result"]["network"]
    assert net.directed is directed
    assert net.core_network.is_directed() is directed
    assert not any("pos" in data for _, data in net.core_network.nodes(data=True))
    assert payload["provenance"] == {
        "source_path": str(path),
        "input_type": "multiedgelist",
        "directed": directed,
    }


def test_agent_loader_does_not_compute_visualization_layouts(tmp_path, monkeypatch):
    def unexpected_layout(*args, **kwargs):
        pytest.fail("Loading graph statistics must not compute a visualization layout")

    monkeypatch.setattr(converters, "compute_layout", unexpected_layout)
    path = tmp_path / "network.edges"
    path.write_text("a b\n")
    payload = load_network_from_path(str(path))
    assert payload["result"]["network_stats"]["layers"] == ["null"]

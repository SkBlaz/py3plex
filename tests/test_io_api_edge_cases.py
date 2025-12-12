import pytest

from py3plex.exceptions import Py3plexFormatError
from py3plex.io import (
    FormatUnsupportedError,
    Layer,
    MultiLayerGraph,
    Node,
    read,
    write,
)
from py3plex.io.formats import arrow_format


def _minimal_graph():
    graph = MultiLayerGraph()
    graph.add_layer(Layer(id="L"))
    graph.add_node(Node(id="n1"))
    return graph


def test_jsonl_reader_reports_line_number_on_invalid_json(tmp_path):
    """JSONL reader should surface line numbers for malformed lines."""
    path = tmp_path / "bad.jsonl"
    path.write_text('{"directed": true}\n{"type": "node" "missing_colon": 1}\n')

    with pytest.raises(Py3plexFormatError, match="line 2"):
        read(path, format="jsonl")


def test_jsonl_reader_rejects_unknown_object_type(tmp_path):
    """Unknown object type should raise Py3plexFormatError."""
    path = tmp_path / "unknown_type.jsonl"
    path.write_text('{"directed": true}\n{"type": "mystery"}\n')

    with pytest.raises(Py3plexFormatError, match="Unknown object type"):
        read(path, format="jsonl")


def test_explicit_format_allows_unknown_extension(tmp_path):
    """Explicit format parameter should bypass extension-based detection."""
    graph = _minimal_graph()
    path = tmp_path / "graph.weird"

    write(graph, path, format="json")
    loaded = read(path, format="json")

    assert set(loaded.nodes) == set(graph.nodes)
    assert set(loaded.layers) == set(graph.layers)


def test_arrow_write_raises_when_pyarrow_unavailable(monkeypatch, tmp_path):
    """write_arrow should fail fast if pyarrow is missing."""
    graph = _minimal_graph()
    monkeypatch.setattr(arrow_format, "PYARROW_AVAILABLE", False)

    with pytest.raises(Py3plexFormatError, match="pyarrow"):
        arrow_format.write_arrow(graph, tmp_path / "graph.arrow")


def test_unknown_gz_extension_reports_format_error(tmp_path):
    """Unknown inner extension with .gz should raise FormatUnsupportedError."""
    path = tmp_path / "graph.unknown.gz"
    path.write_text("not a real graph")

    with pytest.raises(FormatUnsupportedError, match="gz"):
        read(path)

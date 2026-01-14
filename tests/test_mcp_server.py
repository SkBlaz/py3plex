"""Tests for py3plex MCP server.

Tests cover:
- Registry operations (add, get, remove, list)
- Safe path validation
- Truncation behavior
- Error handling and payloads
- Tool functionality
"""

import json
import tempfile
from pathlib import Path

import pytest

from py3plex_mcp.errors import (
    MCPError,
    NetworkNotFoundError,
    PathAccessError,
    UnsupportedFormatError,
    make_error_response,
)
from py3plex_mcp.registry import NetworkRegistry
from py3plex_mcp.safe_paths import (
    DEFAULT_OUTPUT_DIR,
    make_unique_filename,
    resolve_out_dir,
    resolve_read_path,
)
from py3plex_mcp.schemas import (
    format_stats,
    make_meta,
    make_success_response,
    serialize_json,
    truncate_list,
)


# ============================================================================
# Registry Tests
# ============================================================================


def test_registry_add_get():
    """Test adding and retrieving networks."""
    registry = NetworkRegistry()

    # Mock network object
    mock_net = {"type": "test_network"}

    net_id = registry.add(mock_net, source="/test/path.csv")

    assert isinstance(net_id, str)
    assert len(net_id) == 8  # UUID first 8 chars

    retrieved = registry.get(net_id)
    assert retrieved == mock_net


def test_registry_custom_id():
    """Test custom network ID."""
    registry = NetworkRegistry()
    mock_net = {"type": "test"}

    net_id = registry.add(mock_net, source="/test/path.csv", net_id="custom_id")
    assert net_id == "custom_id"

    retrieved = registry.get("custom_id")
    assert retrieved == mock_net


def test_registry_duplicate_id():
    """Test handling duplicate IDs."""
    registry = NetworkRegistry()
    mock_net1 = {"type": "net1"}
    mock_net2 = {"type": "net2"}

    net_id1 = registry.add(mock_net1, source="/test/1.csv", net_id="test_id")
    net_id2 = registry.add(mock_net2, source="/test/2.csv", net_id="test_id")

    assert net_id1 == "test_id"
    assert net_id2 == "test_id_1"


def test_registry_get_not_found():
    """Test getting non-existent network."""
    registry = NetworkRegistry()

    with pytest.raises(NetworkNotFoundError) as exc_info:
        registry.get("nonexistent")

    assert "nonexistent" in str(exc_info.value)


def test_registry_get_info():
    """Test getting network metadata."""
    registry = NetworkRegistry()
    mock_net = {"type": "test"}

    net_id = registry.add(
        mock_net,
        source="/test/path.csv",
        metadata={"foo": "bar"},
    )

    info = registry.get_info(net_id)

    assert info["net_id"] == net_id
    assert info["source"] == "/test/path.csv"
    assert "created_at" in info
    assert info["metadata"]["foo"] == "bar"


def test_registry_remove():
    """Test removing network."""
    registry = NetworkRegistry()
    mock_net = {"type": "test"}

    net_id = registry.add(mock_net, source="/test/path.csv")
    registry.remove(net_id)

    with pytest.raises(NetworkNotFoundError):
        registry.get(net_id)


def test_registry_list_all():
    """Test listing all networks."""
    registry = NetworkRegistry()

    # Add multiple networks
    net_id1 = registry.add({"type": "net1"}, source="/test/1.csv")
    net_id2 = registry.add({"type": "net2"}, source="/test/2.csv")

    handles = registry.list_all()

    assert len(handles) == 2
    assert any(h["net_id"] == net_id1 for h in handles)
    assert any(h["net_id"] == net_id2 for h in handles)


def test_registry_clear():
    """Test clearing registry."""
    registry = NetworkRegistry()

    registry.add({"type": "net1"}, source="/test/1.csv")
    registry.add({"type": "net2"}, source="/test/2.csv")

    registry.clear()

    assert len(registry.list_all()) == 0


# ============================================================================
# Safe Path Tests
# ============================================================================


def test_resolve_read_path_valid(tmp_path):
    """Test resolving valid read path."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("test")

    resolved = resolve_read_path(str(test_file))

    assert resolved.exists()
    assert resolved.is_absolute()


def test_resolve_read_path_not_exists():
    """Test resolving non-existent path."""
    with pytest.raises(PathAccessError) as exc_info:
        resolve_read_path("/nonexistent/path.csv")

    error = exc_info.value
    assert error.error_type == "PathAccessError"
    assert "/nonexistent/path.csv" in error.message


def test_resolve_read_path_globbing():
    """Test rejecting globbing patterns."""
    with pytest.raises(PathAccessError) as exc_info:
        resolve_read_path("/tmp/*.csv")

    error = exc_info.value
    assert error.error_type == "PathAccessError"


def test_resolve_read_path_forbidden(monkeypatch):
    """Test rejecting forbidden paths."""
    # Create a temp file in /tmp (not forbidden)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        # This should work
        resolved = resolve_read_path(str(tmp_path))
        assert resolved.exists()
    finally:
        tmp_path.unlink()

    # Test forbidden path (if /etc exists)
    if Path("/etc").exists():
        etc_test = Path("/etc/hosts")
        if etc_test.exists():
            with pytest.raises(PathAccessError) as exc_info:
                resolve_read_path(str(etc_test))
            assert exc_info.value.error_type == "PathAccessError"


def test_resolve_out_dir_default():
    """Test default output directory."""
    out_dir = resolve_out_dir(None)

    assert out_dir == DEFAULT_OUTPUT_DIR
    assert out_dir.exists()


def test_resolve_out_dir_custom(tmp_path):
    """Test custom output directory."""
    custom_dir = tmp_path / "custom_out"

    out_dir = resolve_out_dir(str(custom_dir))

    assert out_dir == custom_dir.resolve()
    assert out_dir.exists()


def test_make_unique_filename(tmp_path):
    """Test unique filename generation."""
    # First call
    path1 = make_unique_filename(tmp_path, "test", "json")
    assert path1.name == "test.json"

    # Create file
    path1.write_text("{}")

    # Second call should add suffix
    path2 = make_unique_filename(tmp_path, "test", "json")
    assert path2.name == "test_1.json"


# ============================================================================
# Schema Tests
# ============================================================================


def test_make_meta():
    """Test metadata generation."""
    meta = make_meta("test_tool", ok=True)

    assert meta["ok"] is True
    assert meta["tool"] == "test_tool"
    assert "version" in meta
    assert "timestamp" in meta


def test_make_meta_truncated():
    """Test truncated metadata."""
    meta = make_meta("test_tool", truncated=True, count=1000, limit=200)

    assert meta["truncated"] is True
    assert meta["total_count"] == 1000
    assert meta["limit"] == 200


def test_make_success_response():
    """Test success response generation."""
    response = make_success_response(
        "test_tool",
        {"result": "success"},
    )

    assert "meta" in response
    assert response["meta"]["ok"] is True
    assert response["meta"]["tool"] == "test_tool"
    assert response["result"] == "success"


def test_truncate_list():
    """Test list truncation."""
    items = list(range(100))

    # No truncation
    result, truncated, count = truncate_list(items, 200)
    assert len(result) == 100
    assert truncated is False

    # With truncation
    result, truncated, count = truncate_list(items, 50)
    assert len(result) == 50
    assert truncated is True
    assert count == 100


def test_serialize_json():
    """Test JSON serialization."""
    import numpy as np

    # Test numpy types
    data = {
        "scalar": np.int64(42),
        "array": np.array([1, 2, 3]).tolist(),  # Pre-convert to list
        "set": {1, 2, 3},
        "nested": {"list": [1, 2], "set": {4, 5}},
    }

    result = serialize_json(data)

    assert isinstance(result["scalar"], int)
    assert isinstance(result["array"], list)
    assert isinstance(result["set"], list)
    assert isinstance(result["nested"]["set"], list)

    # Should be JSON serializable
    json.dumps(result)


# ============================================================================
# Error Tests
# ============================================================================


def test_mcp_error():
    """Test MCPError creation."""
    error = MCPError(
        "Test error",
        error_type="TestError",
        hint="Try something else",
        details={"foo": "bar"},
    )

    error_dict = error.to_dict()

    assert error_dict["type"] == "TestError"
    assert error_dict["message"] == "Test error"
    assert error_dict["hint"] == "Try something else"
    assert error_dict["details"]["foo"] == "bar"


def test_network_not_found_error():
    """Test NetworkNotFoundError."""
    error = NetworkNotFoundError("test_id")

    assert "test_id" in error.message
    assert error.error_type == "NetworkNotFoundError"
    assert "list_handles" in error.hint


def test_unsupported_format_error():
    """Test UnsupportedFormatError."""
    error = UnsupportedFormatError("invalid", ["valid1", "valid2"])

    assert "invalid" in error.message
    assert "valid1" in error.hint
    assert "supported_formats" in error.details


def test_make_error_response():
    """Test error response generation."""
    error = NetworkNotFoundError("test_id")
    response = make_error_response(error)

    assert response["ok"] is False
    assert "error" in response
    assert response["error"]["type"] == "NetworkNotFoundError"

    # Test generic exception
    generic_error = ValueError("Test error")
    response = make_error_response(generic_error)

    assert response["ok"] is False
    assert response["error"]["type"] == "ValueError"


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
def test_load_stats_workflow(tmp_path):
    """Test load -> stats workflow."""
    from py3plex.core import multinet
    from py3plex_mcp.registry import get_registry
    from py3plex_mcp.schemas import format_stats

    # Create test network file (multiedgelist format)
    test_file = tmp_path / "test.csv"
    test_file.write_text("A layer1 B layer1\nB layer1 C layer1\n")

    # Load network
    net = multinet.multi_layer_network(directed=False)
    net.load_network(str(test_file), input_type="multiedgelist")

    # Add to registry
    registry = get_registry()
    registry.clear()  # Clear any previous test data
    net_id = registry.add(net, source=str(test_file))

    # Get stats
    stats = format_stats(net)

    assert stats["node_count"] >= 2
    assert stats["edge_count"] >= 1
    assert "layers_preview" in stats

    # Clean up
    registry.clear()


@pytest.mark.integration
def test_query_workflow(tmp_path):
    """Test load -> query workflow."""
    from py3plex.core import multinet
    from py3plex.dsl_legacy import execute_query
    from py3plex_mcp.registry import get_registry
    from py3plex_mcp.schemas import format_query_result

    # Create test network (multiedgelist format)
    test_file = tmp_path / "test.csv"
    test_file.write_text("A layer1 B layer1\nB layer1 C layer1\nC layer1 D layer1\n")

    net = multinet.multi_layer_network(directed=False)
    net.load_network(str(test_file), input_type="multiedgelist")

    # Add to registry
    registry = get_registry()
    registry.clear()
    net_id = registry.add(net, source=str(test_file))

    # Execute query
    result = execute_query(net, "SELECT nodes")

    # Format result
    formatted = format_query_result(result, limit=2)

    assert "result" in formatted
    assert formatted["truncated"] in [True, False]

    # Clean up
    registry.clear()


@pytest.mark.integration
def test_query_workflow_dslv2(tmp_path):
    """Test load -> DSL v2 query workflow."""
    from py3plex.core import multinet
    from py3plex.dsl import Q
    from py3plex_mcp.registry import get_registry
    from py3plex_mcp.schemas import format_query_result

    # Create test network (multiedgelist format)
    test_file = tmp_path / "test.csv"
    test_file.write_text("A layer1 B layer1\nB layer1 C layer1\nC layer1 D layer1\n")

    net = multinet.multi_layer_network(directed=False)
    net.load_network(str(test_file), input_type="multiedgelist")

    # Add to registry
    registry = get_registry()
    registry.clear()
    net_id = registry.add(net, source=str(test_file))

    # Execute DSL v2 query
    result = Q.nodes().execute(net, progress=False)

    # Format result
    formatted = format_query_result(result, limit=2)

    assert "result" in formatted
    assert formatted["truncated"] in [True, False]
    assert "nodes" in formatted["result"] or "edges" in formatted["result"]

    # Test with computed metrics
    result_with_compute = Q.nodes().compute("degree").execute(net, progress=False)
    formatted_compute = format_query_result(result_with_compute, limit=10)

    assert "result" in formatted_compute
    assert "computed" in formatted_compute["result"]

    # Clean up
    registry.clear()


@pytest.mark.integration
def test_export_workflow(tmp_path):
    """Test export workflow."""
    from py3plex_mcp.safe_paths import make_unique_filename, resolve_out_dir

    # Prepare data
    data = {"nodes": [{"id": "A", "degree": 2}, {"id": "B", "degree": 3}]}

    # Resolve output directory
    out_dir = resolve_out_dir(str(tmp_path / "out"))

    # Generate filename
    output_path = make_unique_filename(out_dir, "test_export", "json")

    # Write file
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    # Verify
    assert output_path.exists()
    loaded = json.loads(output_path.read_text())
    assert loaded == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

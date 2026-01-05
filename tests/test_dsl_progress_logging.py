"""Tests for DSL progress logging feature.

Tests cover:
- Progress logging enabled/disabled
- Progress logging with different query types
- Progress logging with compute steps
"""

import logging
import pytest
from io import StringIO
from py3plex.core import multinet
from py3plex.dsl import Q, L, execute_ast, Query, SelectStmt, Target


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)

    return network


class TestProgressLogging:
    """Test progress logging feature."""

    def test_progress_enabled_by_default(self, sample_network, caplog):
        """Test that progress logging is enabled by default."""
        with caplog.at_level(logging.INFO):
            q = Q.nodes().from_layers(L["social"]).compute("degree")
            result = q.execute(sample_network)
            
            # Should have progress messages by default
            assert "Starting DSL query execution" in caplog.text
            assert len(result.items) == 3

    def test_progress_enabled(self, sample_network, caplog):
        """Test that progress logging can be enabled."""
        with caplog.at_level(logging.INFO):
            q = Q.nodes().from_layers(L["social"]).compute("degree")
            result = q.execute(sample_network, progress=True)
            
            # Should have progress messages
            assert "Starting DSL query execution" in caplog.text
            assert "Step 1: Binding parameters" in caplog.text
            assert "Step 3: Executing SELECT statement" in caplog.text
            assert "Query execution completed" in caplog.text
            assert len(result.items) == 3

    def test_progress_with_multiple_steps(self, sample_network, caplog):
        """Test progress logging with multiple query steps."""
        with caplog.at_level(logging.INFO):
            q = (
                Q.nodes()
                 .from_layers(L["social"] + L["work"])
                 .where(degree__gt=0)
                 .compute("degree")
                 .compute("betweenness")
                 .order_by("betweenness", desc=True)
                 .limit(3)
            )
            result = q.execute(sample_network, progress=True)
            
            # Check for all major steps
            assert "Step 3.1: Getting initial nodes" in caplog.text
            assert "Step 3.2: Applying layer filter" in caplog.text
            assert "Step 3.3: Applying WHERE conditions" in caplog.text
            assert "Step 3.4: Computing 2 measure(s)" in caplog.text
            assert "Computing degree (1/2)" in caplog.text
            assert "Computing betweenness (2/2)" in caplog.text
            assert "Step 3.5: Applying ORDER BY" in caplog.text
            assert "Step 3.6: Applying LIMIT 3" in caplog.text
            assert len(result.items) == 3

    def test_progress_with_layer_filter(self, sample_network, caplog):
        """Test progress logging shows layer filtering."""
        with caplog.at_level(logging.INFO):
            q = Q.nodes().from_layers(L["social"])
            result = q.execute(sample_network, progress=True)
            
            assert "Step 3.2: Applying layer filter" in caplog.text
            assert "Filtered to 3 nodes in 1 layers" in caplog.text
            assert len(result.items) == 3

    def test_progress_with_edge_query(self, sample_network, caplog):
        """Test progress logging with edge queries."""
        with caplog.at_level(logging.INFO):
            q = Q.edges().from_layers(L["social"])
            result = q.execute(sample_network, progress=True)
            
            assert "Starting DSL query execution" in caplog.text
            assert "Getting initial edges" in caplog.text
            assert "Query execution completed" in caplog.text
            # Should have 3 edges in social layer (triangle)
            assert len(result.items) == 3

    def test_progress_disabled_explicitly(self, sample_network, caplog):
        """Test that progress logging can be explicitly disabled."""
        with caplog.at_level(logging.INFO):
            q = Q.nodes().from_layers(L["social"]).compute("degree")
            result = q.execute(sample_network, progress=False)
            
            # Should not have progress messages when explicitly disabled
            assert "Starting DSL query execution" not in caplog.text
            assert len(result.items) == 3

    def test_progress_with_execute_ast(self, sample_network, caplog):
        """Test progress logging works with execute_ast function."""
        with caplog.at_level(logging.INFO):
            # Build a simple query using AST
            select = SelectStmt(
                target=Target.NODES,
                layer_expr=None,
                where=None,
                compute=[],
                order_by=[],
                limit=None,
                export=None,
            )
            query = Query(explain=False, select=select)
            
            result = execute_ast(sample_network, query, progress=True)
            
            assert "Starting DSL query execution" in caplog.text
            assert "Query execution completed" in caplog.text
            assert len(result.items) == 5  # All nodes

    def test_progress_messages_are_info_level(self, sample_network, caplog):
        """Test that progress messages use INFO logging level."""
        with caplog.at_level(logging.INFO):
            q = Q.nodes().from_layers(L["social"])
            result = q.execute(sample_network, progress=True)
            
            # Check that messages are at INFO level
            info_messages = [record for record in caplog.records if record.levelname == "INFO"]
            assert len(info_messages) > 0
            
            # Check logger name
            for record in info_messages:
                if "Starting DSL query execution" in record.message:
                    assert record.name == "py3plex.dsl.executor"

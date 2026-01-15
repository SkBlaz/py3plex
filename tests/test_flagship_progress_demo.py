"""Test that demonstrates flagship example progress logging.

This test demonstrates the enhanced progress logging with a complex
flagship-style query similar to the one in README.md.
"""

import logging
import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L


@pytest.fixture
def multilayer_network():
    """Create a multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Add nodes across 3 layers
    edges = [
        # Layer 0: A and B are hubs
        ["A", "L0", "B", "L0", 1.0],
        ["A", "L0", "C", "L0", 1.0],
        ["A", "L0", "D", "L0", 1.0],
        ["B", "L0", "C", "L0", 1.0],
        ["B", "L0", "D", "L0", 1.0],
        ["B", "L0", "E", "L0", 1.0],
        # Layer 1: A and F are hubs
        ["A", "L1", "F", "L1", 1.0],
        ["A", "L1", "G", "L1", 1.0],
        ["A", "L1", "H", "L1", 1.0],
        ["F", "L1", "G", "L1", 1.0],
        ["F", "L1", "H", "L1", 1.0],
        # Layer 2: A and I are hubs
        ["A", "L2", "I", "L2", 1.0],
        ["A", "L2", "J", "L2", 1.0],
        ["I", "L2", "J", "L2", 1.0],
        # Cross-layer edges
        ["A", "L0", "A", "L1", 1.0],
        ["A", "L0", "A", "L2", 1.0],
        ["A", "L1", "A", "L2", 1.0],
    ]
    network.add_edges(edges, input_type="list")
    
    return network


def test_flagship_style_query_progress(multilayer_network, caplog):
    """Test progress logging with a flagship-style complex query."""
    with caplog.at_level(logging.INFO):
        # Complex query similar to flagship example (without actual community detection)
        result = (
            Q.nodes()
            .from_layers(L["L0"] + L["L1"] + L["L2"])
            .where(degree__gt=1)
            .compute("degree_centrality", "betweenness_centrality")
            .per_layer()  # Group by layer
            .top_k(2, "betweenness_centrality")  # Top 2 per layer
            .end_grouping()
            .coverage(mode="at_least", k=2)  # Keep nodes in ≥2 layers
            .mutate(
                score=lambda r: (
                    0.5 * r.get("betweenness_centrality", 0)
                    + 0.5 * r.get("degree_centrality", 0)
                )
            )
            .limit(5)
            .execute(multilayer_network, progress=True)
        )
        
        # Verify progress messages
        log_text = caplog.text
        
        # Initial message
        assert "Starting DSL query execution" in log_text
        
        # Query pipeline summary
        assert "Query pipeline:" in log_text
        assert "Target: nodes" in log_text
        assert "Compute: 2 measure(s)" in log_text
        assert "degree_centrality" in log_text
        assert "betweenness_centrality" in log_text
        assert "Grouping: by layer" in log_text
        assert "Top-k: 2 per group" in log_text
        assert "Coverage: at_least (k=2)" in log_text
        assert "Post-processing: mutate(1)" in log_text
        assert "Limit: 5" in log_text
        
        # Execution steps
        assert "Step 1: Binding parameters" in log_text
        assert "Step 3: Executing SELECT statement" in log_text
        assert "Getting initial nodes" in log_text
        assert "Applying layer filter" in log_text
        assert "Applying WHERE conditions" in log_text
        assert "Computing 2 measure(s)" in log_text
        assert "Computing degree_centrality" in log_text
        assert "Computing betweenness_centrality" in log_text
        
        # Grouping operations
        assert "Applying grouping and coverage filtering" in log_text
        assert "Grouping" in log_text and "items by" in log_text
        assert "Created" in log_text and "groups" in log_text
        assert "Applying per-group top-k" in log_text
        assert "Applying coverage filter" in log_text
        assert "Flattened to" in log_text and "items after grouping" in log_text
        
        # Post-processing
        assert "Applying post-processing operations" in log_text
        assert "Applying mutate" in log_text
        
        # Limit
        assert "Applying LIMIT" in log_text
        
        # Result creation
        assert "Creating QueryResult" in log_text
        
        # Completion
        assert "Query execution completed" in log_text
        
        # Verify result is valid
        assert result is not None
        assert result.count > 0
        assert result.count <= 5


def test_flagship_progress_shows_pipeline_length(multilayer_network, caplog):
    """Test that progress logs make the pipeline length clear."""
    with caplog.at_level(logging.INFO):
        result = (
            Q.nodes()
            .from_layers(L["L0"] + L["L1"])
            .compute("degree")
            .per_layer()
            .top_k(3, "degree")
            .end_grouping()
            .execute(multilayer_network, progress=True)
        )
        
        # Count step messages to understand pipeline length
        log_text = caplog.text
        
        # Should have clear indicators of each major step
        step_indicators = [
            "Starting DSL query execution",
            "Query pipeline:",
            "Step 1:",
            "Step 2:",
            "Step 3:",
            "Query execution completed",
        ]
        
        for indicator in step_indicators:
            assert indicator in log_text, f"Missing step indicator: {indicator}"
        
        # Should show clear hierarchical structure with main steps and sub-steps
        assert "Step 3.1:" in log_text  # Sub-step
        assert "Step 3.2:" in log_text  # Sub-step
        assert "Step 3.4:" in log_text  # Sub-step


if __name__ == "__main__":
    # Manual testing / demo script
    # This block allows running this test file directly to see the progress logging in action
    import sys
    logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
    
    network = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["A", "L0", "B", "L0", 1.0],
        ["A", "L0", "C", "L0", 1.0],
        ["A", "L1", "B", "L1", 1.0],
        ["A", "L1", "D", "L1", 1.0],
    ]
    network.add_edges(edges, input_type="list")
    
    print("=" * 80)
    print("FLAGSHIP-STYLE QUERY PROGRESS DEMO")
    print("=" * 80)
    print()
    
    result = (
        Q.nodes()
        .from_layers(L["L0"] + L["L1"])
        .where(degree__gt=0)
        .compute("degree_centrality", "betweenness_centrality")
        .per_layer()
        .top_k(2, "betweenness_centrality")
        .end_grouping()
        .mutate(score=lambda r: r.get("betweenness_centrality", 0) * 2)
        .limit(3)
        .execute(network, progress=True)
    )
    
    print()
    print("=" * 80)
    print(f"RESULT: {result.count} nodes")
    print("=" * 80)

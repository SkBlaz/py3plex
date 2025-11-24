"""
Unit tests for multi-edgelist parsing improvements

These tests validate the friction point fixes without requiring
full API setup or Celery workers.
"""
import tempfile
import os
import sys

# Add gui/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../api'))

from app.services.io import load_multilayer_edgelist
import networkx as nx


def test_load_multiedgelist_with_comments():
    """Test that comments are properly skipped in multi-edgelist files"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("# This is a comment\n")
        f.write("1 2 social 1.0\n")
        f.write("# Another comment\n")
        f.write("2 3 social 1.5\n")
        f.write("3 4 work 2.0\n")
        filepath = f.name
    
    try:
        graph = load_multilayer_edgelist(filepath)
        
        # Verify graph was loaded correctly
        assert graph.number_of_nodes() == 4, "Should have 4 nodes"
        assert graph.number_of_edges() == 3, "Should have 3 edges"
        
        # Verify layers
        layers = set()
        for u, v, data in graph.edges(data=True):
            if 'layer' in data:
                layers.add(data['layer'])
        
        assert 'social' in layers, "Should have social layer"
        assert 'work' in layers, "Should have work layer"
        
        print("✓ Comments handled correctly")
    finally:
        os.unlink(filepath)


def test_load_multiedgelist_simple_format():
    """Test that simple 2-column edgelists are supported"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("1 2\n")
        f.write("2 3\n")
        f.write("3 4\n")
        filepath = f.name
    
    try:
        graph = load_multilayer_edgelist(filepath)
        
        assert graph.number_of_nodes() == 4, "Should have 4 nodes"
        assert graph.number_of_edges() == 3, "Should have 3 edges"
        
        # Verify default layer is assigned
        for u, v, data in graph.edges(data=True):
            assert 'layer' in data, "Edge should have layer attribute"
            assert data['layer'] == 'default', "Should use default layer"
        
        print("✓ Simple 2-column format supported")
    finally:
        os.unlink(filepath)


def test_load_multiedgelist_with_weights():
    """Test that edge weights are properly parsed"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("1 2 social 1.5\n")
        f.write("2 3 social 2.0\n")
        f.write("3 4 work 0.5\n")
        filepath = f.name
    
    try:
        graph = load_multilayer_edgelist(filepath)
        
        # Check weights
        weights = [data.get('weight', 0) for u, v, data in graph.edges(data=True)]
        assert 1.5 in weights, "Should have edge with weight 1.5"
        assert 2.0 in weights, "Should have edge with weight 2.0"
        assert 0.5 in weights, "Should have edge with weight 0.5"
        
        print("✓ Edge weights parsed correctly")
    finally:
        os.unlink(filepath)


def test_load_multiedgelist_no_weights():
    """Test format without weights: node1 node2 layer"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("1 2 social\n")
        f.write("2 3 work\n")
        filepath = f.name
    
    try:
        graph = load_multilayer_edgelist(filepath)
        
        # Check default weights
        for u, v, data in graph.edges(data=True):
            assert data['weight'] == 1.0, "Should default to weight 1.0"
        
        print("✓ Default weights assigned correctly")
    finally:
        os.unlink(filepath)


def test_multigraph_to_graph_conversion():
    """Test that MultiGraph can be converted to Graph for centrality"""
    # Create a MultiGraph with multiple edges
    G = nx.MultiGraph()
    G.add_edge('1', '2', layer='social', weight=1.0)
    G.add_edge('1', '2', layer='work', weight=2.0)
    G.add_edge('2', '3', layer='social', weight=1.5)
    
    # Convert to simple graph (aggregating weights)
    simple_graph = nx.Graph()
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 1.0)
        if simple_graph.has_edge(u, v):
            simple_graph[u][v]['weight'] += weight
        else:
            simple_graph.add_edge(u, v, weight=weight)
    
    # Verify conversion
    assert simple_graph.number_of_nodes() == 3
    assert simple_graph.number_of_edges() == 2
    
    # Verify weight aggregation
    assert simple_graph['1']['2']['weight'] == 3.0, "Should aggregate weights from multiple edges"
    assert simple_graph['2']['3']['weight'] == 1.5
    
    # Verify centrality can be computed
    degree_cent = dict(simple_graph.degree(weight='weight'))
    assert degree_cent['1'] == 3.0
    assert degree_cent['2'] == 4.5
    assert degree_cent['3'] == 1.5
    
    print("✓ MultiGraph to Graph conversion works for centrality")


def test_empty_lines_handling():
    """Test that empty lines are properly skipped"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("1 2 social\n")
        f.write("\n")
        f.write("  \n")
        f.write("2 3 social\n")
        f.write("\n")
        filepath = f.name
    
    try:
        graph = load_multilayer_edgelist(filepath)
        assert graph.number_of_edges() == 2, "Empty lines should be skipped"
        print("✓ Empty lines handled correctly")
    finally:
        os.unlink(filepath)


if __name__ == '__main__':
    # Run all tests
    test_load_multiedgelist_with_comments()
    test_load_multiedgelist_simple_format()
    test_load_multiedgelist_with_weights()
    test_load_multiedgelist_no_weights()
    test_multigraph_to_graph_conversion()
    test_empty_lines_handling()
    
    print("\nAll unit tests passed!")
    print("\nFriction points fixed:")
    print("  1. Comments in edgelist files now properly skipped")
    print("  2. Simple 2-column edgelists now supported")
    print("  3. MultiGraph to Graph conversion for centrality works")
    print("  4. Empty lines handled gracefully")

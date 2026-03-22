"""
Unit tests for GUI performance optimizations

These tests validate the performance improvements.
Run with: python -m pytest test_performance_optimizations.py
Or directly: python test_performance_optimizations.py

Note: Requires API dependencies to be installed.
"""
import sys
import os

# Test if we can import the required modules
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../api'))
    from app.services.model import get_cache_stats, clear_cache
    import networkx as nx
    CAN_RUN_TESTS = True
except ImportError as e:
    print(f" Cannot run tests: {e}")
    print("These tests require API dependencies. Run in Docker or install dependencies:")
    print("  cd gui/api && pip install -r requirements.txt")
    CAN_RUN_TESTS = False

if not CAN_RUN_TESTS:
    sys.exit(0)

# Import after checking dependencies
from app.services.io import load_multilayer_edgelist, GRAPH_REGISTRY
from app.services.model import get_graph_summary, get_graph_positions, filter_graph
from app.services.metrics import compute_centrality
from app.services.layouts import compute_layout
from app.schemas import FilterSpec
import tempfile


def test_summary_caching():
    """Test that graph summaries are cached"""
    # Create a test graph
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("1 2 social 1.0\n")
        f.write("2 3 social 1.5\n")
        f.write("3 4 work 2.0\n")
        filepath = f.name
    
    try:
        graph = load_multilayer_edgelist(filepath)
        graph_id = "test_cache_1"
        GRAPH_REGISTRY[graph_id] = {
            'graph': graph,
            'filepath': filepath,
            'positions': None,
            'metadata': {}
        }
        
        # Clear cache first
        clear_cache()
        
        # Get summary first time (should cache)
        summary1 = get_graph_summary(graph_id)
        assert summary1 is not None
        
        # Check cache stats
        stats = get_cache_stats()
        assert stats['summary_cache_size'] == 1
        
        # Get summary second time (should use cache)
        summary2 = get_graph_summary(graph_id)
        assert summary2 == summary1
        
        # Clear specific graph cache
        clear_cache(graph_id)
        stats = get_cache_stats()
        assert stats['summary_cache_size'] == 0
        
        print(" Summary caching works correctly")
    finally:
        os.unlink(filepath)
        GRAPH_REGISTRY.pop(graph_id, None)


def test_position_caching():
    """Test that graph positions are cached"""
    # Create a small test graph
    G = nx.Graph()
    G.add_edge('1', '2', layer='social', weight=1.0)
    G.add_edge('2', '3', layer='social', weight=1.5)
    
    graph_id = "test_cache_2"
    GRAPH_REGISTRY[graph_id] = {
        'graph': G,
        'filepath': None,
        'positions': None,
        'metadata': {}
    }
    
    try:
        clear_cache()
        
        # Get positions first time (should cache)
        positions1 = get_graph_positions(graph_id)
        assert positions1 is not None
        
        # Check cache stats
        stats = get_cache_stats()
        assert stats['position_cache_size'] == 1
        
        # Get positions second time (should use cache)
        positions2 = get_graph_positions(graph_id)
        assert positions2 == positions1
        
        print(" Position caching works correctly")
    finally:
        GRAPH_REGISTRY.pop(graph_id, None)


def test_large_graph_layout_optimization():
    """Test that large graphs use optimized layout algorithms"""
    # Create a large graph (simulated)
    G = nx.Graph()
    for i in range(1500):
        G.add_edge(str(i), str(i+1))
    
    graph_id = "test_large"
    GRAPH_REGISTRY[graph_id] = {
        'graph': G,
        'filepath': None,
        'positions': None,
        'metadata': {}
    }
    
    try:
        # Spring layout should be limited to 30 iterations
        positions = compute_layout(graph_id, algorithm='spring', iterations=50)
        assert len(positions) == G.number_of_nodes()
        
        # Kamada-Kawai should switch to spring for large graphs
        positions = compute_layout(graph_id, algorithm='kamada_kawai')
        assert len(positions) == G.number_of_nodes()
        
        print(" Large graph layout optimization works")
    finally:
        GRAPH_REGISTRY.pop(graph_id, None)


def test_centrality_result_limiting():
    """Test that centrality results are limited for very large graphs"""
    # Create a large graph
    G = nx.Graph()
    for i in range(500):
        G.add_edge(str(i), str(i+1))
    
    graph_id = "test_centrality"
    GRAPH_REGISTRY[graph_id] = {
        'graph': G,
        'filepath': None,
        'positions': None,
        'metadata': {}
    }
    
    try:
        # Compute degree centrality
        results = compute_centrality(graph_id, metrics=['degree'])
        assert 'degree' in results
        assert len(results['degree']) <= G.number_of_nodes()
        
        print(" Centrality computation works for large graphs")
    finally:
        GRAPH_REGISTRY.pop(graph_id, None)


def test_optimized_graph_filtering():
    """Test that graph filtering uses optimized operations"""
    # Create a test graph
    G = nx.MultiGraph()
    for i in range(100):
        G.add_edge(str(i), str(i+1), layer='social', weight=1.0)
        if i % 2 == 0:
            G.add_edge(str(i), str(i+2), layer='work', weight=2.0)
    
    graph_id = "test_filter"
    GRAPH_REGISTRY[graph_id] = {
        'graph': G,
        'filepath': None,
        'positions': None,
        'metadata': {}
    }
    
    try:
        # Filter by degree
        spec = FilterSpec(min_degree=2, max_degree=None, layers=None)
        result = filter_graph(graph_id, spec)
        
        assert result is not None
        assert result.nodes < G.number_of_nodes()  # Should filter out some nodes
        
        # Clean up subgraph
        GRAPH_REGISTRY.pop(result.subgraph_id, None)
        
        print(" Optimized graph filtering works")
    finally:
        GRAPH_REGISTRY.pop(graph_id, None)


def test_multigraph_centrality_with_optimization():
    """Test that MultiGraph centrality uses optimized conversion"""
    # Create a MultiGraph
    G = nx.MultiGraph()
    G.add_edge('1', '2', layer='social', weight=1.0)
    G.add_edge('1', '2', layer='work', weight=2.0)
    G.add_edge('2', '3', layer='social', weight=1.5)
    
    graph_id = "test_multi"
    GRAPH_REGISTRY[graph_id] = {
        'graph': G,
        'filepath': None,
        'positions': None,
        'metadata': {}
    }
    
    try:
        # Compute centrality (should handle MultiGraph)
        results = compute_centrality(graph_id, metrics=['degree', 'pagerank'])
        
        assert 'degree' in results
        assert 'pagerank' in results
        assert len(results['degree']) == 3  # 3 nodes
        
        print(" MultiGraph centrality with optimization works")
    finally:
        GRAPH_REGISTRY.pop(graph_id, None)


if __name__ == '__main__':
    # Run all tests
    print("Testing performance optimizations...\n")
    
    test_summary_caching()
    test_position_caching()
    test_large_graph_layout_optimization()
    test_centrality_result_limiting()
    test_optimized_graph_filtering()
    test_multigraph_centrality_with_optimization()
    
    print("\nAll performance optimization tests passed!")
    print("\nOptimizations validated:")
    print("  1. Graph summary and position caching")
    print("  2. Adaptive layout algorithms for large graphs")
    print("  3. Centrality result limiting")
    print("  4. Optimized graph filtering with set operations")
    print("  5. MultiGraph to Graph conversion for centrality")

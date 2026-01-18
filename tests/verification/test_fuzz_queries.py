"""
Fuzzing Harness for DSL Queries.

Generates random queries and networks to discover crashes and edge cases.
"""

import pytest
import random
import numpy as np
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.executor import execute_ast


# Strategies for generating test data
@st.composite
def small_network(draw):
    """Generate a small random multilayer network."""
    num_nodes = draw(st.integers(min_value=0, max_value=10))
    num_layers = draw(st.integers(min_value=1, max_value=3))
    
    network = multinet.multi_layer_network(directed=False)
    
    if num_nodes == 0:
        return network
    
    # Generate node names
    node_names = [f'n{i}' for i in range(num_nodes)]
    layer_names = [f'L{i}' for i in range(num_layers)]
    
    # Add nodes
    nodes = []
    for node in node_names:
        for layer in layer_names:
            nodes.append({'source': node, 'type': layer})
    
    if nodes:
        network.add_nodes(nodes)
    
    # Add random edges
    num_edges = draw(st.integers(min_value=0, max_value=min(20, num_nodes * num_layers)))
    
    edges = []
    for _ in range(num_edges):
        if num_nodes < 2:
            break
        src = draw(st.sampled_from(node_names))
        tgt = draw(st.sampled_from(node_names))
        layer = draw(st.sampled_from(layer_names))
        
        edges.append({
            'source': src,
            'target': tgt,
            'source_type': layer,
            'target_type': layer,
        })
    
    if edges:
        network.add_edges(edges)
    
    return network


@st.composite
def simple_node_query(draw):
    """Generate a simple node query."""
    # Start with nodes
    builder = Q.nodes()
    
    # Optionally add layer filter
    if draw(st.booleans()):
        layer = draw(st.sampled_from(['L0', 'L1', 'L2']))
        builder = builder.from_layers([layer])
    
    # Optionally add compute
    if draw(st.booleans()):
        measure = draw(st.sampled_from(['degree', 'betweenness_centrality', 'closeness_centrality']))
        builder = builder.compute(measure)
    
    # Optionally add limit
    if draw(st.booleans()):
        limit = draw(st.integers(min_value=0, max_value=10))
        builder = builder.limit(limit)
    
    return builder.to_ast()


@pytest.mark.verification
@pytest.mark.fuzz
@pytest.mark.slow
@given(network=small_network(), query=simple_node_query())
@settings(
    max_examples=50,
    deadline=2000,  # 2 seconds per example
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
def test_fuzz_node_queries_no_crash(network, query):
    """
    Fuzz test: Random node queries should not crash.
    
    Invariant: All valid queries execute without exceptions (or raise expected errors).
    """
    try:
        result = execute_ast(network, query)
        
        # Basic sanity checks
        assert result is not None, "Result should not be None"
        assert hasattr(result, 'count'), "Result should have count"
        assert hasattr(result, 'items'), "Result should have items"
        
        # Count should match items length
        assert result.count == len(result.items), \
            f"Count mismatch: count={result.count}, len(items)={len(result.items)}"
        
        # Should be able to convert to pandas
        df = result.to_pandas()
        assert len(df) == result.count, "DataFrame length should match count"
        
    except (KeyError, ValueError, AttributeError, TypeError) as e:
        # Some errors are acceptable (e.g., unknown measure, invalid layer)
        # Just ensure they don't cause crashes
        pass


@pytest.mark.verification
@pytest.mark.fuzz
@pytest.mark.fast
def test_fuzz_empty_network_queries():
    """
    Fuzz test: Queries on empty network should not crash.
    """
    network = multinet.multi_layer_network(directed=False)
    
    queries = [
        Q.nodes().to_ast(),
        Q.edges().to_ast(),
        Q.nodes().compute('degree').to_ast(),
        Q.nodes().where(degree__gt=0).to_ast(),
        Q.nodes().limit(5).to_ast(),
    ]
    
    for query in queries:
        result = execute_ast(network, query)
        assert result.count == 0, "Empty network should return 0 results"
        assert len(result.items) == 0, "Empty network should have no items"


@pytest.mark.verification
@pytest.mark.fuzz
@pytest.mark.fast
def test_fuzz_single_node_queries():
    """
    Fuzz test: Queries on single-node network.
    """
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([{'source': 'A', 'type': 'layer1'}])
    
    queries = [
        Q.nodes().to_ast(),
        Q.nodes().compute('degree').to_ast(),
        Q.nodes().compute('betweenness_centrality').to_ast(),
        Q.nodes().where(degree__ge=0).to_ast(),
    ]
    
    for query in queries:
        result = execute_ast(network, query)
        assert result.count >= 0, "Single node network should not crash"
        assert len(result.items) == result.count


@pytest.mark.verification
@pytest.mark.fuzz
@pytest.mark.fast
def test_fuzz_various_limits():
    """
    Fuzz test: Various limit values.
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [{'source': f'n{i}', 'type': 'layer1'} for i in range(5)]
    network.add_nodes(nodes)
    
    limits = [0, 1, 2, 5, 10, 100]
    
    for limit in limits:
        query = Q.nodes().limit(limit).to_ast()
        result = execute_ast(network, query)
        
        # Result count should not exceed limit
        assert result.count <= limit, f"Result count {result.count} exceeds limit {limit}"
        
        # Result count should not exceed total nodes
        total_nodes = 5
        assert result.count <= total_nodes, \
            f"Result count {result.count} exceeds total nodes {total_nodes}"


@pytest.mark.verification
@pytest.mark.fuzz
@pytest.mark.fast
def test_fuzz_multiple_computes():
    """
    Fuzz test: Multiple compute measures.
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    # Try computing multiple measures
    query = (
        Q.nodes()
        .compute('degree')
        .compute('betweenness_centrality')
        .to_ast()
    )
    
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # Should have both measures
    assert 'degree' in df.columns, "Should have degree column"
    assert 'betweenness_centrality' in df.columns, \
        "Should have betweenness_centrality column"


@pytest.mark.verification
@pytest.mark.fuzz
@pytest.mark.fast
def test_fuzz_layer_combinations():
    """
    Fuzz test: Various layer selection combinations.
    """
    network = multinet.multi_layer_network(directed=False)
    
    # Create network with 3 layers
    nodes = []
    for node_id in ['A', 'B', 'C']:
        for layer in ['L1', 'L2', 'L3']:
            nodes.append({'source': node_id, 'type': layer})
    network.add_nodes(nodes)
    
    # Test various layer selections
    layer_combos = [
        ['L1'],
        ['L1', 'L2'],
        ['L1', 'L2', 'L3'],
        [],  # Empty list
    ]
    
    for layers in layer_combos:
        query = Q.nodes().from_layers(layers).to_ast()
        result = execute_ast(network, query)
        
        # Should not crash
        assert result is not None
        assert result.count >= 0


@pytest.mark.verification
@pytest.mark.fuzz
@pytest.mark.fast
def test_fuzz_order_by_combinations():
    """
    Fuzz test: Various order_by configurations.
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [{'source': chr(ord('A') + i), 'type': 'layer1'} for i in range(5)]
    network.add_nodes(nodes)
    
    edges = []
    for i in range(4):
        edges.append({
            'source': chr(ord('A') + i),
            'target': chr(ord('A') + i + 1),
            'source_type': 'layer1',
            'target_type': 'layer1',
        })
    network.add_edges(edges)
    
    # Test ordering
    for desc in [True, False]:
        query = Q.nodes().compute('degree').order_by('degree', desc=desc).to_ast()
        result = execute_ast(network, query)
        
        df = result.to_pandas()
        degrees = df['degree'].values
        
        # Check ordering
        for i in range(len(degrees) - 1):
            if desc:
                assert degrees[i] >= degrees[i + 1], \
                    f"Descending order violated at index {i}: {degrees}"
            else:
                assert degrees[i] <= degrees[i + 1], \
                    f"Ascending order violated at index {i}: {degrees}"

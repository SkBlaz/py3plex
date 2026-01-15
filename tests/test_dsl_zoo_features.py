"""Tests for new DSL features added for dsl_zoo examples.

Tests:
1. interlayer=True predicate (any inter-layer edge)
2. summarise() method
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L


def test_interlayer_true_predicate():
    """Test interlayer=True special predicate filters any inter-layer edges."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes in two layers
    net.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'work'},
        {'source': 'D', 'type': 'work'},
    ])
    
    # Add edges: 2 intralayer, 2 interlayer
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'C', 'target': 'D', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'work'},
        {'source': 'B', 'target': 'D', 'source_type': 'social', 'target_type': 'work'},
    ])
    
    # Query interlayer edges
    result = Q.edges().where(interlayer=True).execute(net)
    
    # Should get 2 interlayer edges
    assert result.count == 2
    
    # Verify they are indeed interlayer
    df = result.to_pandas()
    for _, row in df.iterrows():
        assert row['source_layer'] != row['target_layer']


def test_intralayer_predicate():
    """Test intralayer=True special predicate filters intralayer edges."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    net.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'work'},
    ])
    
    # Add edges: 1 intralayer, 1 interlayer
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'work'},
    ])
    
    # Query intralayer edges
    result = Q.edges().where(intralayer=True).execute(net)
    
    # Should get 1 intralayer edge
    assert result.count == 1
    
    # Verify it's intralayer
    df = result.to_pandas()
    for _, row in df.iterrows():
        assert row['source_layer'] == row['target_layer']


def test_interlayer_specific_pair():
    """Test interlayer=(layer1, layer2) filters specific layer pair."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    net.add_nodes([
        {'source': 'A', 'type': 'gene'},
        {'source': 'B', 'type': 'disease'},
        {'source': 'C', 'type': 'protein'},
    ])
    
    # Add edges between different layer pairs
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'gene', 'target_type': 'disease'},
        {'source': 'A', 'target': 'C', 'source_type': 'gene', 'target_type': 'protein'},
    ])
    
    # Query edges between gene and disease
    result = Q.edges().where(interlayer=("gene", "disease")).execute(net)
    
    # Should get 1 edge
    assert result.count == 1


def test_summarise_without_grouping():
    """Test summarise() aggregates without grouping."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add simple network
    net.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
    ])
    
    # Summarise edge count
    result = Q.edges().summarise(count="n()").execute(net)
    
    # Check count attribute
    count_val = result.attributes.get('count', {}).get('__global__', 0)
    assert count_val == 2


def test_summarise_with_per_layer_pair_grouping():
    """Test summarise() with per_layer_pair() grouping."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes in two layers
    net.add_nodes([
        {'source': f'N{i}', 'type': 'social'} for i in range(3)
    ] + [
        {'source': f'N{i}', 'type': 'work'} for i in range(3)
    ])
    
    # Add edges
    net.add_edges([
        {'source': 'N0', 'target': 'N1', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'N1', 'target': 'N2', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'N0', 'target': 'N0', 'source_type': 'social', 'target_type': 'work'},
    ])
    
    # Summarise per layer pair
    result = Q.edges().per_layer_pair().summarise(count="n()").end_grouping().execute(net)
    
    # Should have data
    assert result.count > 0
    
    # Check that we have counts
    df = result.to_pandas()
    assert 'count' in df.columns


def test_summarise_expressions():
    """Test various summarise() expressions."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add network with weights
    net.add_nodes([
        {'source': f'N{i}', 'type': 'social'} for i in range(4)
    ])
    net.add_edges([
        {'source': 'N0', 'target': 'N1', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'N1', 'target': 'N2', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
        {'source': 'N2', 'target': 'N3', 'source_type': 'social', 'target_type': 'social', 'weight': 3.0},
    ])
    
    # Test multiple aggregations
    result = (
        Q.edges()
        .per_layer_pair()
        .summarise(
            count="n()",
            mean_weight="mean(weight)",
            sum_weight="sum(weight)"
        )
        .end_grouping()
        .execute(net)
    )
    
    # Check attributes exist
    assert 'count' in result.attributes
    assert 'mean_weight' in result.attributes
    assert 'sum_weight' in result.attributes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

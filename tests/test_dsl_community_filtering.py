"""Test that the DSL community filtering example in documentation works correctly."""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.algorithms.community_detection import community_louvain


def test_dsl_community_filtering_example():
    """Test the exact example shown in the documentation."""
    
    # Create a simple network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    network.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'David', 'type': 'social'},
        {'source': 'Eve', 'type': 'social'},
    ])
    
    # Add edges
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'David', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
    ])
    
    # Step 1: Detect communities
    communities = community_louvain.best_partition(network.core_network)
    assert len(communities) > 0
    
    # Step 2: Store community IDs as node attributes
    for node, comm_id in communities.items():
        network.core_network.nodes[node]['community'] = comm_id
    
    # Step 3: Find high-degree nodes in specific community
    result = (
        Q.nodes()
         .where(community=0)  # Filter by community ID
         .compute("degree", "betweenness_centrality")
         .order_by("-degree")
         .limit(10)
         .execute(network)
    )
    
    # Verify results
    assert result.count > 0
    assert 'degree' in result.attributes
    assert 'betweenness_centrality' in result.attributes
    
    # Step 4: Export for further analysis
    df = result.to_pandas()
    assert df is not None
    assert len(df) > 0
    assert 'id' in df.columns
    assert 'degree' in df.columns
    assert 'betweenness_centrality' in df.columns
    
    # Test CSV export (just create the file)
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=True) as f:
        df.to_csv(f.name, index=False)


def test_dsl_community_filtering_workflow():
    """Test the complete workflow with community filtering."""
    
    network = multinet.multi_layer_network(directed=False)
    
    # Create a network with clear community structure
    nodes = [
        {'source': 'A1', 'type': 'social'},
        {'source': 'A2', 'type': 'social'},
        {'source': 'A3', 'type': 'social'},
        {'source': 'B1', 'type': 'social'},
        {'source': 'B2', 'type': 'social'},
        {'source': 'B3', 'type': 'social'},
    ]
    network.add_nodes(nodes)
    
    # Dense community 1 (A*)
    edges = [
        {'source': 'A1', 'target': 'A2', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A1', 'target': 'A3', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A2', 'target': 'A3', 'source_type': 'social', 'target_type': 'social'},
        # Dense community 2 (B*)
        {'source': 'B1', 'target': 'B2', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B1', 'target': 'B3', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B2', 'target': 'B3', 'source_type': 'social', 'target_type': 'social'},
        # Bridge
        {'source': 'A3', 'target': 'B1', 'source_type': 'social', 'target_type': 'social'},
    ]
    network.add_edges(edges)
    
    # Detect communities
    communities = community_louvain.best_partition(network.core_network)
    
    # Store as attributes
    for node, comm_id in communities.items():
        network.core_network.nodes[node]['community'] = comm_id
    
    # Test filtering by each community
    unique_communities = set(communities.values())
    assert len(unique_communities) >= 2, "Should detect at least 2 communities"
    
    for comm_id in unique_communities:
        result = (
            Q.nodes()
             .where(community=comm_id)
             .compute("degree")
             .execute(network)
        )
        
        assert result.count > 0, f"Community {comm_id} should have nodes"
        
        # Verify all returned nodes have the correct community
        for node in result.nodes:
            actual_comm = network.core_network.nodes[node].get('community')
            assert actual_comm == comm_id, f"Node {node} has wrong community"


if __name__ == '__main__':
    test_dsl_community_filtering_example()
    test_dsl_community_filtering_workflow()
    print("✓ All tests passed!")

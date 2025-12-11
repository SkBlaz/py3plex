"""Example demonstrating edge grouping and coverage with per_layer_pair().

This example showcases the new DSL features for analyzing edges across
layer pairs in multilayer networks:
- per_layer_pair() for grouping edges by (src_layer, dst_layer)
- coverage() for finding edges that appear across multiple layer pairs
- Grouping metadata in QueryResult.meta
- group_summary() for summarizing grouped results
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L


def create_sample_network():
    """Create a sample multilayer network for demonstration."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create nodes in 3 layers
    nodes = []
    for layer in ["social", "work", "family"]:
        for i in range(6):
            nodes.append({'source': f'person{i}', 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges with different patterns per layer
    edges = []
    
    # Social layer: Dense connections among first 4 people
    for i in range(4):
        for j in range(i + 1, 4):
            edges.append({
                'source': f'person{i}', 'target': f'person{j}',
                'source_type': 'social', 'target_type': 'social', 'weight': 1.0
            })
    
    # Work layer: Star topology (person0 as hub)
    for i in range(1, 5):
        edges.append({
            'source': 'person0', 'target': f'person{i}',
            'source_type': 'work', 'target_type': 'work', 'weight': 2.0
        })
    
    # Family layer: Linear chain
    for i in range(5):
        edges.append({
            'source': f'person{i}', 'target': f'person{i+1}',
            'source_type': 'family', 'target_type': 'family', 'weight': 3.0
        })
    
    # Add some inter-layer edges
    edges.append({
        'source': 'person0', 'target': 'person1',
        'source_type': 'social', 'target_type': 'work', 'weight': 1.5
    })
    edges.append({
        'source': 'person1', 'target': 'person2',
        'source_type': 'work', 'target_type': 'family', 'weight': 2.5
    })
    
    network.add_edges(edges)
    
    return network


def example_1_basic_per_layer_pair():
    """Example 1: Basic per_layer_pair grouping."""
    print("=" * 70)
    print("Example 1: Basic per_layer_pair grouping")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Query edges grouped by layer pairs
    result = (
        Q.edges()
         .from_layers(L["*"])
         .per_layer_pair()
         .execute(network)
    )
    
    print(f"\nFound {len(result)} edges across all layer pairs")
    
    # Access grouping metadata
    if "grouping" in result.meta:
        grouping = result.meta["grouping"]
        print(f"\nGrouping kind: {grouping['kind']}")
        print(f"Grouping target: {grouping['target']}")
        print(f"Grouping keys: {grouping['keys']}")
        print(f"Number of groups: {len(grouping['groups'])}")
    
    # Get summary of groups
    summary = result.group_summary()
    print("\nGroup Summary:")
    print(summary.to_string())


def example_2_top_k_per_layer_pair():
    """Example 2: Top-k edges per layer pair."""
    print("\n" + "=" * 70)
    print("Example 2: Top-k edges per layer pair")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Get top-3 edges per layer pair by weight
    result = (
        Q.edges()
         .from_layers(L["*"])
         .per_layer_pair()
            .top_k(3, "weight")
         .end_grouping()
         .execute(network)
    )
    
    df = result.to_pandas()
    print(f"\nTop-3 edges per layer pair (total: {len(df)} edges):")
    print(df[['source', 'target', 'source_layer', 'target_layer', 'weight']].to_string())
    
    # Group summary
    summary = result.group_summary()
    print("\nEdges per layer pair:")
    print(summary.to_string())


def example_3_edge_coverage():
    """Example 3: Coverage filtering for edges."""
    print("\n" + "=" * 70)
    print("Example 3: Coverage filtering for edges")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Find edges that appear in top-3 in at least 2 layer pairs
    result = (
        Q.edges()
         .from_layers(L["*"])
         .per_layer_pair()
            .top_k(3, "weight")
         .end_grouping()
         .coverage(mode="at_least", k=2)
         .execute(network)
    )
    
    df = result.to_pandas()
    print(f"\nEdges appearing in top-3 of at least 2 layer pairs:")
    if len(df) > 0:
        print(df[['source', 'target', 'source_layer', 'target_layer', 'weight']].to_string())
    else:
        print("  (No edges meet this criterion)")
    
    # Show which edges appear across multiple layer pairs
    if len(df) > 0:
        edge_counts = df.groupby(['source', 'target']).size()
        print("\nEdge appearance counts:")
        for (src, tgt), count in edge_counts.items():
            print(f"  {src} - {tgt}: appears in {count} layer pair(s)")


def example_4_multiindex_dataframe():
    """Example 4: Using multiindex in pandas output."""
    print("\n" + "=" * 70)
    print("Example 4: Using multiindex in pandas output")
    print("=" * 70)
    
    network = create_sample_network()
    
    result = (
        Q.edges()
         .from_layers(L["social", "work"])
         .per_layer_pair()
            .top_k(3, "weight")
         .end_grouping()
         .execute(network)
    )
    
    # Get DataFrame with multiindex
    df = result.to_pandas(multiindex=True)
    print("\nDataFrame with multiindex on (source_layer, target_layer):")
    print(df[['source', 'target', 'weight']].head(10).to_string())


def example_5_comparing_node_and_edge_grouping():
    """Example 5: Comparing node and edge grouping."""
    print("\n" + "=" * 70)
    print("Example 5: Comparing node and edge grouping")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Node grouping with per_layer
    node_result = (
        Q.nodes()
         .from_layers(L["*"])
         .per_layer()
            .top_k(3, "degree")
         .end_grouping()
         .execute(network)
    )
    
    print("\nNode grouping metadata:")
    if "grouping" in node_result.meta:
        grouping = node_result.meta["grouping"]
        print(f"  Kind: {grouping['kind']}")
        print(f"  Keys: {grouping['keys']}")
    
    node_summary = node_result.group_summary()
    print("\nNodes per layer:")
    print(node_summary.to_string())
    
    # Edge grouping with per_layer_pair
    edge_result = (
        Q.edges()
         .from_layers(L["*"])
         .per_layer_pair()
            .top_k(3, "weight")
         .end_grouping()
         .execute(network)
    )
    
    print("\nEdge grouping metadata:")
    if "grouping" in edge_result.meta:
        grouping = edge_result.meta["grouping"]
        print(f"  Kind: {grouping['kind']}")
        print(f"  Keys: {grouping['keys']}")
    
    edge_summary = edge_result.group_summary()
    print("\nEdges per layer pair:")
    print(edge_summary.to_string())


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("DSL Edge Grouping and Coverage Examples")
    print("=" * 70)
    
    example_1_basic_per_layer_pair()
    example_2_top_k_per_layer_pair()
    example_3_edge_coverage()
    example_4_multiindex_dataframe()
    example_5_comparing_node_and_edge_grouping()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)

"""Example demonstrating semiring algebra in py3plex.

This script shows how to use the S builder for:
1. Shortest paths (min-plus semiring)
2. Reachability analysis (boolean semiring)
3. Most reliable paths (max-times semiring)
4. Transitive closure
"""

from py3plex.core import multinet
from py3plex.dsl import S, L


def create_sample_network():
    """Create a sample multilayer network for demonstration."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'Diana', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob', 'type': 'work'},
        {'source': 'Charlie', 'type': 'work'},
    ]
    net.add_nodes(nodes)
    
    # Add edges with weights
    edges = [
        # Social layer
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0, 'reliability': 0.9},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0, 'reliability': 0.8},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 5.0, 'reliability': 0.6},
        {'source': 'Charlie', 'target': 'Diana', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0, 'reliability': 0.95},
        # Work layer
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 3.0, 'reliability': 0.7},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0, 'reliability': 0.85},
        # Cross-layer edge
        {'source': 'Alice', 'target': 'Alice', 'source_type': 'social', 'target_type': 'work', 'weight': 0.5, 'reliability': 1.0},
    ]
    net.add_edges(edges)
    
    return net


def example_shortest_paths():
    """Example: Find shortest paths using min-plus semiring."""
    print("=" * 60)
    print("Example 1: Shortest Paths (Min-Plus Semiring)")
    print("=" * 60)
    
    net = create_sample_network()
    
    # Find shortest paths from Alice to all other nodes
    result = (
        S.paths()
        .from_node('Alice')
        .semiring('min_plus')
        .lift(attr='weight', default=1.0)
        .witness(True)  # Enable path reconstruction
        .execute(net)
    )
    
    df = result.to_pandas()
    
    # Extract results (QueryResult.to_pandas() returns items as dicts in 'id' column)
    # This is a known limitation - direct dict access is cleaner for now
    print("\nShortest distances from Alice:")
    for item in result.items:
        if isinstance(item['node'], str):  # Filter out intermediate artifacts
            print(f"  {item['node']}: {item['value']}")
    
    # Show path to Charlie
    for item in result.items:
        if item['node'] == 'Charlie' and item.get('path'):
            print(f"\nPath to Charlie: {item['path']}")
            print(f"Distance: {item['value']}")
            break
    
    # Show provenance
    prov = result.meta['provenance']['algebra']
    print(f"\nAlgorithm used: {prov['backend']['algorithm']}")
    print(f"Execution time: {prov['performance']['total_time']:.4f}s")


def example_reachability():
    """Example: Reachability analysis with boolean semiring."""
    print("\n" + "=" * 60)
    print("Example 2: Reachability Analysis (Boolean Semiring)")
    print("=" * 60)
    
    net = create_sample_network()
    
    # Check which nodes are reachable from Alice
    result = (
        S.paths()
        .from_node('Alice')
        .semiring('boolean')
        .lift(attr=None, default=True)  # No weights needed
        .execute(net)
    )
    
    # Extract reachable nodes
    reachable = [item['node'] for item in result.items 
                 if isinstance(item['node'], str) and item['value'] == True]
    
    print(f"\nNodes reachable from Alice: {reachable}")


def example_reliable_paths():
    """Example: Most reliable paths with max-times semiring."""
    print("\n" + "=" * 60)
    print("Example 3: Most Reliable Paths (Max-Times Semiring)")
    print("=" * 60)
    
    net = create_sample_network()
    
    # Find most reliable path (maximize reliability product)
    result = (
        S.paths()
        .from_node('Alice')
        .to_node('Diana')
        .semiring('max_times')
        .lift(attr='reliability', default=1.0)
        .execute(net)
    )
    
    # Find Diana's reliability
    for item in result.items:
        if item['node'] == 'Diana':
            reliability = item['value']
            print(f"\nMost reliable path reliability to Diana: {reliability:.4f}")
            print(f"(This is the product of edge reliabilities along the best path)")
            break


def example_closure():
    """Example: Transitive closure with boolean semiring."""
    print("\n" + "=" * 60)
    print("Example 4: Transitive Closure (Boolean Semiring)")
    print("=" * 60)
    
    net = create_sample_network()
    
    # Compute reachability closure
    result = (
        S.closure()
        .semiring('boolean')
        .from_layers(L['social'])  # Only social layer
        .execute(net)
    )
    
    # Extract reachable pairs
    reachable_pairs = [(item['source'], item['target']) 
                       for item in result.items if item['value'] == True]
    
    print(f"\nReachable pairs in social layer ({len(reachable_pairs)} pairs):")
    for src, dst in reachable_pairs[:10]:
        print(f"  {src} -> {dst}")


def example_layer_filtering():
    """Example: Layer filtering and cross-layer edges."""
    print("\n" + "=" * 60)
    print("Example 5: Layer Filtering and Cross-Layer Edges")
    print("=" * 60)
    
    net = create_sample_network()
    
    # Shortest paths only in social layer
    result_social = (
        S.paths()
        .from_node('Alice')
        .to_node('Charlie')
        .semiring('min_plus')
        .lift(attr='weight', default=1.0)
        .from_layers(L['social'])
        .execute(net)
    )
    
    dist_social = None
    for item in result_social.items:
        if item['node'] == 'Charlie':
            dist_social = item['value']
            break
    
    # Shortest paths allowing cross-layer
    result_cross = (
        S.paths()
        .from_node('Alice')
        .to_node('Charlie')
        .semiring('min_plus')
        .lift(attr='weight', default=1.0)
        .crossing_layers(mode='allowed')
        .execute(net)
    )
    
    dist_cross = None
    for item in result_cross.items:
        if item['node'] == 'Charlie':
            dist_cross = item['value']
            break
    
    if dist_social is not None and dist_cross is not None:
        print(f"\nShortest distance to Charlie (social layer only): {dist_social}")
        print(f"Shortest distance to Charlie (with cross-layer): {dist_cross}")
        print(f"Benefit of cross-layer edges: {dist_social - dist_cross:.2f}")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Semiring Algebra Examples in py3plex")
    print("=" * 60)
    
    example_shortest_paths()
    example_reachability()
    example_reliable_paths()
    example_closure()
    example_layer_filtering()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)

"""Example demonstrating temporal multilayer network features.

This script shows how to:
1. Create a temporal multilayer network
2. Add time-stamped edges
3. Query by time ranges
4. Create snapshots at specific times
5. Iterate over sliding windows
6. Use streaming algorithms
"""

from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.algorithms.temporal import streaming_pagerank, streaming_community_change
import networkx as nx


def create_sample_temporal_network():
    """Create a sample temporal multilayer network."""
    print("Creating temporal multilayer network...")
    
    tnet = TemporalMultiLayerNetwork(directed=True)
    
    # Add time-stamped edges representing network evolution
    # Time 0-100: Initial network structure
    edges_t1 = [
        ('Alice', 'social', 'Bob', 'social', 50.0, 1.0),
        ('Bob', 'social', 'Charlie', 'social', 50.0, 1.0),
        ('Charlie', 'social', 'Alice', 'social', 50.0, 1.0),
    ]
    
    # Time 100-200: Network grows
    edges_t2 = [
        ('Alice', 'social', 'David', 'social', 150.0, 1.0),
        ('David', 'social', 'Eve', 'social', 150.0, 1.0),
        ('Eve', 'social', 'Bob', 'social', 150.0, 1.0),
    ]
    
    # Time 200-300: More connections
    edges_t3 = [
        ('David', 'social', 'Charlie', 'social', 250.0, 1.0),
        ('Eve', 'social', 'Alice', 'social', 250.0, 1.0),
    ]
    
    # Add all edges
    all_edges = edges_t1 + edges_t2 + edges_t3
    tnet.add_edges(all_edges, input_type="tuple")
    
    print(f"Created network with {tnet.number_of_edges()} temporal edges")
    print(f"Time range: {tnet.time_range()}")
    
    return tnet


def demonstrate_time_slicing(tnet):
    """Demonstrate time-based slicing."""
    print("\n=== Time-Based Slicing ===")
    
    # Get edges in a specific time range
    print("\nEdges between t=100 and t=200:")
    edges = list(tnet.edges_between(100.0, 200.0))
    for edge in edges:
        print(f"  {edge['source']} -> {edge['target']} at t={edge['t']}")
    
    # Create a time-sliced subnetwork
    sliced = tnet.slice_time_window(100.0, 200.0)
    print(f"\nSliced network has {sliced.number_of_edges()} edges")


def demonstrate_snapshots(tnet):
    """Demonstrate snapshot creation."""
    print("\n=== Network Snapshots ===")
    
    # Cumulative snapshot at t=150
    snapshot_cumulative = tnet.snapshot_at(150.0, mode="up_to")
    print(f"\nCumulative snapshot at t=150:")
    print(f"  Nodes: {snapshot_cumulative.core_network.number_of_nodes()}")
    print(f"  Edges: {snapshot_cumulative.core_network.number_of_edges()}")
    
    # Exact snapshot at t=150
    snapshot_exact = tnet.snapshot_at(150.0, mode="exact")
    print(f"\nExact snapshot at t=150:")
    print(f"  Edges: {snapshot_exact.core_network.number_of_edges()}")


def demonstrate_sliding_windows(tnet):
    """Demonstrate sliding window iteration."""
    print("\n=== Sliding Windows ===")
    
    # Non-overlapping windows
    print("\nNon-overlapping windows (size=100):")
    for t_start, t_end, window_net in tnet.window_iter(window_size=100.0):
        print(f"  Window [{t_start:.0f}, {t_end:.0f}]: {window_net.number_of_edges()} edges")
    
    # Overlapping windows
    print("\nOverlapping windows (size=100, step=50):")
    for t_start, t_end, window_net in tnet.window_iter(window_size=100.0, step=50.0):
        print(f"  Window [{t_start:.0f}, {t_end:.0f}]: {window_net.number_of_edges()} edges")


def demonstrate_streaming_pagerank(tnet):
    """Demonstrate streaming PageRank."""
    print("\n=== Streaming PageRank ===")
    
    print("\nComputing PageRank over time windows:")
    for t_start, t_end, scores in streaming_pagerank(
        tnet,
        window_size=100.0,
        max_iter_per_window=10,
        normalize=True,
    ):
        print(f"\nWindow [{t_start:.0f}, {t_end:.0f}]:")
        # Show top 3 nodes
        top_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        for node, score in top_nodes:
            print(f"  {node}: {score:.4f}")


def demonstrate_streaming_community(tnet):
    """Demonstrate streaming community detection."""
    print("\n=== Streaming Community Detection ===")
    
    # Simple community detector using connected components
    def detect_communities(network):
        graph = network.core_network if hasattr(network, 'core_network') else network
        communities = {}
        for i, component in enumerate(nx.weakly_connected_components(graph)):
            for node in component:
                communities[node] = i
        return communities
    
    print("\nDetecting community changes over time:")
    for t_start, t_end, communities, change_score in streaming_community_change(
        tnet,
        detect_communities,
        window_size=100.0,
    ):
        num_communities = len(set(communities.values()))
        print(f"\nWindow [{t_start:.0f}, {t_end:.0f}]:")
        print(f"  Number of communities: {num_communities}")
        print(f"  Change score: {change_score:.4f}")
        
        # Show community membership
        if communities:
            comm_members = {}
            for node, comm_id in communities.items():
                comm_members.setdefault(comm_id, []).append(node)
            
            for comm_id, members in sorted(comm_members.items()):
                # Convert node tuples to strings if needed
                member_strs = [str(m) if isinstance(m, tuple) else m for m in members]
                print(f"  Community {comm_id}: {', '.join(member_strs)}")


def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("Temporal Multilayer Network Example")
    print("=" * 60)
    
    # Create temporal network
    tnet = create_sample_temporal_network()
    
    # Demonstrate features
    demonstrate_time_slicing(tnet)
    demonstrate_snapshots(tnet)
    demonstrate_sliding_windows(tnet)
    demonstrate_streaming_pagerank(tnet)
    demonstrate_streaming_community(tnet)
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

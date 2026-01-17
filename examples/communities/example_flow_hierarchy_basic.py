"""
Example: Basic Usage of Hierarchical Flow-Based Community Detection

This example demonstrates the basic usage of the flow_hierarchical_communities
algorithm on a simple network with clear community structure.
"""

from py3plex.core import multinet
from py3plex.algorithms.community_detection import flow_hierarchical_communities


def main():
    """Run basic flow hierarchy example."""
    print("=" * 70)
    print("Hierarchical Flow-Based Community Detection - Basic Example")
    print("=" * 70)
    print()

    # Create a network with two clear communities connected by a bridge
    print("Creating network with two communities...")
    net = multinet.multi_layer_network(directed=False)
    
    # Community 1: Triangle A-B-C
    net.add_edges([
        ["A", "L1", "B", "L1", 1.0],
        ["B", "L1", "C", "L1", 1.0],
        ["C", "L1", "A", "L1", 1.0],
    ], input_type="list")
    
    # Community 2: Triangle D-E-F
    net.add_edges([
        ["D", "L1", "E", "L1", 1.0],
        ["E", "L1", "F", "L1", 1.0],
        ["F", "L1", "D", "L1", 1.0],
    ], input_type="list")
    
    # Bridge between communities
    net.add_edges([
        ["C", "L1", "D", "L1", 0.3],  # Weak connection
    ], input_type="list")
    
    print(f"Network created: {len(list(net.get_nodes()))} nodes")
    print()

    # Run hierarchical flow-based community detection
    print("Running hierarchical flow detection...")
    result = flow_hierarchical_communities(
        net,
        approx="mc",       # Use Monte Carlo approximation
        n_walks=200,       # Number of random walks per node
        seed=42            # For reproducibility
    )
    print("✓ Detection complete")
    print()

    # Display summary
    print(result.summary())
    print()

    # Explore hierarchy levels
    print("Hierarchy exploration:")
    print("-" * 70)
    for scale in sorted(result.hierarchy_levels.keys()):
        partition = result.hierarchy_levels[scale]
        n_communities = len(set(partition.values()))
        stability = result.stability_scores[scale]
        print(f"Scale {scale:6.1f}: {n_communities:2d} communities, stability = {stability:8.4f}")
    print()

    # Get best partition (maximum stability)
    print("Best partition (maximum stability):")
    print("-" * 70)
    best_partition = result.get_partition()
    
    # Group nodes by community
    communities = {}
    for node, comm_id in best_partition.items():
        if comm_id not in communities:
            communities[comm_id] = []
        communities[comm_id].append(node)
    
    for comm_id, members in sorted(communities.items()):
        node_names = [node[0] for node in members]  # Extract node names (not layers)
        print(f"Community {comm_id}: {', '.join(sorted(node_names))}")
    print()

    # Get partition with specific number of communities
    print("Partition with 2 communities:")
    print("-" * 70)
    partition_2 = result.get_flat_partition(n_communities=2)
    
    communities_2 = {}
    for node, comm_id in partition_2.items():
        if comm_id not in communities_2:
            communities_2[comm_id] = []
        communities_2[comm_id].append(node)
    
    for comm_id, members in sorted(communities_2.items()):
        node_names = [node[0] for node in members]
        print(f"Community {comm_id}: {', '.join(sorted(node_names))}")
    print()

    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

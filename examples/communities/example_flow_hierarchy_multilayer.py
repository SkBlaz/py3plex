"""
Example: Multilayer Flow-Based Community Detection

This example demonstrates flow hierarchy detection on a multilayer network,
showing how communities can span multiple layers and how the alpha parameter
controls interlayer coupling.
"""

from py3plex.core import multinet
from py3plex.algorithms.community_detection import flow_hierarchical_communities


def main():
    """Run multilayer flow hierarchy example."""
    print("=" * 70)
    print("Hierarchical Flow-Based Community Detection - Multilayer Example")
    print("=" * 70)
    print()

    # Create a multilayer social-biological network
    print("Creating multilayer network (social + collaboration layers)...")
    net = multinet.multi_layer_network(directed=False)
    
    # Social layer: Two friend groups
    print("  Adding social layer...")
    net.add_edges([
        # Group 1: Alice, Bob, Carol
        ["Alice", "social", "Bob", "social", 1.0],
        ["Bob", "social", "Carol", "social", 1.0],
        ["Carol", "social", "Alice", "social", 1.0],
        # Group 2: David, Eve, Frank
        ["David", "social", "Eve", "social", 1.0],
        ["Eve", "social", "Frank", "social", 1.0],
        ["Frank", "social", "David", "social", 1.0],
        # Weak social tie across groups
        ["Carol", "social", "David", "social", 0.3],
    ], input_type="list")
    
    # Collaboration layer: Different grouping structure
    print("  Adding collaboration layer...")
    net.add_edges([
        # Project team 1: Alice, Carol, Eve
        ["Alice", "collab", "Carol", "collab", 1.0],
        ["Carol", "collab", "Eve", "collab", 1.0],
        ["Eve", "collab", "Alice", "collab", 1.0],
        # Project team 2: Bob, David, Frank
        ["Bob", "collab", "David", "collab", 1.0],
        ["David", "collab", "Frank", "collab", 1.0],
        ["Frank", "collab", "Bob", "collab", 1.0],
    ], input_type="list")
    
    n_nodes = len(list(net.get_nodes()))
    print(f"Multilayer network created: {n_nodes} node-layer pairs")
    print()

    # Run with different alpha values to see coupling effect
    print("Comparing different interlayer coupling strengths...")
    print("-" * 70)
    
    # High alpha (0.9): Layers are more independent
    print("\n1. High alpha (α=0.9) - Layers mostly independent:")
    result_high = flow_hierarchical_communities(
        net,
        alpha=0.9,        # High intralayer weight
        approx="mc",
        n_walks=150,
        seed=42
    )
    
    partition_high = result_high.get_partition()
    n_comms_high = len(set(partition_high.values()))
    best_scale_high = max(result_high.stability_scores, key=result_high.stability_scores.get)
    stability_high = result_high.stability_scores[best_scale_high]
    
    print(f"   Best partition: {n_comms_high} communities")
    print(f"   Stability: {stability_high:.4f}")
    print(f"   Scale: {best_scale_high}")
    
    # Medium alpha (0.5): Balanced coupling
    print("\n2. Medium alpha (α=0.5) - Balanced layer coupling:")
    result_medium = flow_hierarchical_communities(
        net,
        alpha=0.5,        # Balanced
        approx="mc",
        n_walks=150,
        seed=42
    )
    
    partition_medium = result_medium.get_partition()
    n_comms_medium = len(set(partition_medium.values()))
    best_scale_medium = max(result_medium.stability_scores, key=result_medium.stability_scores.get)
    stability_medium = result_medium.stability_scores[best_scale_medium]
    
    print(f"   Best partition: {n_comms_medium} communities")
    print(f"   Stability: {stability_medium:.4f}")
    print(f"   Scale: {best_scale_medium}")
    
    # Low alpha (0.2): Strong interlayer coupling
    print("\n3. Low alpha (α=0.2) - Strong interlayer coupling:")
    result_low = flow_hierarchical_communities(
        net,
        alpha=0.2,        # Low intralayer weight, high interlayer
        approx="mc",
        n_walks=150,
        seed=42
    )
    
    partition_low = result_low.get_partition()
    n_comms_low = len(set(partition_low.values()))
    best_scale_low = max(result_low.stability_scores, key=result_low.stability_scores.get)
    stability_low = result_low.stability_scores[best_scale_low]
    
    print(f"   Best partition: {n_comms_low} communities")
    print(f"   Stability: {stability_low:.4f}")
    print(f"   Scale: {best_scale_low}")
    print()

    # Detailed analysis of medium coupling result
    print("=" * 70)
    print("Detailed Analysis (α=0.5)")
    print("=" * 70)
    print()
    print(result_medium.summary())
    print()

    # Show hierarchy
    print("Hierarchy levels:")
    print("-" * 70)
    for scale in sorted(result_medium.hierarchy_levels.keys())[:5]:  # First 5 scales
        partition = result_medium.hierarchy_levels[scale]
        n_communities = len(set(partition.values()))
        stability = result_medium.stability_scores[scale]
        print(f"Scale {scale:6.1f}: {n_communities:2d} communities, stability = {stability:10.4f}")
    print()

    # Show communities at best scale
    print(f"Communities at best scale (scale={best_scale_medium}):")
    print("-" * 70)
    
    communities = {}
    for node_layer, comm_id in partition_medium.items():
        if comm_id not in communities:
            communities[comm_id] = []
        communities[comm_id].append(node_layer)
    
    for comm_id in sorted(communities.keys())[:5]:  # Show first 5 communities
        members = communities[comm_id]
        print(f"\nCommunity {comm_id}:")
        # Group by layer
        by_layer = {}
        for node, layer in members:
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(node)
        
        for layer in sorted(by_layer.keys()):
            nodes_str = ", ".join(sorted(by_layer[layer]))
            print(f"  {layer:10s}: {nodes_str}")
    
    print()
    print("=" * 70)
    print("Multilayer example complete!")
    print("=" * 70)
    print()
    print("Key insights:")
    print("- Alpha controls layer independence vs coupling")
    print("- High alpha: Communities reflect within-layer structure")
    print("- Low alpha: Communities bridge layers based on node identity")
    print("- Hierarchy reveals communities at multiple scales")


if __name__ == "__main__":
    main()

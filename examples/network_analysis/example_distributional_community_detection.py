"""
Distributional Community Detection Example: Uncertainty-Aware Partitioning

This example demonstrates how to use distributional community detection to:
1. Quantify uncertainty in community assignments
2. Identify stable "core" nodes vs uncertain "boundary" nodes
3. Use co-association matrices to understand partition stability

Distributional community detection runs community detection multiple times
(with different seeds or on perturbed networks) to produce a distribution
over partitions. This enables computing:
- Consensus partition (most representative partition)
- Per-node confidence scores
- Co-association matrix P(node_i, node_j in same community)

Example output:
- Consensus community assignments
- Node confidence scores identifying stable vs boundary nodes
- Filtered "stable core" subgraph with high-confidence nodes only
"""

from __future__ import annotations

import argparse

import numpy as np

from py3plex.core import multinet
from py3plex.algorithms.community_detection import multilayer_louvain_distribution
from py3plex.uncertainty import CommunityDistribution


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Distributional community detection with uncertainty quantification"
    )
    parser.add_argument(
        "--n_runs",
        type=int,
        default=100,
        help="Number of community detection runs (default: 100)",
    )
    parser.add_argument(
        "--resampling",
        choices=["seed", "perturbation", "bootstrap"],
        default="perturbation",
        help="Resampling strategy (default: perturbation)",
    )
    parser.add_argument(
        "--edge_drop_p",
        type=float,
        default=0.05,
        help="Edge drop probability for perturbation resampling (default: 0.05)",
    )
    parser.add_argument(
        "--confidence_threshold",
        type=float,
        default=0.8,
        help="Confidence threshold for stable core filtering (default: 0.8)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--n_jobs",
        type=int,
        default=1,
        help="Number of parallel jobs (default: 1)",
    )
    return parser.parse_args()


def create_example_network() -> multinet.multi_layer_network:
    """Create a multilayer network with community structure.

    The network has two clear communities in layer 1, with some
    inter-community connections and a second layer with different structure.
    """
    net = multinet.multi_layer_network(directed=False)

    # Layer 1: Two communities with weak inter-community edges
    # Community 1: A-B-C (triangle)
    edges_l1_c1 = [
        ['A', 'L1', 'B', 'L1', 1.0],
        ['B', 'L1', 'C', 'L1', 1.0],
        ['C', 'L1', 'A', 'L1', 1.0],
    ]

    # Community 2: D-E-F (triangle)
    edges_l1_c2 = [
        ['D', 'L1', 'E', 'L1', 1.0],
        ['E', 'L1', 'F', 'L1', 1.0],
        ['F', 'L1', 'D', 'L1', 1.0],
    ]

    # Weak inter-community edges (boundary nodes C and D)
    edges_l1_inter = [
        ['C', 'L1', 'D', 'L1', 0.2],
    ]

    # Layer 2: Different community structure
    edges_l2 = [
        ['A', 'L2', 'D', 'L2', 1.0],
        ['B', 'L2', 'E', 'L2', 1.0],
        ['C', 'L2', 'F', 'L2', 1.0],
    ]

    all_edges = edges_l1_c1 + edges_l1_c2 + edges_l1_inter + edges_l2
    net.add_edges(all_edges, input_type='list')

    return net


def print_network_stats(net: multinet.multi_layer_network):
    """Print basic network statistics."""
    print("\n" + "=" * 70)
    print("NETWORK STATISTICS")
    print("=" * 70)

    nodes = list(net.get_nodes())
    edges = list(net.get_edges())
    layers = list(net.get_layers())

    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")
    print(f"  Layers: {len(layers)} {layers}")
    print()


def run_distributional_community_detection(
    net: multinet.multi_layer_network,
    n_runs: int,
    resampling: str,
    edge_drop_p: float,
    seed: int,
    n_jobs: int,
) -> CommunityDistribution:
    """Run distributional community detection."""
    print("=" * 70)
    print("DISTRIBUTIONAL COMMUNITY DETECTION")
    print("=" * 70)
    print(f"  Strategy: {resampling}")
    print(f"  Runs: {n_runs}")
    if resampling == "perturbation":
        print(f"  Edge drop probability: {edge_drop_p}")
    print(f"  Seed: {seed}")
    print(f"  Parallel jobs: {n_jobs}")
    print()

    perturbation_params = {'edge_drop_p': edge_drop_p} if resampling == "perturbation" else None

    dist = multilayer_louvain_distribution(
        net,
        n_runs=n_runs,
        resampling=resampling,
        perturbation_params=perturbation_params,
        gamma=1.0,
        seed=seed,
        n_jobs=n_jobs,
        weight_by='modularity',
        coassoc_mode='auto',
    )

    print(f" Generated distribution with {dist.n_partitions} partitions")
    print(f" Mean modularity: {dist.meta['mean_modularity']:.4f} +/- {dist.meta['std_modularity']:.4f}")
    print()

    return dist


def analyze_consensus_partition(dist: CommunityDistribution):
    """Analyze and display consensus partition."""
    print("=" * 70)
    print("CONSENSUS PARTITION")
    print("=" * 70)

    consensus = dist.consensus_partition()
    nodes = dist.nodes

    # Group nodes by consensus community
    communities = {}
    for i, node in enumerate(nodes):
        comm = int(consensus[i])
        if comm not in communities:
            communities[comm] = []
        communities[comm].append(node)

    print(f"  Number of communities: {len(communities)}")
    print()

    for comm_id, members in sorted(communities.items()):
        print(f"  Community {comm_id}: {len(members)} nodes")
        # Format node list (show first few)
        member_strs = [f"{n[0]}/{n[1]}" if isinstance(n, tuple) else str(n)
                       for n in members[:10]]
        if len(members) > 10:
            member_strs.append(f"... +{len(members)-10} more")
        print(f"    Members: {', '.join(member_strs)}")

    print()


def analyze_node_confidence(dist: CommunityDistribution, threshold: float):
    """Analyze per-node confidence and identify stable core."""
    print("=" * 70)
    print("NODE CONFIDENCE ANALYSIS")
    print("=" * 70)

    confidence = dist.node_confidence()
    entropy = dist.node_entropy()
    margin = dist.node_margin()

    nodes = dist.nodes
    consensus = dist.consensus_partition()

    # Compute statistics
    mean_conf = np.mean(confidence)
    std_conf = np.std(confidence)

    print(f"  Mean confidence: {mean_conf:.4f} +/- {std_conf:.4f}")
    print(f"  Range: [{np.min(confidence):.4f}, {np.max(confidence):.4f}]")
    print()

    # Identify low-confidence (boundary) nodes
    low_conf_mask = confidence < threshold
    boundary_nodes = [
        (nodes[i], confidence[i], entropy[i], int(consensus[i]))
        for i in range(len(nodes)) if low_conf_mask[i]
    ]

    if boundary_nodes:
        print(f"  Boundary nodes (confidence < {threshold}):")
        boundary_nodes.sort(key=lambda x: x[1])  # Sort by confidence
        for node, conf, ent, comm in boundary_nodes[:10]:
            node_str = f"{node[0]}/{node[1]}" if isinstance(node, tuple) else str(node)
            print(f"    {node_str:15s} | conf={conf:.3f} ent={ent:.3f} comm={comm}")

        if len(boundary_nodes) > 10:
            print(f"    ... +{len(boundary_nodes)-10} more boundary nodes")
    else:
        print(f"  No boundary nodes (all confidence >= {threshold})")

    print()

    # Identify high-confidence (stable core) nodes
    stable_mask = confidence >= threshold
    stable_nodes = [
        (nodes[i], confidence[i], int(consensus[i]))
        for i in range(len(nodes)) if stable_mask[i]
    ]

    print(f"  Stable core nodes (confidence >= {threshold}):")
    print(f"    Count: {len(stable_nodes)} / {len(nodes)} ({100*len(stable_nodes)/len(nodes):.1f}%)")

    if stable_nodes:
        # Show a few examples
        stable_nodes.sort(key=lambda x: x[1], reverse=True)  # Sort by confidence descending
        print("    Top stable nodes:")
        for node, conf, comm in stable_nodes[:5]:
            node_str = f"{node[0]}/{node[1]}" if isinstance(node, tuple) else str(node)
            print(f"      {node_str:15s} | conf={conf:.3f} comm={comm}")

    print()

    return stable_nodes, boundary_nodes


def analyze_coassociation(dist: CommunityDistribution):
    """Analyze co-association matrix."""
    print("=" * 70)
    print("CO-ASSOCIATION MATRIX")
    print("=" * 70)

    # For small networks, use dense; for large use sparse
    mode = 'dense' if dist.n_nodes < 20 else 'sparse'

    print(f"  Mode: {mode}")
    print(f"  Shape: ({dist.n_nodes}, {dist.n_nodes})")
    print()

    if mode == 'dense':
        coassoc = dist.coassociation(mode='dense')

        # Show statistics
        # Remove diagonal (always 1)
        off_diag = coassoc[~np.eye(coassoc.shape[0], dtype=bool)]

        print(f"  Mean co-association (off-diagonal): {np.mean(off_diag):.4f}")
        print(f"  Std co-association: {np.std(off_diag):.4f}")
        print(f"  Range: [{np.min(off_diag):.4f}, {np.max(off_diag):.4f}]")
        print()

        # Show a few high co-association pairs
        print("  Strong co-associations (top 5):")
        # Get upper triangle indices (exclude diagonal)
        i_upper, j_upper = np.triu_indices_from(coassoc, k=1)
        coassoc_pairs = list(zip(i_upper, j_upper, coassoc[i_upper, j_upper]))
        coassoc_pairs.sort(key=lambda x: x[2], reverse=True)

        for i, j, prob in coassoc_pairs[:5]:
            node_i = dist.nodes[i]
            node_j = dist.nodes[j]
            node_i_str = f"{node_i[0]}/{node_i[1]}" if isinstance(node_i, tuple) else str(node_i)
            node_j_str = f"{node_j[0]}/{node_j[1]}" if isinstance(node_j, tuple) else str(node_j)
            print(f"    {node_i_str:10s} <-> {node_j_str:10s}  P={prob:.3f}")

    else:
        coassoc_sparse = dist.coassociation(mode='sparse', topk=5)
        print("  Top-5 co-associations per node (sparse mode)")
        for node_idx in range(min(5, dist.n_nodes)):
            node = dist.nodes[node_idx]
            node_str = f"{node[0]}/{node[1]}" if isinstance(node, tuple) else str(node)
            neighbors = coassoc_sparse[node_idx][:3]  # Show top 3
            neighbor_strs = [
                f"{dist.nodes[nidx][0]}/{dist.nodes[nidx][1]}={prob:.2f}"
                if isinstance(dist.nodes[nidx], tuple) else f"{dist.nodes[nidx]}={prob:.2f}"
                for nidx, prob in neighbors
            ]
            print(f"    {node_str:15s}: {', '.join(neighbor_strs)}")

    print()


def main():
    """Main function."""
    args = parse_args()

    print("\n" + "=" * 70)
    print("DISTRIBUTIONAL COMMUNITY DETECTION EXAMPLE")
    print("=" * 70)
    print("\nThis example demonstrates uncertainty-aware community detection")
    print("that identifies stable vs boundary nodes in multilayer networks.")
    print()

    # Create example network
    print("Creating example multilayer network...")
    net = create_example_network()
    print_network_stats(net)

    # Run distributional community detection
    dist = run_distributional_community_detection(
        net,
        n_runs=args.n_runs,
        resampling=args.resampling,
        edge_drop_p=args.edge_drop_p,
        seed=args.seed,
        n_jobs=args.n_jobs,
    )

    # Analyze results
    analyze_consensus_partition(dist)
    stable_nodes, boundary_nodes = analyze_node_confidence(dist, args.confidence_threshold)
    analyze_coassociation(dist)

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total nodes: {dist.n_nodes}")
    print(f"  Stable core: {len(stable_nodes)} nodes (confidence >= {args.confidence_threshold})")
    print(f"  Boundary: {len(boundary_nodes)} nodes (confidence < {args.confidence_threshold})")
    print()
    print("  Interpretation:")
    print("    - Stable core nodes have consistent community assignments")
    print("    - Boundary nodes have uncertain assignments (between communities)")
    print("    - Co-association matrix shows pairwise community stability")
    print()
    print(" Example completed successfully!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()

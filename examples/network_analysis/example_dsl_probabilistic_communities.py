#!/usr/bin/env python
"""
Example: Probabilistic Community Detection with DSL v2
========================================================

This example demonstrates probabilistic community detection using the DSL v2
uncertainty quantification framework. It shows how to:

1. Generate community ensembles with different resampling strategies
2. Access probabilistic membership distributions
3. Analyze node-level and community-level uncertainty
4. Export results with expanded uncertainty columns

Key Features Demonstrated:
- Backward-compatible deterministic mode
- Probabilistic mode with .uq() chaining
- Multiple resampling strategies (SEED, PERTURBATION, BOOTSTRAP)
- Node uncertainty metrics (entropy, confidence, margin)
- Community stability metrics
- Partition variability metrics (VI/ARI/NMI)
"""

from py3plex.core import multinet
from py3plex.dsl import Q
import numpy as np


def create_sample_network():
    """Create a sample network with clear community structure."""
    net = multinet.multi_layer_network(directed=False, verbose=False)

    # Community 1: Tight cluster (Alice, Bob, Charlie)
    net.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
    ])
    net.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    ])

    # Community 2: Tight cluster (David, Eve, Frank)
    net.add_nodes([
        {'source': 'David', 'type': 'social'},
        {'source': 'Eve', 'type': 'social'},
        {'source': 'Frank', 'type': 'social'},
    ])
    net.add_edges([
        {'source': 'David', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'David', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Eve', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
    ])

    # Bridge node (Grace) - uncertain assignment
    net.add_nodes([
        {'source': 'Grace', 'type': 'social'},
    ])
    net.add_edges([
        # Connects to both communities (ambiguous)
        {'source': 'Charlie', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'David', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
    ])

    return net


def main():
    print("=" * 80)
    print("PROBABILISTIC COMMUNITY DETECTION WITH DSL V2")
    print("=" * 80)

    # Create network
    net = create_sample_network()
    print(f"\nNetwork: {len(list(net.get_nodes()))} nodes, {len(list(net.get_edges()))} edges")

    # =========================================================================
    # Example 1: Deterministic Community Detection (Backward Compatible)
    # =========================================================================
    print("\n" + "=" * 80)
    print("Example 1: Deterministic Community Detection (Backward Compatible)")
    print("=" * 80)

    result_det = Q.nodes().compute("communities").execute(net)
    communities_det = result_det.attributes['communities']

    print("\nDeterministic community assignments:")
    for node, comm_id in sorted(communities_det.items(), key=lambda x: str(x[0])):
        print(f"  {node[0]:12} -> Community {comm_id}")

    # =========================================================================
    # Example 2: Probabilistic Community Detection with SEED Method
    # =========================================================================
    print("\n" + "=" * 80)
    print("Example 2: Probabilistic Communities (SEED Method)")
    print("=" * 80)
    print("Using multiple random seeds to capture algorithmic stochasticity")

    result_prob = (
        Q.nodes()
        .uq(method="seed", n_samples=30, seed=42)
        .compute("communities")
        .execute(net)
    )
    communities_prob = result_prob.attributes['communities']

    print("\nProbabilistic community memberships:")
    print(f"{'Node':<12} {'Label':<8} {'Confidence':<12} {'Entropy':<10} {'Margin':<10}")
    print("-" * 65)

    for node in sorted(communities_prob.keys(), key=lambda x: str(x)):
        data = communities_prob[node]
        print(f"{node[0]:<12} {data['mean']:<8} {data['confidence']:<12.3f} "
              f"{data['entropy']:<10.3f} {data['margin']:<10.3f}")

    # Show detailed membership probabilities for uncertain nodes
    print("\nDetailed membership probabilities for uncertain nodes:")
    for node in sorted(communities_prob.keys(), key=lambda x: str(x)):
        data = communities_prob[node]
        if data['entropy'] > 0.1:  # Only show uncertain nodes
            print(f"\n  {node[0]}:")
            if 'probs' in data and data['probs']:
                for comm_id, prob in sorted(data['probs'].items()):
                    print(f"    Community {comm_id}: {prob:.3f}")
            else:
                print(f"    Community {data['mean']}: 1.000 (deterministic)")

    # =========================================================================
    # Example 3: Probabilistic Communities with PERTURBATION Method
    # =========================================================================
    print("\n" + "=" * 80)
    print("Example 3: Probabilistic Communities (PERTURBATION Method)")
    print("=" * 80)
    print("Perturbing network structure to assess structural uncertainty")

    result_pert = (
        Q.nodes()
        .uq(method="perturbation", n_samples=25, seed=42)
        .compute("communities")
        .execute(net)
    )
    communities_pert = result_pert.attributes['communities']

    print("\nUncertainty comparison (SEED vs PERTURBATION):")
    print(f"{'Node':<12} {'Entropy(SEED)':<15} {'Entropy(PERT)':<15} {'Delta':<10}")
    print("-" * 60)

    for node in sorted(communities_prob.keys(), key=lambda x: str(x)):
        ent_seed = communities_prob[node]['entropy']
        ent_pert = communities_pert[node]['entropy']
        delta = ent_pert - ent_seed
        print(f"{node[0]:<12} {ent_seed:<15.3f} {ent_pert:<15.3f} {delta:+.3f}")

    # =========================================================================
    # Example 4: Pandas Export with Uncertainty Expansion
    # =========================================================================
    print("\n" + "=" * 80)
    print("Example 4: Pandas Export with Uncertainty Expansion")
    print("=" * 80)

    # Note: This would require extending QueryResult.to_pandas() to handle
    # the special community uncertainty format. For now, we'll demonstrate
    # manual construction.

    import pandas as pd

    data = []
    for node, comm_data in communities_prob.items():
        row = {
            'node': node[0],
            'layer': node[1],
            'community_id': comm_data['mean'],
            'community_confidence': comm_data['confidence'],
            'membership_entropy': comm_data['entropy'],
            'membership_margin': comm_data['margin'],
        }

        # Add top-k membership probabilities
        if 'probs' in comm_data and comm_data['probs']:
            sorted_probs = sorted(comm_data['probs'].items(),
                                key=lambda x: x[1], reverse=True)
            for k, (comm_id, prob) in enumerate(sorted_probs[:3]):
                row[f'p_comm_{comm_id}'] = prob

        data.append(row)

    df = pd.DataFrame(data)
    print("\nDataFrame with expanded uncertainty columns:")
    print(df.to_string(index=False))

    # =========================================================================
    # Example 5: Filtering by Uncertainty Metrics
    # =========================================================================
    print("\n" + "=" * 80)
    print("Example 5: Filtering by Uncertainty Metrics")
    print("=" * 80)

    # Find high-uncertainty nodes (potential boundary nodes)
    high_entropy_nodes = [
        node for node, data in communities_prob.items()
        if data['entropy'] > 0.5
    ]

    print(f"\nHigh-uncertainty nodes (entropy > 0.5): {len(high_entropy_nodes)}")
    for node in high_entropy_nodes:
        data = communities_prob[node]
        print(f"  {node[0]}: entropy={data['entropy']:.3f}, "
              f"confidence={data['confidence']:.3f}")

    # Find confident core nodes
    core_nodes = [
        node for node, data in communities_prob.items()
        if data['confidence'] > 0.9
    ]

    print(f"\nConfident core nodes (confidence > 0.9): {len(core_nodes)}")
    for node in core_nodes:
        data = communities_prob[node]
        print(f"  {node[0]}: community={data['mean']}, "
              f"confidence={data['confidence']:.3f}")

    # =========================================================================
    # Example 6: Accessing Full Probabilistic Result Object
    # =========================================================================
    print("\n" + "=" * 80)
    print("Example 6: Advanced - Full Probabilistic Result Object")
    print("=" * 80)

    # The full ProbabilisticCommunityResult is stored in network metadata
    if hasattr(net, '_probabilistic_community_result'):
        prob_result = net._probabilistic_community_result

        # Handle both dict (with 'latest' key) and direct object storage
        if isinstance(prob_result, dict):
            prob_result = prob_result.get('latest')

        if prob_result is not None:
            print(f"\nProbabilistic community result:")
            print(f"  Number of nodes: {prob_result.n_nodes}")
            print(f"  Number of partitions: {prob_result.n_partitions}")
            print(f"  Is deterministic: {prob_result.is_deterministic}")

            if not prob_result.is_deterministic:
                # Access community stability metrics
                stability = prob_result.community_stability
                print(f"\nCommunity stability metrics:")
                for comm_id, metrics in sorted(stability.items()):
                    print(f"  Community {comm_id}:")
                    print(f"    Persistence: {metrics['persistence']:.3f}")
                    print(f"    Size (mean +/- std): {metrics['size_mean']:.1f} +/- {metrics['size_std']:.1f}")
                    print(f"    Coefficient of variation: {metrics['size_cv']:.3f}")

                # Access partition-space metrics
                part_metrics = prob_result.partition_metrics
                print(f"\nPartition variability metrics:")
                print(f"  Variation of Information (VI):")
                print(f"    Mean: {part_metrics['vi_mean']:.3f}")
                print(f"    Std: {part_metrics['vi_std']:.3f}")

                if 'ari_mean' in part_metrics:
                    print(f"  Adjusted Rand Index (ARI):")
                    print(f"    Mean: {part_metrics['ari_mean']:.3f}")
                    print(f"    Std: {part_metrics['ari_std']:.3f}")

                if 'nmi_mean' in part_metrics:
                    print(f"  Normalized Mutual Information (NMI):")
                    print(f"    Mean: {part_metrics['nmi_mean']:.3f}")
                    print(f"    Std: {part_metrics['nmi_std']:.3f}")
        else:
            print("\nNo probabilistic result stored (not available in this version)")
    else:
        print("\nNo probabilistic result stored (not available in this version)")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
Key Takeaways:
1. Backward compatible: Q.nodes().compute("communities") still works deterministically
2. UQ-enabled: Add .uq(...) to get probabilistic memberships
3. Multiple methods: SEED (algorithmic), PERTURBATION (structural), BOOTSTRAP
4. Rich uncertainty metrics: entropy, confidence, margin for each node
5. Community stability: persistence, size variability across partitions
6. Partition variability: VI/ARI/NMI distributions between partitions

Use Cases:
- Identify boundary nodes (high entropy, low confidence)
- Assess robustness of community assignments
- Compare structural vs algorithmic uncertainty
- Filter by confidence for downstream analysis

For more information, see: py3plex.uncertainty module documentation
    """)


if __name__ == "__main__":
    main()

"""Minimal example: Compositional UQ for aggregate statistics.

This example demonstrates uncertainty quantification for aggregate operations
in the DSL. Unlike traditional UQ which only affects compute(), compositional UQ
propagates uncertainty through aggregate/summarize, order_by, and coverage operations.

Example output:
    Average degree across all nodes: 2.5 +/- 0.3 (95% CI: [1.9, 3.1])
    
Key insight: The uncertainty reflects how the aggregate statistic varies
across different resamples of the network, not just node-level uncertainty.
"""

from py3plex.core import multinet
from py3plex.dsl import Q


def main():
    # Create a simple network
    net = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'David', 'type': 'social'},
    ]
    net.add_nodes(nodes)
    
    edges = [
        {'source': 'Alice', 'target': 'Bob',
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie',
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'David',
         'source_type': 'social', 'target_type': 'social'},
    ]
    net.add_edges(edges)
    
    print("=" * 60)
    print("Example 1: Aggregate with Compositional UQ")
    print("=" * 60)
    
    # Query: Compute average degree with uncertainty
    result = (
        Q.nodes()
         .compute("degree")
         .summarize(
             avg_degree="mean(degree)",
             median_degree="median(degree)",
             count="count()"
         )
         .uq(method="seed", n_samples=20, seed=42)
         .execute(net)
    )
    
    print(f"\nResults from {result.meta['uq']['n_samples']} resamples:")
    print(f"Method: {result.meta['uq']['method']}")
    print()
    
    # Extract and display results
    item = result.items[0]
    
    avg_deg = result.attributes["avg_degree"][item]
    if isinstance(avg_deg, dict) and "mean" in avg_deg:
        print(f"Average degree: {avg_deg['mean']:.2f} +/- {avg_deg['std']:.2f}")
        if avg_deg.get("quantiles"):
            q_low = min(avg_deg["quantiles"].values())
            q_high = max(avg_deg["quantiles"].values())
            print(f"  95% CI: [{q_low:.2f}, {q_high:.2f}]")
    
    median_deg = result.attributes["median_degree"][item]
    if isinstance(median_deg, dict) and "mean" in median_deg:
        print(f"Median degree: {median_deg['mean']:.2f} +/- {median_deg['std']:.2f}")
    
    count_val = result.attributes["count"][item]
    if isinstance(count_val, dict) and "mean" in count_val:
        print(f"Node count: {count_val['mean']:.0f} +/- {count_val['std']:.2f}")
    
    print("\n" + "=" * 60)
    print("Example 2: Ranking with Stability Metrics")
    print("=" * 60)
    
    # Query: Rank nodes by degree with uncertainty
    result_rank = (
        Q.nodes()
         .compute("degree")
         .order_by("-degree")
         .uq(method="seed", n_samples=20, seed=42)
         .execute(net)
    )
    
    print(f"\nRank stability metrics:")
    
    if "rank_stability" in result_rank.meta:
        rank_stab = result_rank.meta["rank_stability"]
        
        if rank_stab.get("kendall_tau_mean"):
            print(f"Kendall tau (rank correlation): {rank_stab['kendall_tau_mean']:.3f}")
        
        print("\nPer-node rank statistics:")
        for item in result_rank.items[:3]:  # Top 3
            node_id = item[0] if isinstance(item, tuple) else item
            rank_mean = rank_stab["rank_means"].get(item)
            rank_std = rank_stab["rank_stds"].get(item)
            if rank_mean is not None:
                print(f"  {node_id}: rank {rank_mean:.1f} +/- {rank_std:.2f}")
    
    print("\n" + "=" * 60)
    print("OK Compositional UQ example complete")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Example: DSL Uncertainty - Flagship Example
=============================================

This example demonstrates the flagship use case from the documentation:
finding hub nodes with uncertainty bounds using the DSL.
"""

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.uncertainty import uncertainty_enabled


def main():
    """Run the flagship uncertainty example."""
    print("=" * 70)
    print("DSL Uncertainty - Flagship Example")
    print("=" * 70)
    
    # Create a test network
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        # Layer 0: Triangle
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "a", "L0", 1.0],
        # Layer 1: Chain
        ["a", "L1", "b", "L1", 1.0],
        ["b", "L1", "c", "L1", 1.0],
        ["c", "L1", "d", "L1", 1.0],
        ["d", "L1", "e", "L1", 1.0],
        # Inter-layer connections
        ["a", "L0", "a", "L1", 1.0],
        ["b", "L0", "b", "L1", 1.0],
        ["c", "L0", "c", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    
    print(f"\nNetwork has {len(list(net.get_nodes()))} nodes")
    
    # Flagship example from the issue
    print("\n" + "-" * 70)
    print("Finding hubs with uncertainty bounds")
    print("-" * 70)
    
    with uncertainty_enabled(n_runs=10):
        hubs = (
            Q.nodes()
            .compute(
                "degree", "betweenness_centrality",
                uncertainty=True,
                method="perturbation",  # Use perturbation (edge/node drops)
                n_samples=10,  # Use fewer samples for quick testing
                ci=0.95
            )
            .order_by("-betweenness_centrality")
            .limit(5)
            .execute(net)
        )
    
    print(f"\nFound {len(hubs)} hub nodes:")
    
    # Convert to pandas for easier display
    df = hubs.to_pandas()
    print("\nResults as DataFrame:")
    print(df)
    
    # Extract and display uncertainty information
    print("\n" + "-" * 70)
    print("Hub nodes with uncertainty bounds:")
    print("-" * 70)
    
    # CI level from the query (0.95 -> quantiles at 0.025 and 0.975)
    ci = 0.95
    lower_q = (1 - ci) / 2  # 0.025 for 95% CI
    upper_q = 1 - lower_q   # 0.975 for 95% CI
    
    for idx, row in df.iterrows():
        node_id = row['id']
        bc_info = row.get('betweenness_centrality')
        deg_info = row.get('degree')
        
        print(f"\n{node_id}:")
        
        # Handle dict format (with uncertainty)
        if isinstance(bc_info, dict) and 'mean' in bc_info:
            bc_mean = bc_info['mean']
            bc_std = bc_info.get('std', 0)
            bc_quantiles = bc_info.get('quantiles', {})
            bc_low = bc_quantiles.get(lower_q, bc_mean)
            bc_high = bc_quantiles.get(upper_q, bc_mean)
            
            print(f"  Betweenness: {bc_mean:.4f} ± {bc_std:.4f}")
            print(f"  {int(ci*100)}% CI: [{bc_low:.4f}, {bc_high:.4f}]")
        else:
            # Handle scalar format (without uncertainty)
            print(f"  Betweenness: {bc_info}")
        
        if isinstance(deg_info, dict) and 'mean' in deg_info:
            deg_mean = deg_info['mean']
            deg_std = deg_info.get('std', 0)
            print(f"  Degree: {deg_mean:.2f} ± {deg_std:.2f}")
        else:
            print(f"  Degree: {deg_info}")
    
    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()

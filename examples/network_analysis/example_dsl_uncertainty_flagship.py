#!/usr/bin/env python
"""
Example: DSL Uncertainty - Flagship Example
=============================================

This example demonstrates the flagship use case from the documentation:
finding hub nodes with uncertainty bounds using the DSL with query-scoped
uncertainty configuration (.uq() method).
"""

from py3plex.core import multinet
from py3plex.dsl import Q, UQ


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
    
    # Flagship example: one-liner uncertainty analysis
    print("\n" + "-" * 70)
    print("Finding hubs with uncertainty bounds (one-liner)")
    print("-" * 70)
    
    # New ergonomic API: query-scoped uncertainty with .uq()
    df = (
        Q.nodes()
        .uq(method="perturbation", n_samples=100, ci=0.95, seed=42)
        .compute("betweenness_centrality")
        .order_by("-betweenness_centrality__mean")
        .limit(10)
        .execute(net)
        .to_pandas(expand_uncertainty=True)
    )
    
    print(f"\nFound {len(df)} hub nodes:")
    print("\nResults with expanded uncertainty columns:")
    print(df[["id", "betweenness_centrality", "betweenness_centrality_std", 
              "betweenness_centrality_ci95_low", "betweenness_centrality_ci95_high"]])
    
    # Display detailed uncertainty information
    print("\n" + "-" * 70)
    print("Hub nodes with uncertainty bounds:")
    print("-" * 70)
    
    for idx, row in df.head(5).iterrows():
        node_id = row['id']
        bc_mean = row['betweenness_centrality']
        bc_std = row['betweenness_centrality_std']
        bc_low = row['betweenness_centrality_ci95_low']
        bc_high = row['betweenness_centrality_ci95_high']
        
        print(f"\n{node_id}:")
        print(f"  Betweenness: {bc_mean:.4f} ± {bc_std:.4f}")
        print(f"  95% CI: [{bc_low:.4f}, {bc_high:.4f}]")
        print(f"  CI width: {bc_high - bc_low:.4f}")
    
    # Example 2: Using UQ profiles for quick setup
    print("\n" + "=" * 70)
    print("Using UQ Profiles")
    print("=" * 70)
    
    # Fast profile: 25 samples, good for exploration
    print("\n--- Fast profile (25 samples) ---")
    df_fast = (
        Q.nodes()
        .uq(UQ.fast(seed=42))
        .compute("degree")
        .order_by("-degree__mean")
        .limit(5)
        .execute(net)
        .to_pandas(expand_uncertainty=True)
    )
    print(df_fast[["id", "degree", "degree_std", "degree_ci95_width"]])
    
    # Example 3: Filtering by CI width (precision)
    print("\n" + "=" * 70)
    print("Conservative Ranking (by CI lower bound)")
    print("=" * 70)
    
    df_conservative = (
        Q.nodes()
        .uq(method="perturbation", n_samples=100, ci=0.95, seed=42)
        .compute("betweenness_centrality")
        .order_by("-betweenness_centrality__ci95__low")  # Most conservative
        .limit(5)
        .execute(net)
        .to_pandas(expand_uncertainty=True)
    )
    print(df_conservative[["id", "betweenness_centrality", 
                          "betweenness_centrality_ci95_low", 
                          "betweenness_centrality_ci95_high"]])
    
    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()

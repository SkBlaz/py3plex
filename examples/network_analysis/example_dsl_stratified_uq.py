"""Example demonstrating DSL builder API for stratified perturbation UQ.

This example shows the recommended way to use stratified UQ through the
DSL builder API rather than the low-level estimate_uncertainty function.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L
import numpy as np


def build_example_network():
    """Build a multilayer network for demonstration."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Social layer: star topology
    edges_social = [
        ["Alice", "social", "Bob", "social", 1.0],
        ["Alice", "social", "Charlie", "social", 1.0],
        ["Alice", "social", "David", "social", 1.0],
        ["Bob", "social", "Charlie", "social", 1.0],
    ]
    
    # Work layer: chain topology
    edges_work = [
        ["Alice", "work", "Bob", "work", 1.0],
        ["Bob", "work", "Charlie", "work", 1.0],
        ["Charlie", "work", "David", "work", 1.0],
    ]
    
    # Inter-layer connections
    edges_inter = [
        ["Alice", "social", "Alice", "work", 1.0],
        ["Bob", "social", "Bob", "work", 1.0],
        ["Charlie", "social", "Charlie", "work", 1.0],
        ["David", "social", "David", "work", 1.0],
    ]
    
    net.add_edges(edges_social + edges_work + edges_inter, input_type="list")
    return net


def main():
    print("=" * 70)
    print("DSL Builder API for Stratified Perturbation UQ")
    print("=" * 70)
    
    net = build_example_network()
    print(f"\nNetwork: {net.core_network.number_of_nodes()} nodes, "
          f"{net.core_network.number_of_edges()} edges, 2 layers\n")
    
    # Example 1: Auto-select stratification (recommended)
    print("-" * 70)
    print("Example 1: Auto-select stratification (recommended)")
    print("-" * 70)
    
    result1 = (
        Q.nodes()
        .from_layers(L["*"])  # All layers
        .compute("betweenness_centrality")
        .uq(
            method="stratified_perturbation",
            n_samples=50,
            ci=0.95,
            seed=42,
            edge_drop_p=0.1
        )
        .execute(net)
    )
    
    print(f"Computed betweenness with UQ for {len(result1)} nodes")
    print(f"Metadata: {list(result1.meta.keys())}")
    
    # Example 2: Explicit degree stratification
    print("\n" + "-" * 70)
    print("Example 2: Explicit degree stratification with 3 bins")
    print("-" * 70)
    
    result2 = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree", "clustering")
        .uq(
            method="stratified_perturbation",
            n_samples=50,
            ci=0.95,
            seed=42,
            strata=["degree"],
            bins={"degree": 3},
            edge_drop_p=0.1
        )
        .execute(net)
    )
    
    print(f"Computed degree & clustering with UQ for {len(result2)} nodes")
    
    # Example 3: Multi-layer query with composite stratification
    print("\n" + "-" * 70)
    print("Example 3: Composite stratification (degree + layer)")
    print("-" * 70)
    
    result3 = (
        Q.nodes()
        .from_layers(L["social"] + L["work"])
        .compute("pagerank")
        .uq(
            method="stratified_perturbation",
            n_samples=50,
            ci=0.95,
            seed=42,
            strata=["degree", "layer"],
            bins={"degree": 5},
            edge_drop_p=0.05
        )
        .execute(net)
    )
    
    print(f"Computed pagerank with UQ for {len(result3)} nodes")
    
    # Example 4: Per-layer grouping with UQ
    print("\n" + "-" * 70)
    print("Example 4: Per-layer grouping with stratified UQ")
    print("-" * 70)
    
    result4 = (
        Q.nodes()
        .from_layers(L["*"])
        .compute("degree")
        .uq(
            method="stratified_perturbation",
            n_samples=30,
            seed=42,
            edge_drop_p=0.1
        )
        .per_layer()
        .top_k(2, "degree")
        .end_grouping()
        .execute(net)
    )
    
    print(f"Top-2 nodes per layer with UQ:")
    df = result4.to_pandas()
    # Check available columns
    if len(df) > 0:
        print(f"Available columns: {df.columns.tolist()}")
        # Use actual column names from result
        cols_to_show = [c for c in df.columns if c in ['id', 'layer', 'degree', 'node']]
        if cols_to_show:
            print(df[cols_to_show].to_string(index=False))
        else:
            print(df.head().to_string())
    else:
        print("No results")
    
    # Example 5: Filtering with uncertainty-aware conditions
    print("\n" + "-" * 70)
    print("Example 5: Filter nodes by uncertain metric")
    print("-" * 70)
    
    result5 = (
        Q.nodes()
        .compute("betweenness_centrality")
        .uq(
            method="stratified_perturbation",
            n_samples=50,
            seed=42,
            edge_drop_p=0.1
        )
        .where(betweenness_centrality__gt=0.0)  # Filter by point estimate
        .execute(net)
    )
    
    print(f"Filtered to {len(result5)} nodes with betweenness > 0")
    
    # Example 6: Comparison with regular perturbation
    print("\n" + "-" * 70)
    print("Example 6: Regular vs Stratified Perturbation")
    print("-" * 70)
    
    # Regular perturbation
    result_regular = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .uq(
            method="perturbation",
            n_samples=50,
            seed=42,
            edge_drop_p=0.1
        )
        .execute(net)
    )
    
    # Stratified perturbation
    result_stratified = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .uq(
            method="stratified_perturbation",
            n_samples=50,
            seed=42,
            edge_drop_p=0.1
        )
        .execute(net)
    )
    
    print("Regular perturbation:")
    print(f"  Result nodes: {len(result_regular)}")
    
    print("Stratified perturbation:")
    print(f"  Result nodes: {len(result_stratified)}")
    print(f"  Stratification: {result_stratified.meta.get('stratification', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("DSL Builder API Examples Complete")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("- Use .uq() method on QueryBuilder to enable UQ")
    print("- Pass method='stratified_perturbation' for variance reduction")
    print("- Omit 'strata' parameter for auto-selection (recommended)")
    print("- Use 'strata' and 'bins' for fine-grained control")
    print("- Stratified UQ works seamlessly with grouping, filtering, etc.")


if __name__ == "__main__":
    main()

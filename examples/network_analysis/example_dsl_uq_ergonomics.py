"""Example: Uncertainty-First DSL Ergonomics.

This example demonstrates the new uncertainty-first features in DSL v2:
- Query-scoped uncertainty context with .uq()
- UQ profiles (fast/default/paper)
- Autocompute with uncertainty
- Selector syntax for ordering (metric__mean, metric__std, metric__ci95__low)
- Expanded uncertainty export in to_pandas()

The goal is to make uncertainty analysis reachable from one-liners.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, UQ


def build_example_network():
    """Build a small multilayer network for demonstration."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Social layer: Dense community
    edges = [
        ["Alice", "social", "Bob", "social", 1.0],
        ["Bob", "social", "Carol", "social", 1.0],
        ["Carol", "social", "Alice", "social", 1.0],
        ["Alice", "social", "David", "social", 1.0],
        ["Bob", "social", "David", "social", 1.0],
    ]
    
    # Work layer: More sparse
    edges.extend([
        ["Alice", "work", "Bob", "work", 1.0],
        ["Bob", "work", "Eve", "work", 1.0],
        ["Carol", "work", "Frank", "work", 1.0],
        ["David", "work", "Frank", "work", 1.0],
    ])
    
    # Inter-layer connections
    edges.extend([
        ["Alice", "social", "Alice", "work", 1.0],
        ["Bob", "social", "Bob", "work", 1.0],
        ["Carol", "social", "Carol", "work", 1.0],
        ["David", "social", "David", "work", 1.0],
    ])
    
    net.add_edges(edges, input_type="list")
    return net


def example_1_basic_uq():
    """Example 1: Basic query-scoped uncertainty."""
    print("=" * 60)
    print("Example 1: Basic Query-Scoped Uncertainty")
    print("=" * 60)
    
    net = build_example_network()
    
    # Use .uq() to set uncertainty defaults for the query
    result = (
        Q.nodes()
        .uq(method="perturbation", n_samples=50, ci=0.95, seed=42)
        .compute("degree")
        .execute(net)
    )
    
    df = result.to_pandas()
    print("\nResults with uncertainty (showing first 5 nodes):")
    print(df.head())
    
    # The degree column contains dicts with mean, std, quantiles
    print("\nFirst degree value (with uncertainty):")
    print(df["degree"].iloc[0])


def example_2_uq_profiles():
    """Example 2: Using UQ profiles for quick setup."""
    print("\n" + "=" * 60)
    print("Example 2: UQ Profiles (fast/default/paper)")
    print("=" * 60)
    
    net = build_example_network()
    
    # Fast profile: 25 samples, good for exploration
    print("\n--- Using UQ.fast() ---")
    result = (
        Q.nodes()
        .uq(UQ.fast(seed=0))
        .compute("degree")
        .limit(3)
        .execute(net)
    )
    
    df = result.to_pandas()
    print(f"Fast analysis complete, {len(df)} nodes")
    
    # Default profile: 50 samples, balanced
    print("\n--- Using UQ.default() ---")
    result = (
        Q.nodes()
        .uq(UQ.default(seed=0))
        .compute("degree")
        .limit(3)
        .execute(net)
    )
    
    df = result.to_pandas()
    print(f"Default analysis complete, {len(df)} nodes")
    
    # Paper profile: 300 samples with bootstrap, publication-quality
    print("\n--- Using UQ.paper() (would take longer) ---")
    # Reduced samples for demo
    result = (
        Q.nodes()
        .uq(method="bootstrap", n_samples=30, seed=0)  # Reduced for demo
        .compute("degree")
        .limit(3)
        .execute(net)
    )
    
    df = result.to_pandas()
    print(f"Publication-quality analysis complete, {len(df)} nodes")


def example_3_selector_syntax():
    """Example 3: Ordering with selector syntax."""
    print("\n" + "=" * 60)
    print("Example 3: Selector Syntax for Ordering")
    print("=" * 60)
    
    net = build_example_network()
    
    # Order by mean degree
    print("\n--- Order by mean degree (descending) ---")
    result = (
        Q.nodes()
        .uq(method="perturbation", n_samples=30, seed=42)
        .compute("degree")
        .order_by("-degree__mean")
        .limit(5)
        .execute(net)
    )
    
    df = result.to_pandas()
    for _, row in df.iterrows():
        deg = row["degree"]
        if isinstance(deg, dict):
            print(f"  {row['id']}: mean={deg['mean']:.2f}, std={deg.get('std', 0):.3f}")
    
    # Order by CI width (ascending = most precise first)
    print("\n--- Order by CI width (ascending = most precise first) ---")
    result = (
        Q.nodes()
        .uq(method="perturbation", n_samples=30, seed=42)
        .compute("degree")
        .order_by("degree__ci95__width")
        .limit(5)
        .execute(net)
    )
    
    df = result.to_pandas()
    for _, row in df.iterrows():
        deg = row["degree"]
        if isinstance(deg, dict):
            qs = deg.get('quantiles', {})
            low = qs.get(0.025, deg['mean'])
            high = qs.get(0.975, deg['mean'])
            width = high - low
            print(f"  {row['id']}: mean={deg['mean']:.2f}, CI width={width:.3f}")


def example_4_expand_uncertainty():
    """Example 4: Expanded uncertainty columns in DataFrame."""
    print("\n" + "=" * 60)
    print("Example 4: Expand Uncertainty in DataFrame")
    print("=" * 60)
    
    net = build_example_network()
    
    result = (
        Q.nodes()
        .uq(method="perturbation", n_samples=50, seed=42)
        .compute("degree")
        .order_by("-degree__mean")
        .limit(5)
        .execute(net)
    )
    
    # Without expand_uncertainty (default)
    print("\n--- Default export (single column) ---")
    df_compact = result.to_pandas(expand_uncertainty=False)
    print(df_compact.head())
    print(f"\nColumns: {list(df_compact.columns)}")
    
    # With expand_uncertainty=True
    print("\n--- Expanded export (multiple columns) ---")
    df_expanded = result.to_pandas(expand_uncertainty=True)
    print(df_expanded.head())
    print(f"\nColumns: {list(df_expanded.columns)}")
    
    # Show expanded values
    print("\n--- Expanded values detail ---")
    for _, row in df_expanded.head(3).iterrows():
        print(f"\n{row['id']}:")
        print(f"  degree (mean):  {row['degree']:.2f}")
        print(f"  degree_std:     {row['degree_std']:.3f}")
        print(f"  degree_ci95_low:  {row['degree_ci95_low']:.2f}")
        print(f"  degree_ci95_high: {row['degree_ci95_high']:.2f}")
        print(f"  degree_ci95_width: {row['degree_ci95_width']:.3f}")


def example_5_autocompute():
    """Example 5: Autocompute with uncertainty."""
    print("\n" + "=" * 60)
    print("Example 5: Autocompute with Uncertainty")
    print("=" * 60)
    
    net = build_example_network()
    
    # Order by degree without explicitly computing it
    # Since .uq() is set, autocompute will use uncertainty
    print("\n--- Autocompute degree with uncertainty ---")
    result = (
        Q.nodes()
        .uq(method="perturbation", n_samples=30, seed=42)
        .order_by("-degree")  # Autocomputes degree with uncertainty
        .limit(5)
        .execute(net)
    )
    
    df = result.to_pandas(expand_uncertainty=True)
    print(df[["id", "degree", "degree_std", "degree_ci95_width"]].head())
    
    print("\nNote: degree was auto-computed with uncertainty because .uq() was set")


def example_6_one_liner():
    """Example 6: The "one-liner" use case."""
    print("\n" + "=" * 60)
    print("Example 6: One-Liner Uncertainty Analysis")
    print("=" * 60)
    
    net = build_example_network()
    
    # Complete uncertainty analysis in one expression
    df = (
        Q.nodes()
        .uq(UQ.fast(seed=42))
        .compute("degree")
        .order_by("-degree__mean")
        .limit(5)
        .execute(net)
        .to_pandas(expand_uncertainty=True)
    )
    
    print("\nTop 5 nodes by mean degree with uncertainty:")
    print(df[["id", "layer", "degree", "degree_std", "degree_ci95_width"]])
    
    print("\n✓ Complete uncertainty analysis in a single fluent expression!")


def example_7_filtering_by_uncertainty():
    """Example 7: Filtering by uncertainty properties (via order_by + limit)."""
    print("\n" + "=" * 60)
    print("Example 7: Filtering by Uncertainty")
    print("=" * 60)
    
    net = build_example_network()
    
    # Find nodes with low uncertainty (narrow CI)
    print("\n--- Nodes with most precise estimates (narrow CI) ---")
    result = (
        Q.nodes()
        .uq(method="perturbation", n_samples=50, seed=42)
        .compute("degree")
        .order_by("degree__ci95__width")  # Ascending - smallest width first
        .limit(3)
        .execute(net)
    )
    
    df = result.to_pandas(expand_uncertainty=True)
    print(df[["id", "degree", "degree_ci95_width"]])
    
    # Conservative ranking: order by lower CI bound
    print("\n--- Conservative ranking (by CI lower bound) ---")
    result = (
        Q.nodes()
        .uq(method="perturbation", n_samples=50, seed=42)
        .compute("degree")
        .order_by("-degree__ci95__low")  # Descending - highest lower bound
        .limit(3)
        .execute(net)
    )
    
    df = result.to_pandas(expand_uncertainty=True)
    print(df[["id", "degree", "degree_ci95_low", "degree_ci95_high"]])


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DSL Uncertainty-First Ergonomics Examples")
    print("=" * 60)
    
    example_1_basic_uq()
    example_2_uq_profiles()
    example_3_selector_syntax()
    example_4_expand_uncertainty()
    example_5_autocompute()
    example_6_one_liner()
    example_7_filtering_by_uncertainty()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)

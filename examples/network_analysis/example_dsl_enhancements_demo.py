"""Example demonstrating new DSL enhancements: temporal helpers, autocompute control, and pipeline interop.

This example showcases:
1. Temporal query helpers (before/after)
2. Autocompute flag control
3. DSL result integration with pipeline operations
4. Computed metrics tracking

For complete documentation, see:
- DSL How-to: docfiles/how-to/query_with_dsl.rst
- Pipeline How-to: docfiles/how-to/build_pipelines.rst
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L, DslMissingMetricError


def create_temporal_network():
    """Create a sample temporal multilayer network."""
    network = multinet.multi_layer_network(directed=False)

    # Add nodes
    nodes = []
    for layer in ["social", "work"]:
        for i in range(10):
            nodes.append({'source': f'person{i}', 'type': layer})
    network.add_nodes(nodes)

    # Add temporal edges with time attribute
    # Early period (t < 100): sparse network
    # Mid period (100 <= t <= 200): growing network
    # Late period (t > 200): dense network
    edges = []

    # Social layer edges
    for i in range(4):
        edges.append({
            'source': f'person{i}',
            'target': f'person{i+1}',
            'source_type': 'social',
            'target_type': 'social',
            'weight': 1.0,
            't': 50.0 + i * 10  # Times 50, 60, 70, 80
        })

    for i in range(7):
        edges.append({
            'source': f'person{i}',
            'target': f'person{i+1}',
            'source_type': 'social',
            'target_type': 'social',
            'weight': 1.0,
            't': 100.0 + i * 10  # Times 100-160
        })

    for i in range(9):
        edges.append({
            'source': f'person{i}',
            'target': f'person{i+1}',
            'source_type': 'social',
            'target_type': 'social',
            'weight': 1.0,
            't': 200.0 + i * 5  # Times 200-240
        })

    # Work layer edges
    for i in range(5):
        edges.append({
            'source': f'person{i}',
            'target': f'person{i+2}',
            'source_type': 'work',
            'target_type': 'work',
            'weight': 1.0,
            't': 100.0 + i * 20  # Times 100-180
        })

    network.add_edges(edges)
    return network


def demo_temporal_helpers():
    """Demonstrate before() and after() temporal helpers."""
    print("=" * 70)
    print("DEMO 1: Temporal Query Helpers (before/after)")
    print("=" * 70)

    network = create_temporal_network()

    # Compare network before and after a key event (t=100)
    event_time = 100.0

    print(f"\nAnalyzing network evolution around event at t={event_time}...\n")

    # Query edges before the event
    edges_before = Q.edges().before(event_time).execute(network)
    print(f"Edges before event (t <= {event_time}): {len(edges_before)}")

    # Query edges after the event
    edges_after = Q.edges().after(event_time).execute(network)
    print(f"Edges after event (t >= {event_time}): {len(edges_after)}")

    # Compute node metrics before and after
    nodes_before = (
        Q.nodes()
         .before(event_time)
         .compute("degree")
         .execute(network)
    )

    nodes_after = (
        Q.nodes()
         .after(event_time)
         .compute("degree")
         .execute(network)
    )

    df_before = nodes_before.to_pandas()
    df_after = nodes_after.to_pandas()

    print(f"\nNetwork metrics:")
    print(f"  Average degree before event: {df_before['degree'].mean():.2f}")
    print(f"  Average degree after event:  {df_after['degree'].mean():.2f}")

    growth_rate = (df_after['degree'].mean() - df_before['degree'].mean()) / df_before['degree'].mean() * 100
    print(f"  Network growth: {growth_rate:+.1f}%")

    # Show top connected nodes before and after
    print(f"\nTop 3 connected nodes before event:")
    top_before = df_before.nlargest(3, 'degree')[['id', 'layer', 'degree']]
    for _, row in top_before.iterrows():
        print(f"  {row['id']:12} ({row['layer']:6}): degree = {row['degree']}")

    print(f"\nTop 3 connected nodes after event:")
    top_after = df_after.nlargest(3, 'degree')[['id', 'layer', 'degree']]
    for _, row in top_after.iterrows():
        print(f"  {row['id']:12} ({row['layer']:6}): degree = {row['degree']}")


def demo_autocompute_control():
    """Demonstrate autocompute flag and computed_metrics tracking."""
    print("\n" + "=" * 70)
    print("DEMO 2: Autocompute Control and Metric Tracking")
    print("=" * 70)

    network = create_temporal_network()

    # Example 1: Default behavior (autocompute enabled)
    print("\n1. Default behavior (autocompute=True):")
    result_auto = (
        Q.nodes()
         .from_layers(L["social"])
         .order_by("degree")  # degree auto-computed
         .limit(5)
         .execute(network)
    )

    print(f"   Computed metrics: {result_auto.computed_metrics}")
    print(f"   Result has 'degree' column: {'degree' in result_auto.to_pandas().columns}")

    # Example 2: Explicit autocompute disabled
    print("\n2. Explicit control (autocompute=False):")
    result_explicit = (
        Q.nodes(autocompute=False)
         .from_layers(L["social"])
         .compute("degree")  # Must explicitly compute
         .order_by("degree")
         .limit(5)
         .execute(network)
    )

    print(f"   Computed metrics: {result_explicit.computed_metrics}")
    print(f"   Result has 'degree' column: {'degree' in result_explicit.to_pandas().columns}")

    # Example 3: What happens without explicit compute when autocompute is disabled
    print("\n3. Missing metric with autocompute=False:")
    try:
        Q.nodes(autocompute=False).order_by("betweenness_centrality").execute(network)
    except Exception as e:
        print(f"    Error: {type(e).__name__}")
        print(f"   Message: {str(e)[:100]}...")

    # Example 4: Track multiple computed metrics
    print("\n4. Tracking multiple auto-computed metrics:")
    result_multi = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=1)  # degree auto-computed
         .compute("clustering")  # clustering explicitly computed
         .order_by("betweenness_centrality")  # betweenness auto-computed
         .limit(5)
         .execute(network)
    )

    print(f"   Computed metrics: {result_multi.computed_metrics}")
    print(f"   Total metrics computed: {len(result_multi.computed_metrics)}")


def demo_pipeline_interop():
    """Demonstrate DSL result integration with pipeline operations."""
    print("\n" + "=" * 70)
    print("DEMO 3: DSL <-> Pipeline Interoperability")
    print("=" * 70)

    network = create_temporal_network()

    print("\nCombined workflow: DSL query -> pandas transformations -> analysis\n")

    # Step 1: DSL query to get nodes with centrality metrics
    result = (
        Q.nodes()
         .from_layers(L["*"])  # All layers
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )

    # Step 2: Export to pandas for flexible transformations
    df = result.to_pandas()

    # Step 3: Pandas operations (similar to pipeline verbs)
    # Filter: Keep only connected nodes
    df = df[df["degree"] > 1]

    # Mutate: Add composite influence score
    df['influence'] = (
        0.6 * df['degree'] +
        0.4 * df['betweenness_centrality'] * 100
    )

    # Mutate: Categorize nodes
    df['node_type'] = df['degree'].apply(
        lambda d: "hub" if d > 3 else "connector" if d > 1 else "peripheral"
    )

    # Arrange: Sort by influence
    df = df.sort_values('influence', ascending=False)

    print(f"Pipeline result: {len(df)} nodes")
    print(f"Columns: {list(df.columns)}")

    print("\nTop 5 influential nodes:")
    print(df[['id', 'layer', 'degree', 'betweenness_centrality', 'influence', 'node_type']].head())

    print("\nNode type distribution:")
    type_counts = df['node_type'].value_counts()
    for node_type, count in type_counts.items():
        print(f"  {node_type:12}: {count:3} nodes")

    # Advanced: Group by layer and summarize
    print("\n\nAdvanced: Per-layer statistics:")

    layer_stats = df.groupby('layer').agg({
        'degree': ['mean', 'max'],
        'betweenness_centrality': ['mean', 'max'],
        'influence': ['mean', 'max']
    }).round(3)

    print(layer_stats)


def demo_comprehensive_workflow():
    """Demonstrate a complete analytical workflow using all new features."""
    print("\n" + "=" * 70)
    print("DEMO 4: Comprehensive Workflow (All Features Together)")
    print("=" * 70)

    network = create_temporal_network()

    print("\nScenario: Identify emerging influencers in the late period")
    print("          (nodes with increasing influence after t=150)\n")

    # Step 1: Get early network state (before t=150)
    early_nodes = (
        Q.nodes(autocompute=True)  # Explicit flag for clarity
         .before(150.0)
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )

    early_df = early_nodes.to_pandas()
    print(f"Early period metrics computed: {early_nodes.computed_metrics}")

    # Step 2: Get late network state (after t=150)
    late_nodes = (
        Q.nodes()
         .after(150.0)
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )

    late_df = late_nodes.to_pandas()

    # Step 3: Combine and analyze using pipeline operations
    # Create influence scores for both periods
    early_df['influence_early'] = (
        0.5 * early_df['degree'] +
        0.5 * early_df['betweenness_centrality'] * 100
    )

    late_df['influence_late'] = (
        0.5 * late_df['degree'] +
        0.5 * late_df['betweenness_centrality'] * 100
    )

    # Merge on node id
    comparison = early_df[['id', 'layer', 'influence_early']].merge(
        late_df[['id', 'layer', 'influence_late']],
        on=['id', 'layer'],
        how='outer'
    ).fillna(0)

    # Calculate influence change
    comparison['influence_change'] = (
        comparison['influence_late'] - comparison['influence_early']
    )
    comparison['influence_change_pct'] = (
        (comparison['influence_change'] / (comparison['influence_early'] + 0.01)) * 100
    )

    # Find emerging influencers (biggest gainers)
    emerging = comparison.nlargest(5, 'influence_change')

    print("Top 5 emerging influencers (biggest influence gain):\n")
    for idx, row in emerging.iterrows():
        print(f"  {row['id']:12} ({row['layer']:6}): "
              f"{row['influence_early']:5.1f} -> {row['influence_late']:5.1f} "
              f"(+{row['influence_change']:5.1f}, +{row['influence_change_pct']:5.1f}%)")

    print(f"\nWorkflow used:")
    print(f"   Temporal helpers: before(150), after(150)")
    print(f"   Autocompute flag: explicitly set for clarity")
    print(f"   Computed metrics tracking: verified what was computed")
    print(f"   Pipeline operations: pandas merging and calculations")


if __name__ == "__main__":
    demo_temporal_helpers()
    demo_autocompute_control()
    demo_pipeline_interop()
    demo_comprehensive_workflow()

    print("\n" + "=" * 70)
    print("All demos completed successfully!")
    print("=" * 70)
    print("\nFor more information:")
    print("  - Temporal queries: docfiles/how-to/query_with_dsl.rst (Temporal Queries section)")
    print("  - Autocompute: docfiles/how-to/query_with_dsl.rst (Smart Defaults section)")
    print("  - Pipeline interop: docfiles/how-to/query_with_dsl.rst (DSL Result Interoperability)")
    print("  - API reference: py3plex.dsl module documentation")

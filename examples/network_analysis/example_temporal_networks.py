"""Example: Temporal Network Analysis with py3plex

This example demonstrates how to use the temporal features of py3plex to analyze
time-varying multilayer networks. The temporal support allows you to:

1. Add temporal attributes to edges (point-in-time or intervals)
2. Query networks at specific time points (snapshots)
3. Query networks over time ranges
4. Use the DSL builder API for temporal queries

The temporal features are minimal and non-breaking:
- Existing networks without time data work unchanged
- Temporal filtering is opt-in via TemporalMultinetView or DSL
- Time attributes follow simple conventions (t, t_start, t_end)
"""

from py3plex.core import multinet
from py3plex.temporal_view import TemporalMultinetView
from py3plex.dsl import Q


def create_temporal_network():
    """Create a sample temporal multilayer network.

    This network represents communication patterns that change over time.
    """
    network = multinet.multi_layer_network(directed=False)

    # Add nodes
    nodes = [
        {'source': 'Alice', 'type': 'email'},
        {'source': 'Bob', 'type': 'email'},
        {'source': 'Charlie', 'type': 'email'},
        {'source': 'David', 'type': 'email'},
        {'source': 'Alice', 'type': 'chat'},
        {'source': 'Bob', 'type': 'chat'},
        {'source': 'Charlie', 'type': 'chat'},
    ]
    network.add_nodes(nodes)

    # Add temporal edges
    # Point-in-time edges (discrete events)
    edges = [
        # Email communications (specific timestamps)
        {'source': 'Alice', 'target': 'Bob',
         'source_type': 'email', 'target_type': 'email',
         't': 100.0, 'weight': 1.0},

        {'source': 'Bob', 'target': 'Charlie',
         'source_type': 'email', 'target_type': 'email',
         't': 150.0, 'weight': 1.0},

        {'source': 'Charlie', 'target': 'David',
         'source_type': 'email', 'target_type': 'email',
         't': 250.0, 'weight': 1.0},

        # Chat connections (persistent intervals)
        {'source': 'Alice', 'target': 'Bob',
         'source_type': 'chat', 'target_type': 'chat',
         't_start': 120.0, 't_end': 200.0, 'weight': 1.0},

        {'source': 'Bob', 'target': 'Charlie',
         'source_type': 'chat', 'target_type': 'chat',
         't_start': 150.0, 't_end': 250.0, 'weight': 1.0},

        # Atemporal edge (always present)
        {'source': 'Alice', 'target': 'Charlie',
         'source_type': 'email', 'target_type': 'email',
         'weight': 1.0},
    ]
    network.add_edges(edges)

    return network


def example_temporal_view():
    """Example: Using TemporalMultinetView for temporal filtering."""
    print("=" * 70)
    print("Example 1: TemporalMultinetView - Low-level temporal filtering")
    print("=" * 70)

    network = create_temporal_network()

    # Create temporal view
    view = TemporalMultinetView(network)

    # 1. Snapshot at t=150
    print("\n1. Snapshot at t=150:")
    snapshot = view.snapshot_at(150.0)
    edges = list(snapshot.iter_edges())
    print(f"   Edges active at t=150: {len(edges)}")
    for edge in edges:
        print(f"     {edge[0]} -- {edge[1]}")

    # 2. Time range [100, 200]
    print("\n2. Time range [100, 200]:")
    range_view = view.with_slice(100.0, 200.0)
    edges = list(range_view.iter_edges())
    print(f"   Edges active in [100, 200]: {len(edges)}")
    for edge in edges:
        print(f"     {edge[0]} -- {edge[1]}")

    # 3. Open-ended range (from 200 onwards)
    print("\n3. Open-ended range (from 200 onwards):")
    after_view = view.with_slice(200.0, None)
    edges = list(after_view.iter_edges())
    print(f"   Edges active after t=200: {len(edges)}")
    for edge in edges:
        print(f"     {edge[0]} -- {edge[1]}")


def example_dsl_temporal():
    """Example: Using DSL builder API for temporal queries."""
    print("\n" + "=" * 70)
    print("Example 2: DSL Builder API - High-level temporal queries")
    print("=" * 70)

    network = create_temporal_network()

    # 1. Query edges at specific time
    print("\n1. Query edges AT t=150 using DSL:")
    q = Q.edges().at(150.0)
    result = q.execute(network)
    print(f"   Result type: {type(result)}")
    if hasattr(result, 'to_pandas'):
        df = result.to_pandas()
        print(f"   Number of results: {len(df)}")
    else:
        print(f"   Result: {result}")

    # 2. Query edges during time range
    print("\n2. Query edges DURING [100, 200] using DSL:")
    q = Q.edges().during(100.0, 200.0)
    result = q.execute(network)
    if hasattr(result, 'to_pandas'):
        df = result.to_pandas()
        print(f"   Number of results: {len(df)}")

    # 3. Chain temporal with other clauses
    print("\n3. Chain temporal with LIMIT:")
    q = Q.edges().during(100.0, 250.0).limit(3)
    result = q.execute(network)
    if hasattr(result, 'to_pandas'):
        df = result.to_pandas()
        print(f"   Number of results (with limit): {len(df)}")

    # 4. Temporal query without time data (backwards compatibility)
    print("\n4. Temporal query on atemporal network:")
    atemporal_net = multinet.multi_layer_network(directed=False)
    atemporal_net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
    ])
    atemporal_net.add_edges([
        {'source': 'A', 'target': 'B',
         'source_type': 'layer1', 'target_type': 'layer1',
         'weight': 1.0},
    ])

    q = Q.edges().during(100.0, 200.0)
    result = q.execute(atemporal_net)
    if hasattr(result, 'to_pandas'):
        df = result.to_pandas()
        print(f"   Atemporal edges always included: {len(df)}")


def example_analysis_over_time():
    """Example: Analyzing network evolution over time."""
    print("\n" + "=" * 70)
    print("Example 3: Analyzing Network Evolution Over Time")
    print("=" * 70)

    network = create_temporal_network()
    view = TemporalMultinetView(network)

    # Analyze network at different time points
    time_points = [100.0, 150.0, 200.0, 250.0]

    print("\n   Time | # Edges | Description")
    print("   " + "-" * 50)

    for t in time_points:
        snapshot = view.snapshot_at(t)
        edges = list(snapshot.iter_edges())

        # Determine what's happening
        if t == 100.0:
            desc = "Initial email communication"
        elif t == 150.0:
            desc = "Email + chat connections active"
        elif t == 200.0:
            desc = "Chat ending, new email"
        else:
            desc = "Later email communication"

        print(f"   {t:5.0f} | {len(edges):7d} | {desc}")


def example_temporal_conventions():
    """Example: Different temporal attribute conventions."""
    print("\n" + "=" * 70)
    print("Example 4: Temporal Attribute Conventions")
    print("=" * 70)

    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)

    edges = [
        # Point-in-time: discrete event at t=100
        {'source': 'A', 'target': 'B',
         'source_type': 'layer1', 'target_type': 'layer1',
         't': 100.0, 'weight': 1.0},

        # Interval: active from t=150 to t=250
        {'source': 'B', 'target': 'C',
         'source_type': 'layer1', 'target_type': 'layer1',
         't_start': 150.0, 't_end': 250.0, 'weight': 1.0},

        # Atemporal: always present (no time attributes)
        {'source': 'A', 'target': 'C',
         'source_type': 'layer1', 'target_type': 'layer1',
         'weight': 1.0},
    ]
    network.add_edges(edges)

    view = TemporalMultinetView(network)

    print("\n   Query Type          | # Edges | Included Edges")
    print("   " + "-" * 60)

    # Snapshot at t=100 (only point-in-time at 100)
    snapshot = view.snapshot_at(100.0)
    edges = list(snapshot.iter_edges())
    print(f"   Snapshot at t=100   | {len(edges):7d} | Point-in-time + atemporal")

    # Range [100, 200] (point + interval + atemporal)
    range_view = view.with_slice(100.0, 200.0)
    edges = list(range_view.iter_edges())
    print(f"   Range [100, 200]    | {len(edges):7d} | All edges")

    # Before any temporal data
    early_view = view.with_slice(0.0, 50.0)
    edges = list(early_view.iter_edges())
    print(f"   Range [0, 50]       | {len(edges):7d} | Only atemporal")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("TEMPORAL NETWORK ANALYSIS EXAMPLES")
    print("=" * 70)

    # Run examples
    example_temporal_view()
    example_dsl_temporal()
    example_analysis_over_time()
    example_temporal_conventions()

    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • Temporal attributes (t, t_start, t_end) are optional")
    print("  • Atemporal edges are always included (backwards compatible)")
    print("  • Use TemporalMultinetView for low-level filtering")
    print("  • Use DSL builder API (Q.at(), Q.during()) for high-level queries")
    print("  • Point-in-time edges are discrete events")
    print("  • Interval edges are active during [t_start, t_end]")
    print()


if __name__ == "__main__":
    main()

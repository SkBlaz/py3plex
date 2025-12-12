"""Example demonstrating windowed query execution.

This script shows how to use the DSL to execute windowed queries
on temporal networks, with duration string parsing and result aggregation.
"""

from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.dsl import Q, L
from py3plex.temporal_utils_extended import parse_duration_string, format_duration


def create_temporal_network():
    """Create a sample temporal network."""
    print("Creating temporal network...")
    
    tnet = TemporalMultiLayerNetwork(directed=False)
    
    # Add edges over a 2-week period
    # Simulate network activity over time
    edges = []
    
    # Week 1: Initial connections
    for day in range(7):
        t = day * 86400.0  # Convert days to seconds
        edges.extend([
            ('Alice', 'social', 'Bob', 'social', t, 1.0),
            ('Bob', 'social', 'Charlie', 'social', t, 1.0),
        ])
    
    # Week 2: Network grows
    for day in range(7, 14):
        t = day * 86400.0
        edges.extend([
            ('Alice', 'social', 'David', 'social', t, 1.0),
            ('David', 'social', 'Eve', 'social', t, 1.0),
            ('Eve', 'social', 'Bob', 'social', t, 1.0),
        ])
    
    tnet.add_edges(edges, input_type="tuple")
    
    t_min, t_max = tnet.time_range()
    print(f"Network created with {tnet.number_of_edges()} edges")
    print(f"Time range: {format_duration(t_min)} to {format_duration(t_max)}")
    
    return tnet


def demonstrate_duration_parsing():
    """Demonstrate duration string parsing."""
    print("\n=== Duration String Parsing ===")
    
    durations = ["7d", "24h", "30m", "1w", "1.5h"]
    
    for duration_str in durations:
        seconds = parse_duration_string(duration_str)
        formatted = format_duration(seconds, precision=2)
        print(f"  {duration_str:8s} = {seconds:10.1f} seconds = {formatted}")


def demonstrate_windowed_queries():
    """Demonstrate windowed query execution."""
    print("\n=== Windowed Query Execution ===")
    
    tnet = create_temporal_network()
    
    # Query 1: Non-overlapping windows with numeric size
    print("\n1. Non-overlapping 3-day windows:")
    q1 = Q.nodes().compute("degree").window(3 * 86400.0)  # 3 days in seconds
    result1 = q1.execute(tnet)
    
    print(f"   Window count: {result1.meta['window_count']}")
    print(f"   Aggregation: {result1.meta['aggregation']}")
    
    # Show results from each window
    if isinstance(result1.items, list):
        for i, window_result in enumerate(result1.items[:3]):  # Show first 3
            t_start = window_result.meta['window_start']
            t_end = window_result.meta['window_end']
            print(f"   Window {i+1}: [{format_duration(t_start)} - {format_duration(t_end)}]")
            df = window_result.to_pandas()
            print(f"     Nodes: {len(df)}, Avg degree: {df['degree'].mean():.2f}")
    
    # Query 2: Duration strings
    print("\n2. Overlapping windows with duration strings:")
    q2 = Q.nodes().compute("degree").window("2d", step="1d")
    result2 = q2.execute(tnet)
    
    print(f"   Window count: {result2.meta['window_count']}")
    
    # Query 3: Concatenated results
    print("\n3. Concatenated window results:")
    try:
        import pandas as pd
        
        q3 = Q.nodes().compute("degree").window("3d", aggregation="concat")
        result3 = q3.execute(tnet)
        
        print(f"   Aggregation: {result3.meta['aggregation']}")
        
        # Convert to pandas and show
        df3 = result3.to_pandas()
        print(f"   Total rows: {len(df3)}")
        print(f"   Columns: {list(df3.columns)}")
        
        # Show sample
        print("\n   Sample rows:")
        print(df3.head(5).to_string(index=False))
        
    except ImportError:
        print("   (pandas not available, skipping concat example)")


def demonstrate_complex_windowed_queries():
    """Demonstrate complex windowed queries with filtering."""
    print("\n=== Complex Windowed Queries ===")
    
    tnet = create_temporal_network()
    
    # Query: Windowed query with layer filter and ordering
    print("\n1. Top nodes by degree per window:")
    q = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .window("3d")
        .order_by("degree", desc=True)
        .limit(3)
    )
    
    result = q.execute(tnet)
    
    if isinstance(result.items, list):
        for i, window_result in enumerate(result.items[:2]):  # Show first 2 windows
            t_start = window_result.meta['window_start']
            t_end = window_result.meta['window_end']
            print(f"\n   Window {i+1}: [{format_duration(t_start)} - {format_duration(t_end)}]")
            
            df = window_result.to_pandas()
            if not df.empty:
                for _, row in df.iterrows():
                    print(f"     {row['id']}: degree={row['degree']}")
    
    # Query: Windowed query with temporal filter
    print("\n2. Windowed query with time filter:")
    q2 = (
        Q.nodes()
        .during(0, 7 * 86400.0)  # First week only
        .compute("degree")
        .window("2d")
    )
    
    result2 = q2.execute(tnet)
    print(f"   Windows in first week: {result2.meta['window_count']}")


def demonstrate_practical_use_case():
    """Demonstrate a practical use case."""
    print("\n=== Practical Use Case: Network Evolution ===")
    print("\nTracking degree centrality evolution over time...")
    
    tnet = create_temporal_network()
    
    # Query: Track degree evolution with overlapping windows
    q = (
        Q.nodes()
        .compute("degree")
        .window("2d", step="1d", aggregation="concat")
    )
    
    try:
        import pandas as pd
        
        result = q.execute(tnet)
        df = result.to_pandas()
        
        # Calculate average degree per window
        window_stats = df.groupby(['window_start', 'window_end']).agg({
            'degree': ['mean', 'max', 'count']
        }).reset_index()
        
        print("\n   Window Statistics:")
        print(f"   {'Window':>8s} {'Avg Deg':>10s} {'Max Deg':>10s} {'Nodes':>8s}")
        print("   " + "-" * 45)
        
        for i in range(min(5, len(window_stats))):
            row = window_stats.iloc[i]
            print(f"   {i+1:>8d} {row[('degree', 'mean')]:>10.2f} "
                  f"{row[('degree', 'max')]:>10.0f} {row[('degree', 'count')]:>8.0f}")
        
        print(f"\n   Network activity over time shows evolution from "
              f"{window_stats[('degree', 'mean')].iloc[0]:.1f} to "
              f"{window_stats[('degree', 'mean')].iloc[-1]:.1f} average degree.")
        
    except ImportError:
        print("   (pandas not available)")


def main():
    """Run all demonstrations."""
    print("=" * 70)
    print("Windowed Query Execution Example")
    print("=" * 70)
    
    demonstrate_duration_parsing()
    demonstrate_windowed_queries()
    demonstrate_complex_windowed_queries()
    demonstrate_practical_use_case()
    
    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()

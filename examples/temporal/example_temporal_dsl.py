"""Temporal DSL query construction.

Demonstrates how to express temporal filters, window specifications, and
combined temporal/layer queries using the DSL. These snippets build queries
only; executor support for all windowed operations is still evolving.

Dependencies: py3plex (installed editable or via sys.path tweak below).
"""

from __future__ import annotations

from pathlib import Path
import sys

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.dsl import L, Q


def create_sample_network() -> TemporalMultiLayerNetwork:
    """Create a sample temporal multilayer network."""
    tnet = TemporalMultiLayerNetwork(directed=False)

    # Add edges across multiple layers and time periods
    edges = [
        # Social layer - early period
        ('Alice', 'social', 'Bob', 'social', 100.0, 1.0),
        ('Bob', 'social', 'Charlie', 'social', 100.0, 1.0),

        # Work layer - early period
        ('Alice', 'work', 'David', 'work', 120.0, 1.0),
        ('David', 'work', 'Eve', 'work', 120.0, 1.0),

        # Social layer - middle period
        ('Charlie', 'social', 'David', 'social', 200.0, 1.0),
        ('Alice', 'social', 'Eve', 'social', 200.0, 1.0),

        # Work layer - middle period
        ('Bob', 'work', 'Charlie', 'work', 220.0, 1.0),
        ('Eve', 'work', 'Alice', 'work', 220.0, 1.0),

        # Social layer - late period
        ('David', 'social', 'Eve', 'social', 300.0, 1.0),
        ('Bob', 'social', 'David', 'social', 300.0, 1.0),
    ]

    tnet.add_edges(edges, input_type="tuple")

    return tnet


def demonstrate_temporal_filters(tnet: TemporalMultiLayerNetwork) -> None:
    """Demonstrate temporal filters in where() clause."""
    print("=== DSL Temporal Filters ===\n")
    print(f"Using sample network with {tnet.number_of_edges()} edges spanning {tnet.time_range()}")

    # Note: These examples show DSL query construction
    # Full executor support for windowed queries is a work in progress

    # Query 1: Time range filter with t__between
    print("Query 1: Edges between t=100 and t=200")
    q1 = Q.edges().where(t__between=(100.0, 200.0))
    print(f"  Query: {q1}")
    print(f"  Has temporal filter: {q1._select.where is not None}")
    
    # Query 2: Edges after a specific time
    print("\nQuery 2: Edges after t=200")
    q2 = Q.edges().where(t__gte=200.0)
    print(f"  Query: {q2}")
    
    # Query 3: Edges before a specific time
    print("\nQuery 3: Edges before t=150")
    q3 = Q.edges().where(t__lte=150.0)
    print(f"  Query: {q3}")
    
    # Query 4: Combining temporal and layer filters
    print("\nQuery 4: Social layer edges between t=100 and t=250")
    q4 = (
        Q.edges()
        .from_layers(L["social"])
        .where(t__between=(100.0, 250.0))
    )
    print(f"  Query: {q4}")
    print(f"  Has layer filter: {q4._select.layer_expr is not None}")
    print(f"  Has temporal filter: {q4._select.where is not None}")


def demonstrate_window_queries(tnet: TemporalMultiLayerNetwork) -> None:
    """Demonstrate window specifications."""
    print("\n=== DSL Window Queries ===\n")
    print(f"Windowing over time span {tnet.time_range()}")

    # Query 1: Non-overlapping windows
    print("Query 1: Compute degree in non-overlapping windows")
    q1 = (
        Q.nodes()
        .compute("degree")
        .window(100.0)
    )
    print(f"  Query: {q1}")
    print(f"  Window size: {q1._select.window_spec.window_size}")
    print(f"  Step: {q1._select.window_spec.step}")
    
    # Query 2: Overlapping windows
    print("\nQuery 2: Overlapping windows with step")
    q2 = (
        Q.nodes()
        .compute("degree", "betweenness_centrality")
        .window(100.0, step=50.0)
    )
    print(f"  Query: {q2}")
    print(f"  Window size: {q2._select.window_spec.window_size}")
    print(f"  Step: {q2._select.window_spec.step}")
    
    # Query 3: Duration strings (for datetime timestamps)
    print("\nQuery 3: Window with duration strings")
    q3 = Q.nodes().window("7d", step="1d")
    print(f"  Query: {q3}")
    print(f"  Window size: {q3._select.window_spec.window_size}")
    print(f"  Step: {q3._select.window_spec.step}")


def demonstrate_complex_queries(tnet: TemporalMultiLayerNetwork) -> None:
    """Demonstrate complex temporal queries."""
    print("\n=== Complex Temporal Queries ===\n")
    print(f"Available layers: {tnet.base_network.layers}")

    # Query 1: Multi-layer temporal analysis
    print("Query 1: Top nodes by centrality across layers and time")
    q1 = (
        Q.nodes()
        .from_layers(L["social"] + L["work"])
        .where(t__between=(100.0, 250.0))
        .compute("degree", "betweenness_centrality")
        .window(100.0, step=50.0)
        .order_by("betweenness_centrality", desc=True)
        .limit(5)
    )
    print(f"  Query components:")
    print(f"    - Layers: {q1._select.layer_expr is not None}")
    print(f"    - Temporal filter: {q1._select.where is not None}")
    print(f"    - Metrics: {len(q1._select.compute)}")
    print(f"    - Window: {q1._select.window_spec is not None}")
    print(f"    - Ordering: {len(q1._select.order_by)}")
    print(f"    - Limit: {q1._select.limit}")
    
    # Query 2: Per-layer temporal evolution
    print("\nQuery 2: Per-layer degree evolution over windows")
    q2 = (
        Q.nodes()
        .compute("degree")
        .window(100.0)
        .per_layer()  # Group by layer
    )
    print(f"  Query components:")
    print(f"    - Window: {q2._select.window_spec is not None}")
    print(f"    - Grouping: {q2._select.group_by}")
    
    # Query 3: Using existing temporal methods (at, during)
    print("\nQuery 3: Snapshot query with at()")
    q3 = (
        Q.nodes()
        .at(150.0)
        .compute("degree")
    )
    print(f"  Query components:")
    print(f"    - Temporal context: {q3._select.temporal_context.kind}")
    print(f"    - Time: {q3._select.temporal_context.t0}")


def demonstrate_query_composition():
    """Demonstrate composing temporal queries."""
    print("\n=== Query Composition ===\n")

    # Build query incrementally
    print("Building a temporal query step by step:")

    q = Q.edges()
    print(f"1. Start with edges: {q}")

    q = q.from_layers(L["social"])
    print(f"2. Filter to social layer: layer_expr={q._select.layer_expr is not None}")

    q = q.where(t__between=(100.0, 200.0))
    print(f"3. Add temporal filter: where={q._select.where is not None}")

    q = q.limit(10)
    print(f"4. Limit results: limit={q._select.limit}")

    print(f"\nFinal query has:")
    print(f"  - Layer filter: {q._select.layer_expr is not None}")
    print(f"  - Temporal filter: {q._select.where is not None}")
    print(f"  - Limit: {q._select.limit}")


def main() -> int:
    """Run all demonstrations."""
    tnet = create_sample_network()

    print("=" * 60)
    print("Temporal DSL Example")
    print("=" * 60)
    print()

    demonstrate_temporal_filters(tnet)
    demonstrate_window_queries(tnet)
    demonstrate_complex_queries(tnet)
    demonstrate_query_composition()

    print("\n" + "=" * 60)
    print("Note: Full executor support for windowed queries")
    print("is a work in progress. These examples demonstrate")
    print("the DSL query construction capabilities.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

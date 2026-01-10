"""Example demonstrating edge query support in py3plex DSL.

This example shows how to use the fully-supported edge query features
in both the builder API (Q.edges()) and the string DSL (execute_query).
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L, execute_query


def main():
    # Create a sample multilayer network
    network = multinet.multi_layer_network(directed=False)

    # Add nodes across two layers
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Carol', 'type': 'social'},
        {'source': 'Dave', 'type': 'work'},
        {'source': 'Eve', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    # Add edges (both intralayer and interlayer)
    edges = [
        # Social layer (intralayer)
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
        {'source': 'Alice', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social', 'weight': 3.0},
        # Work layer (intralayer)
        {'source': 'Dave', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work', 'weight': 1.5},
        # Cross-layer (interlayer)
        {'source': 'Alice', 'target': 'Dave', 'source_type': 'social', 'target_type': 'work', 'weight': 0.5},
    ]
    network.add_edges(edges)

    print("=" * 70)
    print("Edge Query Examples for py3plex DSL")
    print("=" * 70)

    # Example 1: Basic edge selection using builder API
    print("\n1. Select all edges (builder API):")
    result = Q.edges().execute(network)
    print(f"   Found {result.count} edges")
    print(f"   First edge: {result.edges[0]}")

    # Example 2: Filter intralayer edges
    print("\n2. Select only intralayer edges:")
    result = Q.edges().where(intralayer=True).execute(network)
    print(f"   Found {result.count} intralayer edges")
    for edge in result.edges:
        source_layer = edge[0][1]
        target_layer = edge[1][1]
        print(f"   - {edge[0][0]} ({source_layer}) <-> {edge[1][0]} ({target_layer})")

    # Example 3: Filter by weight
    print("\n3. Select edges with weight > 1.0:")
    result = Q.edges().where(weight__gt=1.0).execute(network)
    print(f"   Found {result.count} edges")
    for edge in result.edges:
        weight = edge[2].get('weight', 1.0) if len(edge) >= 3 else 1.0
        print(f"   - {edge[0][0]} <-> {edge[1][0]}, weight={weight}")

    # Example 4: Compute edge betweenness
    print("\n4. Compute edge betweenness centrality:")
    result = (
        Q.edges()
        .compute("edge_betweenness", alias="eb")
        .order_by("-eb")
        .limit(3)
        .execute(network)
    )
    print(f"   Top 3 edges by betweenness:")
    for edge in result.edges:
        edge_key = (edge[0], edge[1])
        eb = result.attributes["eb"].get(edge_key, 0)
        print(f"   - {edge[0][0]} <-> {edge[1][0]}, betweenness={eb:.4f}")

    # Example 5: Layer-specific edges
    print("\n5. Select edges from social layer:")
    result = (
        Q.edges()
        .from_layers(L["social"])
        .where(intralayer=True)
        .execute(network)
    )
    print(f"   Found {result.count} social intralayer edges")

    # Example 6: Interlayer edges between specific layers
    print("\n6. Select interlayer edges between social and work:")
    result = Q.edges().where(interlayer=("social", "work")).execute(network)
    print(f"   Found {result.count} interlayer edge(s)")
    for edge in result.edges:
        print(f"   - {edge[0][0]} ({edge[0][1]}) <-> {edge[1][0]} ({edge[1][1]})")

    # Example 7: Export to pandas DataFrame
    print("\n7. Export edge query results to pandas:")
    result = Q.edges().where(weight__ge=1.0).execute(network)
    df = result.to_pandas()
    print(f"   DataFrame shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print("\n   First 3 rows:")
    print(df.head(3).to_string())

    # Example 8: Using string DSL (legacy syntax)
    print("\n8. String DSL examples:")

    # Basic edge selection
    result = execute_query(network, 'SELECT edges')
    print(f"   a) SELECT edges: {result['count']} edges")

    # Filter by weight
    result = execute_query(network, 'SELECT edges WHERE weight > 1.0')
    print(f"   b) SELECT edges WHERE weight > 1.0: {result['count']} edges")

    # Compute measure
    result = execute_query(network, 'SELECT edges COMPUTE edge_betweenness')
    print(f"   c) SELECT edges COMPUTE edge_betweenness: computed for {len(result['computed']['edge_betweenness'])} edges")

    # From specific layer
    result = execute_query(network, "SELECT edges IN LAYER 'social'")
    print(f"   d) SELECT edges IN LAYER 'social': {result['count']} edges")

    print("\n" + "=" * 70)
    print("All edge query examples completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    main()

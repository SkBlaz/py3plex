"""Example: Layer Set Algebra in py3plex DSL.

This example demonstrates the new Layer Set Algebra feature that provides
expressive, composable layer selection for multilayer networks.

Features demonstrated:
- Set operations: union (|), intersection (&), difference (-), complement (~)
- String expression parsing
- Named layer groups
- Integration with DSL queries
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L, LayerSet


def create_sample_network():
    """Create a sample multilayer social-professional network."""
    network = multinet.multi_layer_network(directed=False)

    # Add nodes across multiple layers
    nodes = [
        # Social layers
        {'source': 'Alice', 'type': 'facebook'},
        {'source': 'Bob', 'type': 'facebook'},
        {'source': 'Charlie', 'type': 'twitter'},
        {'source': 'David', 'type': 'twitter'},

        # Professional layers
        {'source': 'Alice', 'type': 'linkedin'},
        {'source': 'Charlie', 'type': 'linkedin'},
        {'source': 'Eve', 'type': 'email'},
        {'source': 'Frank', 'type': 'email'},

        # Hobby layers
        {'source': 'Alice', 'type': 'sports'},
        {'source': 'Bob', 'type': 'sports'},
        {'source': 'Charlie', 'type': 'gaming'},

        # Coupling layer (infrastructure)
        {'source': 'Alice', 'type': 'coupling'},
        {'source': 'Bob', 'type': 'coupling'},
    ]
    network.add_nodes(nodes)

    # Add edges
    edges = [
        # Facebook connections
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'facebook', 'target_type': 'facebook'},

        # Twitter connections
        {'source': 'Charlie', 'target': 'David', 'source_type': 'twitter', 'target_type': 'twitter'},

        # LinkedIn connections
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'linkedin', 'target_type': 'linkedin'},

        # Email connections
        {'source': 'Eve', 'target': 'Frank', 'source_type': 'email', 'target_type': 'email'},

        # Sports connections
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'sports', 'target_type': 'sports'},

        # Coupling edges (cross-layer)
        {'source': 'Alice', 'target': 'Alice', 'source_type': 'coupling', 'target_type': 'facebook'},
        {'source': 'Bob', 'target': 'Bob', 'source_type': 'coupling', 'target_type': 'facebook'},
    ]
    network.add_edges(edges)

    return network


def example_basic_operations():
    """Demonstrate basic set operations."""
    print("\n" + "=" * 70)
    print("BASIC SET OPERATIONS")
    print("=" * 70)

    network = create_sample_network()

    # Example 1: All layers except coupling
    print("\n1. Difference: All layers except coupling")
    print("   Expression: L['* - coupling']")
    result = Q.nodes().from_layers(L["* - coupling"]).execute(network)
    df = result.to_pandas()
    print(f"   Layers: {sorted(df['layer'].unique())}")
    print(f"   Nodes: {len(df)}")

    # Example 2: Union of social media layers
    print("\n2. Union: Facebook OR Twitter")
    print("   Expression: L['facebook | twitter']")
    result = Q.nodes().from_layers(L["facebook | twitter"]).execute(network)
    df = result.to_pandas()
    print(f"   Layers: {sorted(df['layer'].unique())}")
    print(f"   Nodes: {len(df)}")

    # Example 3: Complement of professional layers
    print("\n3. Complement: NOT linkedin")
    print("   Expression: ~LayerSet('linkedin')")
    layers = ~LayerSet("linkedin")
    print(f"   Resolves to: {sorted(layers.resolve(network))}")


def example_named_groups():
    """Demonstrate named layer groups for reuse."""
    print("\n" + "=" * 70)
    print("NAMED LAYER GROUPS")
    print("=" * 70)

    network = create_sample_network()

    # Define named groups
    print("\n1. Defining layer groups...")

    # Social media group
    L.define("social_media", LayerSet.parse("facebook | twitter"))
    print("   - social_media = facebook | twitter")

    # Professional group
    L.define("professional", LayerSet.parse("linkedin | email"))
    print("   - professional = linkedin | email")

    # Hobby group
    L.define("hobby", LayerSet.parse("sports | gaming"))
    print("   - hobby = sports | gaming")

    # List all groups
    print("\n2. Listing all groups:")
    groups = L.list_groups()
    for name in sorted(groups.keys()):
        print(f"   - {name}")

    # Use groups in queries
    print("\n3. Using groups in queries:")

    # Query social media layers
    print("   a) Nodes in social_media group:")
    result = Q.nodes().from_layers(LayerSet("social_media")).execute(network)
    df = result.to_pandas()
    print(f"      Layers: {sorted(df['layer'].unique())}")
    print(f"      Nodes: {len(df)}")

    # Combine groups
    print("\n   b) Nodes in (social_media | professional) group:")
    result = Q.nodes().from_layers(
        LayerSet("social_media") | LayerSet("professional")
    ).execute(network)
    df = result.to_pandas()
    print(f"      Layers: {sorted(df['layer'].unique())}")
    print(f"      Nodes: {len(df)}")


def example_complex_expressions():
    """Demonstrate complex layer expressions."""
    print("\n" + "=" * 70)
    print("COMPLEX EXPRESSIONS")
    print("=" * 70)

    network = create_sample_network()

    # Define groups first
    L.define("social_media", LayerSet.parse("facebook | twitter"))
    L.define("professional", LayerSet.parse("linkedin | email"))

    # Example 1: Intersection of groups
    print("\n1. Nodes appearing in BOTH social_media AND professional layers")
    print("   Expression: LayerSet('social_media') & LayerSet('professional')")
    layers = LayerSet("social_media") & LayerSet("professional")
    print(f"   Explanation:\n{layers.explain(network)}")
    result = Q.nodes().from_layers(layers).execute(network)
    df = result.to_pandas()
    if len(df) > 0:
        print(f"   Found {len(df)} nodes")
    else:
        print("   No nodes appear in both groups (empty intersection)")

    # Example 2: Complex nested expression
    print("\n2. Complex: ((facebook | twitter) & linkedin) - coupling")
    print("   This finds nodes in (facebook OR twitter) AND linkedin, excluding coupling")
    layers = LayerSet.parse("((facebook | twitter) & linkedin) - coupling")
    print(f"   Explanation:\n{layers.explain(network)}")
    result = Q.nodes().from_layers(layers).execute(network)
    df = result.to_pandas()
    print(f"   Result: {len(df)} nodes")


def example_query_integration():
    """Demonstrate integration with DSL queries."""
    print("\n" + "=" * 70)
    print("INTEGRATION WITH DSL QUERIES")
    print("=" * 70)

    network = create_sample_network()

    # Example 1: Layer filtering with compute
    print("\n1. Computing degree on filtered layers")
    print("   Query: All layers except coupling, compute degree")
    result = (
        Q.nodes()
         .from_layers(L["* - coupling"])
         .compute("degree")
         .execute(network)
    )
    df = result.to_pandas()
    print(f"   Nodes analyzed: {len(df)}")
    print(f"   Average degree: {df['degree'].mean():.2f}")

    # Example 2: Layer filtering with WHERE clause
    print("\n2. Combining layer filtering with WHERE clause")
    print("   Query: Social media layers, degree > 0")
    L.define("social_media", LayerSet.parse("facebook | twitter"))
    result = (
        Q.nodes()
         .from_layers(LayerSet("social_media"))
         .where(degree__gt=0)
         .compute("degree")
         .execute(network)
    )
    df = result.to_pandas()
    print(f"   Nodes with degree > 0: {len(df)}")

    # Example 3: Layer filtering with ORDER BY and LIMIT
    print("\n3. Top nodes by degree in non-coupling layers")
    print("   Query: * - coupling, compute degree, order by degree DESC, limit 5")
    result = (
        Q.nodes()
         .from_layers(L["* - coupling"])
         .compute("degree")
         .order_by("degree", desc=True)
         .limit(5)
         .execute(network)
    )
    df = result.to_pandas()
    print(f"   Top {len(df)} nodes:")
    for _, row in df.iterrows():
        print(f"      {row['id']} ({row['layer']}): degree = {row['degree']}")


def example_introspection():
    """Demonstrate introspection and debugging."""
    print("\n" + "=" * 70)
    print("INTROSPECTION AND DEBUGGING")
    print("=" * 70)

    network = create_sample_network()

    # Example 1: Explain without network
    print("\n1. Explain expression structure (without network):")
    layers = LayerSet.parse("(facebook | twitter) - coupling")
    print(f"\n{layers.explain()}")

    # Example 2: Explain with network (shows resolution)
    print("\n2. Explain with network resolution:")
    print(f"\n{layers.explain(network)}")

    # Example 3: Direct resolution
    print("\n3. Direct resolution:")
    resolved = layers.resolve(network)
    print(f"   Resolved layers: {sorted(resolved)}")

    # Example 4: String representation
    print("\n4. String representation:")
    print(f"   repr: {layers}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("PY3PLEX DSL: LAYER SET ALGEBRA EXAMPLES")
    print("=" * 70)

    example_basic_operations()
    example_named_groups()
    example_complex_expressions()
    example_query_integration()
    example_introspection()

    print("\n" + "=" * 70)
    print(" ALL EXAMPLES COMPLETED")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  - Use L['expression'] for compact layer selection")
    print("  - Operators: | (union), & (intersection), - (difference), ~ (complement)")
    print("  - Define named groups with L.define() for reuse")
    print("  - Fully backward compatible with existing code")
    print("  - Use .explain() for debugging layer expressions")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

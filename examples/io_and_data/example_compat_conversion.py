"""
Example: Cross-compatibility conversion layer demonstration.

This example shows how to use py3plex's lossless conversion system
to work with different graph ecosystems.

Run with: python examples/interop/example_cross_compatibility.py
"""

from py3plex.compat import convert, to_ir
from py3plex.compat.schema import infer_schema
from py3plex.io.schema import MultiLayerGraph, Node, Layer, Edge


def create_sample_graph():
    """Create a sample multilayer network."""
    graph = MultiLayerGraph(directed=False)
    
    # Add layers
    graph.add_layer(Layer(id="social"))
    graph.add_layer(Layer(id="professional"))
    
    # Add nodes with attributes
    for name, age in [("Alice", 30), ("Bob", 25), ("Charlie", 35), ("Diana", 28)]:
        graph.add_node(Node(id=name, attributes={"age": age}))
    
    # Add edges with weights
    edges = [
        ("Alice", "Bob", "social", 0.8),
        ("Bob", "Charlie", "social", 0.6),
        ("Alice", "Charlie", "professional", 0.9),
        ("Charlie", "Diana", "professional", 0.7),
    ]
    
    for src, dst, layer, weight in edges:
        graph.add_edge(Edge(
            src=src, dst=dst,
            src_layer=layer, dst_layer=layer,
            attributes={"weight": weight}
        ))
    
    return graph


def main():
    """Run cross-compatibility examples."""
    print("\nPy3plex Cross-Compatibility Conversion Layer Example")
    print("=" * 60)
    
    # Create sample graph
    graph = create_sample_graph()
    print(f"\nCreated graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    
    # Example 1: NetworkX conversion
    print("\n1. NetworkX Conversion")
    print("-" * 60)
    try:
        nx_graph = convert(graph, "networkx")
        print(f"   ✓ Converted to NetworkX: {nx_graph.number_of_nodes()} nodes")
        
        # Convert back
        restored = convert(nx_graph, "py3plex")
        print(f"   ✓ Restored to py3plex: {len(restored.nodes)} nodes")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Example 2: Schema validation
    print("\n2. Schema Validation")
    print("-" * 60)
    try:
        ir = to_ir(graph)
        schema = infer_schema(ir)
        print(f"   Directed: {schema.directed}")
        print(f"   Multi: {schema.multi}")
        print(f"   Node ID type: {schema.node_id_type}")
        print(f"   Layers: {schema.layer_count}")
        print(f"   ✓ Schema inferred successfully")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Example 3: Error handling (SciPy strict mode should fail)
    print("\n3. Error Handling (Strict Mode)")
    print("-" * 60)
    try:
        from py3plex.compat.exceptions import CompatibilityError
        matrix = convert(graph, "scipy_sparse", strict=True)
        print(f"   ✓ Conversion succeeded")
    except CompatibilityError as e:
        print(f"   ✗ Expected error: {str(e)[:60]}...")
        print(f"   (This is correct - strict mode prevents lossy conversion)")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("\nFor more examples, see:")
    print("  - docs/compat/overview.md")
    print("  - docs/compat/examples.md")
    print()


if __name__ == "__main__":
    main()

"""Example usage of GraphProgram class.

This script demonstrates the key features of GraphProgram:
1. Creating programs from AST
2. Stable hashing
3. Program composition
4. Execution on networks
5. Explanation generation
6. Program comparison (diff)
7. Serialization

Run with:
    python examples/advanced/example_graph_program.py
"""

import json
from py3plex.dsl import Q, L
from py3plex.dsl.program import GraphProgram, compose
from py3plex.core import multinet


def create_sample_network():
    """Create a sample multilayer network for testing."""
    net = multinet.multi_layer_network()
    
    # Add nodes
    nodes = [
        {"source": "Alice", "type": "social"},
        {"source": "Bob", "type": "social"},
        {"source": "Charlie", "type": "social"},
        {"source": "David", "type": "social"},
        {"source": "Alice", "type": "work"},
        {"source": "Bob", "type": "work"},
        {"source": "Charlie", "type": "work"},
    ]
    net.add_nodes(nodes)
    
    # Add edges
    edges = [
        # Social layer
        {"source": "Alice", "target": "Bob", "source_type": "social", "target_type": "social"},
        {"source": "Alice", "target": "Charlie", "source_type": "social", "target_type": "social"},
        {"source": "Bob", "target": "Charlie", "source_type": "social", "target_type": "social"},
        {"source": "Charlie", "target": "David", "source_type": "social", "target_type": "social"},
        # Work layer
        {"source": "Alice", "target": "Bob", "source_type": "work", "target_type": "work"},
        {"source": "Bob", "target": "Charlie", "source_type": "work", "target_type": "work"},
    ]
    net.add_edges(edges)
    
    return net


def example_1_basic_program():
    """Example 1: Create and execute a basic program."""
    print("=" * 70)
    print("Example 1: Basic Program Creation and Execution")
    print("=" * 70)
    
    # Create network
    net = create_sample_network()
    
    # Create program from DSL query
    ast = Q.nodes().compute("degree").order_by("degree", desc=True).limit(5).to_ast()
    program = GraphProgram.from_ast(ast)
    
    print(f"\nProgram hash: {program.hash()}")
    print(f"Type signature: {program.type_signature}")
    print(f"\nProgram explanation:")
    print(program.explain())
    
    # Execute program
    print("\nExecuting program...")
    result = program.execute(net, progress=False)
    
    print("\nResults:")
    df = result.to_pandas()
    print(df.head())
    print()


def example_2_hashing():
    """Example 2: Stable hashing for reproducibility."""
    print("=" * 70)
    print("Example 2: Stable Hashing")
    print("=" * 70)
    
    # Create two identical programs
    ast1 = Q.nodes().compute("degree").to_ast()
    ast2 = Q.nodes().compute("degree").to_ast()
    
    program1 = GraphProgram.from_ast(ast1)
    program2 = GraphProgram.from_ast(ast2)
    
    print(f"\nProgram 1 hash: {program1.hash()}")
    print(f"Program 2 hash: {program2.hash()}")
    print(f"Hashes match: {program1.hash() == program2.hash()}")
    
    # Different program
    ast3 = Q.nodes().compute("betweenness").to_ast()
    program3 = GraphProgram.from_ast(ast3)
    
    print(f"\nProgram 3 hash: {program3.hash()}")
    print(f"Program 3 differs: {program1.hash() != program3.hash()}")
    print()


def example_3_composition():
    """Example 3: Program composition."""
    print("=" * 70)
    print("Example 3: Program Composition")
    print("=" * 70)
    
    # Create network
    net = create_sample_network()
    
    # Create two programs
    ast1 = Q.nodes().compute("degree").to_ast()
    program1 = GraphProgram.from_ast(ast1)
    print("\nProgram 1:")
    print(program1.explain())
    
    ast2 = Q.nodes().compute("clustering").to_ast()
    program2 = GraphProgram.from_ast(ast2)
    print("\nProgram 2:")
    print(program2.explain())
    
    # Compose programs
    composed = program1.compose(program2)
    print("\nComposed program:")
    print(composed.explain())
    
    # Execute composed program
    print("\nExecuting composed program...")
    result = composed.execute(net, progress=False)
    
    print("\nResults (both metrics computed):")
    df = result.to_pandas()
    print(df.head())
    
    # Check provenance
    print(f"\nProvenance chain: {composed.metadata.provenance_chain}")
    print()


def example_4_layer_filtering():
    """Example 4: Programs with layer filtering."""
    print("=" * 70)
    print("Example 4: Layer Filtering")
    print("=" * 70)
    
    # Create network
    net = create_sample_network()
    
    # Program for social layer
    ast_social = Q.nodes().from_layers(L["social"]).compute("degree").to_ast()
    program_social = GraphProgram.from_ast(ast_social)
    
    print("\nSocial layer program:")
    print(program_social.explain())
    
    result_social = program_social.execute(net, progress=False)
    print("\nSocial layer results:")
    print(result_social.to_pandas().head())
    
    # Program for work layer
    ast_work = Q.nodes().from_layers(L["work"]).compute("degree").to_ast()
    program_work = GraphProgram.from_ast(ast_work)
    
    print("\nWork layer program:")
    print(program_work.explain())
    
    result_work = program_work.execute(net, progress=False)
    print("\nWork layer results:")
    print(result_work.to_pandas().head())
    
    # Hashes should differ
    print(f"\nPrograms have different hashes: {program_social.hash() != program_work.hash()}")
    print()


def example_5_program_diff():
    """Example 5: Program comparison with diff."""
    print("=" * 70)
    print("Example 5: Program Diff")
    print("=" * 70)
    
    # Create three programs
    ast1 = Q.nodes().compute("degree").to_ast()
    program1 = GraphProgram.from_ast(ast1)
    
    ast2 = Q.nodes().compute("degree").to_ast()
    program2 = GraphProgram.from_ast(ast2)
    
    ast3 = Q.nodes().compute("betweenness").to_ast()
    program3 = GraphProgram.from_ast(ast3)
    
    # Diff identical programs
    print("\nDiff of identical programs:")
    diff_identical = program1.diff(program2)
    print(json.dumps(diff_identical, indent=2))
    
    # Diff different programs
    print("\nDiff of different programs:")
    diff_different = program1.diff(program3)
    print(json.dumps(diff_different, indent=2, default=str))
    print()


def example_6_serialization():
    """Example 6: Program serialization."""
    print("=" * 70)
    print("Example 6: Program Serialization")
    print("=" * 70)
    
    # Create program
    ast = Q.nodes().compute("degree").compute("betweenness").order_by("degree").limit(10).to_ast()
    program = GraphProgram.from_ast(ast)
    
    print("\nOriginal program:")
    print(program.explain())
    
    # Serialize to dict
    program_dict = program.to_dict()
    
    print("\nSerialized program (metadata only):")
    print(json.dumps(
        {"hash": program_dict["program_hash"], "metadata": program_dict["metadata"]},
        indent=2
    ))
    
    print("\nNote: Full deserialization (from_dict) not yet implemented")
    print("      as AST deserialization is complex.")
    print()


def example_7_optimize_placeholder():
    """Example 7: Optimization (placeholder)."""
    print("=" * 70)
    print("Example 7: Program Optimization (Placeholder)")
    print("=" * 70)
    
    # Create program
    ast = Q.nodes().compute("degree").compute("betweenness").to_ast()
    program = GraphProgram.from_ast(ast)
    
    print("\nOriginal program:")
    print(f"Hash: {program.hash()}")
    
    # Optimize (currently a no-op placeholder)
    optimized = program.optimize(level=2)
    
    print("\nOptimized program:")
    print(f"Hash: {optimized.hash()}")
    print(f"Same as original: {program.hash() == optimized.hash()}")
    
    print("\nNote: Optimization is a placeholder - will be implemented")
    print("      with rewrite engine in future versions.")
    print()


def example_8_provenance():
    """Example 8: Provenance tracking."""
    print("=" * 70)
    print("Example 8: Provenance Tracking")
    print("=" * 70)
    
    # Create programs with custom provenance
    ast1 = Q.nodes().compute("degree").to_ast()
    program1 = GraphProgram.from_ast(ast1, provenance=["user_query", "step1"])
    
    print("\nProgram 1 provenance:")
    print(f"  {program1.metadata.provenance_chain}")
    
    ast2 = Q.nodes().compute("betweenness").to_ast()
    program2 = GraphProgram.from_ast(ast2, provenance=["user_query", "step2"])
    
    print("\nProgram 2 provenance:")
    print(f"  {program2.metadata.provenance_chain}")
    
    # Compose - provenance is merged
    composed = program1.compose(program2)
    
    print("\nComposed program provenance:")
    print(f"  {composed.metadata.provenance_chain}")
    print("\nNote: Provenance chain includes both original chains plus 'compose' step")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "GraphProgram Examples".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    example_1_basic_program()
    example_2_hashing()
    example_3_composition()
    example_4_layer_filtering()
    example_5_program_diff()
    example_6_serialization()
    example_7_optimize_placeholder()
    example_8_provenance()
    
    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()

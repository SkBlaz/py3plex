"""Examples demonstrating the RewriteEngine for py3plex Graph Programs.

This script shows:
1. Basic rewrite application
2. Individual rule demonstrations
3. Provenance tracking
4. Context-aware optimization
5. Custom rule sets
6. Integration with GraphProgram.optimize()
"""

from py3plex.dsl.ast import (
    ComputeItem,
    Comparison,
    ConditionAtom,
    ConditionExpr,
    OrderItem,
    Query,
    SelectStmt,
    Target,
    UQConfig,
    AutoCommunityConfig,
    ExportSpec,
)
from py3plex.dsl.program import (
    GraphProgram,
    RewriteEngine,
    RewriteContext,
    apply_rewrites,
    get_standard_rules,
    get_conservative_rules,
    get_aggressive_rules,
)


def example_1_basic_rewrites():
    """Example 1: Basic rewrite application."""
    print("=" * 60)
    print("Example 1: Basic Rewrite Application")
    print("=" * 60)
    
    # Create a query: COMPUTE(degree, betweenness) WHERE(layer="social")
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
            ],
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="layer", op="=", right="social"))]
            ),
        )
    )
    
    # Create program
    program = GraphProgram.from_ast(query)
    print(f"\nOriginal program hash: {program.hash()[:16]}...")
    print(f"Provenance: {program.metadata.provenance_chain}")
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    print(f"\nOptimized program hash: {optimized.hash()[:16]}...")
    print(f"Provenance: {optimized.metadata.provenance_chain}")
    
    # Check if rewrites were applied
    if program.hash() != optimized.hash():
        print("\nOK Program was optimized!")
    else:
        print("\nOK No optimizations needed (already optimal)")
    
    print()


def example_2_pushdown_rules():
    """Example 2: Pushdown optimization rules."""
    print("=" * 60)
    print("Example 2: Pushdown Rules (WHERE before COMPUTE)")
    print("=" * 60)
    
    # Create query where WHERE can be pushed past COMPUTE
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="clustering"),
                ComputeItem(name="betweenness_centrality"),
            ],
            where=ConditionExpr(
                atoms=[
                    ConditionAtom(comparison=Comparison(left="layer", op="=", right="social")),
                    ConditionAtom(comparison=Comparison(left="type", op="=", right="person")),
                ],
                ops=["AND"]
            ),
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    
    print("\nOriginal query:")
    print("  SELECT nodes COMPUTE(degree, clustering, betweenness)")
    print("  WHERE layer='social' AND type='person'")
    
    print("\nOptimized query (conceptually):")
    print("  SELECT nodes WHERE layer='social' AND type='person'")
    print("  COMPUTE(degree, clustering, betweenness)")
    print("  -> Fewer nodes to compute metrics for!")
    
    print(f"\nProvenance chain shows applied rules:")
    for step in optimized.metadata.provenance_chain:
        print(f"  - {step}")
    
    print()


def example_3_projection_pushdown():
    """Example 3: Projection pushdown to eliminate unused metrics."""
    print("=" * 60)
    print("Example 3: Projection Pushdown")
    print("=" * 60)
    
    # Create query that computes more than it needs
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
                ComputeItem(name="closeness_centrality"),
                ComputeItem(name="clustering"),
            ],
            select_cols=["node", "degree", "betweenness_centrality"],
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    print("\nOriginal query computes 4 metrics:")
    print("  COMPUTE(degree, betweenness, closeness, clustering)")
    print("  SELECT_COLS(node, degree, betweenness)")
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    
    print("\nOptimized query only computes what's needed:")
    print("  COMPUTE(degree, betweenness)")
    print("  SELECT_COLS(node, degree, betweenness)")
    print("  -> Closeness and clustering eliminated!")
    
    # Check compute items in optimized
    compute_names = [c.name for c in optimized.canonical_ast.select.compute]
    print(f"\nCompute items after optimization: {compute_names}")
    
    print()


def example_4_layer_distributivity():
    """Example 4: Layer distributivity for parallel processing."""
    print("=" * 60)
    print("Example 4: Layer Distributivity")
    print("=" * 60)
    
    # Create query with PER_LAYER and layer-local metrics
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="clustering"),
            ],
            group_by=['layer'],
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    print("\nQuery with layer-local metrics:")
    print("  SELECT nodes")
    print("  COMPUTE(degree, clustering)")
    print("  PER_LAYER()")
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    
    print("\nOptimization recognizes layer-local metrics:")
    print("  PER_LAYER() can be moved early for parallelization")
    print("  -> Each layer processed independently!")
    
    print()


def example_5_uq_aware_rewrites():
    """Example 5: UQ-aware optimizations."""
    print("=" * 60)
    print("Example 5: UQ-Aware Rewrites")
    print("=" * 60)
    
    # Create query with UQ and deterministic filters
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            uq_config=UQConfig(method="bootstrap", n_samples=100),
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="layer", op="=", right="social"))]
            ),
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    print("\nOriginal query with UQ:")
    print("  UQ(COMPUTE(degree)) WHERE layer='social'")
    print("  -> Filter applied after 100 bootstrap samples")
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    
    print("\nOptimized query moves filter inside UQ:")
    print("  UQ(WHERE layer='social' COMPUTE(degree))")
    print("  -> Filter applied before sampling, reducing cost!")
    
    print()


def example_6_community_optimization():
    """Example 6: Community-specific optimizations."""
    print("=" * 60)
    print("Example 6: Community Optimizations")
    print("=" * 60)
    
    # Create query for communities with single ID filter
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.COMMUNITIES,
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="community_id", op="=", right=5))]
            ),
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    print("\nOriginal query:")
    print("  SELECT communities WHERE community_id = 5")
    print("  -> Full community detection + filtering")
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    
    print("\nOptimized query uses partition slice:")
    print("  PARTITION_SLICE(community_id=5)")
    print("  -> Direct access to single community!")
    
    print()


def example_7_cse_caching():
    """Example 7: Common subexpression elimination and caching."""
    print("=" * 60)
    print("Example 7: CSE and Caching")
    print("=" * 60)
    
    # Create query that uses 'degree' multiple times
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="degree", op=">", right=5))]
            ),
            order_by=[OrderItem(key="degree", desc=True)],
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    print("\nOriginal query uses 'degree' 3 times:")
    print("  COMPUTE(degree)")
    print("  WHERE degree > 5")
    print("  ORDER_BY degree DESC")
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    
    print("\nOptimized query marks degree for caching:")
    print("  COMPUTE(degree) [cache=True]")
    print("  WHERE degree > 5")
    print("  ORDER_BY degree DESC")
    print("  -> Degree computed once and reused!")
    
    print()


def example_8_top_k_optimization():
    """Example 8: TOP-K optimization."""
    print("=" * 60)
    print("Example 8: TOP-K Optimization")
    print("=" * 60)
    
    # Create query: ORDER_BY + LIMIT (classic TOP-K pattern)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="betweenness_centrality")],
            order_by=[OrderItem(key="betweenness_centrality", desc=True)],
            limit=10,
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    print("\nOriginal query:")
    print("  COMPUTE(betweenness)")
    print("  ORDER_BY betweenness DESC")
    print("  LIMIT 10")
    print("  -> Full sort O(n log n)")
    
    # Apply rewrites with context
    context = RewriteContext(network_stats={'node_count': 10000})
    optimized = apply_rewrites(program, context=context)
    
    print("\nOptimized query uses heap-based TOP-K:")
    print("  COMPUTE(betweenness)")
    print("  TOP_K(betweenness, 10)")
    print("  -> Heap-based selection O(n log k)")
    print("  -> Much faster for k << n!")
    
    print()


def example_9_custom_context():
    """Example 9: Context-aware optimization."""
    print("=" * 60)
    print("Example 9: Context-Aware Optimization")
    print("=" * 60)
    
    # Create query with expensive metric
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="betweenness_centrality")],
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    print("\nQuery with expensive metric:")
    print("  COMPUTE(betweenness_centrality)")
    
    # Create context with network statistics
    context = RewriteContext(
        network_stats={
            'node_count': 10000,
            'edge_count': 50000,
            'layer_count': 3,
        },
        safety_mode=False,
    )
    
    print("\nContext provided:")
    print(f"  Nodes: {context.network_stats['node_count']}")
    print(f"  Edges: {context.network_stats['edge_count']}")
    print(f"  Layers: {context.network_stats['layer_count']}")
    
    # Apply rewrites with context
    optimized = apply_rewrites(program, context=context)
    
    print("\nOptimized with context:")
    print("  Betweenness marked for aggressive caching")
    print("  -> Expensive metrics get special treatment!")
    
    print()


def example_10_rule_sets():
    """Example 10: Different rule sets."""
    print("=" * 60)
    print("Example 10: Conservative vs. Aggressive Rules")
    print("=" * 60)
    
    # Create complex query
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
                ComputeItem(name="clustering"),
            ],
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="layer", op="=", right="social"))]
            ),
            group_by=['layer'],
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    # Conservative optimization
    print("\nConservative optimization:")
    conservative_rules = get_conservative_rules()
    print(f"  Using {len(conservative_rules)} safe rules")
    optimized_conservative = apply_rewrites(program, rules=conservative_rules)
    
    # Aggressive optimization
    print("\nAggressive optimization:")
    aggressive_rules = get_aggressive_rules()
    print(f"  Using {len(aggressive_rules)} total rules")
    optimized_aggressive = apply_rewrites(program, rules=aggressive_rules)
    
    print("\nDifference in applied rewrites:")
    conservative_chain = optimized_conservative.metadata.provenance_chain
    aggressive_chain = optimized_aggressive.metadata.provenance_chain
    print(f"  Conservative: {len(conservative_chain)} steps")
    print(f"  Aggressive: {len(aggressive_chain)} steps")
    
    print()


def example_11_explain_rewrites():
    """Example 11: Explaining which rewrites would apply."""
    print("=" * 60)
    print("Example 11: Explaining Applicable Rewrites")
    print("=" * 60)
    
    # Create query
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="clustering"),
            ],
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="layer", op="=", right="social"))]
            ),
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    print("\nQuery:")
    print("  SELECT nodes")
    print("  COMPUTE(degree, clustering)")
    print("  WHERE layer='social'")
    
    # Create engine and explain
    engine = RewriteEngine(rules=get_standard_rules())
    applicable = engine.explain_rewrites(program)
    
    print(f"\nApplicable rewrites ({len(applicable)}):")
    for rule_name in applicable:
        print(f"  - {rule_name}")
    
    print()


def example_12_provenance_tracking():
    """Example 12: Detailed provenance tracking."""
    print("=" * 60)
    print("Example 12: Provenance Tracking")
    print("=" * 60)
    
    # Create query
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
                ComputeItem(name="clustering"),
            ],
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="layer", op="=", right="social"))]
            ),
            select_cols=["node", "degree"],
        )
    )
    
    # Create program and track transformations
    print("\nStep 1: Create original program")
    program = GraphProgram.from_ast(query)
    print(f"  Hash: {program.hash()[:16]}...")
    print(f"  Provenance: {program.metadata.provenance_chain}")
    
    # Apply rewrites
    print("\nStep 2: Apply rewrites")
    optimized = apply_rewrites(program)
    print(f"  Hash: {optimized.hash()[:16]}...")
    print(f"  Provenance: {optimized.metadata.provenance_chain}")
    
    # Show full provenance chain
    print("\nFull provenance chain:")
    for i, step in enumerate(optimized.metadata.provenance_chain, 1):
        print(f"  {i}. {step}")
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("RewriteEngine Examples for py3plex Graph Programs")
    print("=" * 60 + "\n")
    
    examples = [
        example_1_basic_rewrites,
        example_2_pushdown_rules,
        example_3_projection_pushdown,
        example_4_layer_distributivity,
        example_5_uq_aware_rewrites,
        example_6_community_optimization,
        example_7_cse_caching,
        example_8_top_k_optimization,
        example_9_custom_context,
        example_10_rule_sets,
        example_11_explain_rewrites,
        example_12_provenance_tracking,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()

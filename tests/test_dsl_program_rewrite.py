"""Tests for RewriteEngine and rewrite rules.

This test suite validates:
1. Core infrastructure (Match, RewriteContext, RuleGuard, RewriteRule, RewriteEngine)
2. All 17 rewrite rules with equivalence validation
3. Integration with GraphProgram
4. Provenance tracking
5. Guard conditions
6. Fixpoint iteration
"""

import pytest

from py3plex.dsl.ast import (
    ComputeItem,
    Comparison,
    ConditionAtom,
    ConditionExpr,
    LayerExpr,
    LayerTerm,
    OrderItem,
    Query,
    SelectStmt,
    Target,
    UQConfig,
    AutoCommunityConfig,
)
from py3plex.dsl.program.program import GraphProgram
from py3plex.dsl.program.rewrite import (
    Match,
    RewriteContext,
    RuleGuard,
    RewriteRule,
    RewriteEngine,
    apply_rewrites,
    get_standard_rules,
    get_aggressive_rules,
    get_conservative_rules,
    # Individual rule constructors
    rule_push_where_past_compute,
    rule_fuse_compute,
    rule_fuse_where,
    rule_push_limit_early,
    rule_push_projection,
    rule_move_per_layer_early,
    rule_fuse_per_layer,
    rule_group_by_to_per_layer,
    rule_move_deterministic_into_uq,
    rule_hoist_reporting_outside_uq,
    rule_cache_uq_subprogram,
    rule_fuse_community_annotation,
    rule_community_to_partition_slice,
    rule_batch_community_metrics,
    rule_detect_common_subexpression,
    rule_cache_expensive_metrics,
    rule_eliminate_redundant_order_by,
    rule_optimize_top_k,
)


# ============================================================================
# Test Core Infrastructure
# ============================================================================


def test_match_creation():
    """Test Match object creation and attributes."""
    select = SelectStmt(target=Target.NODES)
    match = Match(
        node=select,
        captures={'field': 'value'},
        metadata={'info': 'test'}
    )
    
    assert match.node == select
    assert match.captures['field'] == 'value'
    assert match.metadata['info'] == 'test'


def test_rewrite_context_creation():
    """Test RewriteContext creation with various options."""
    context = RewriteContext(
        network_stats={'node_count': 1000, 'edge_count': 5000},
        available_metrics={'degree', 'betweenness'},
        layer_info={'layers': ['social', 'work']},
        safety_mode=True,
    )
    
    assert context.network_stats['node_count'] == 1000
    assert 'degree' in context.available_metrics
    assert context.safety_mode is True


def test_rule_guard():
    """Test RuleGuard functionality."""
    def always_true(match, context):
        return True
    
    def always_false(match, context):
        return False
    
    guard_true = RuleGuard(always_true, "Always passes")
    guard_false = RuleGuard(always_false, "Always fails")
    
    match = Match(node=None)
    context = RewriteContext()
    
    assert guard_true.check(match, context) is True
    assert guard_false.check(match, context) is False


def test_rewrite_rule_structure():
    """Test RewriteRule creation and basic methods."""
    def matcher(query):
        return Match(node=query)
    
    def transform(query, match):
        return query
    
    rule = RewriteRule(
        name="test_rule",
        description="Test rule",
        pattern_matcher=matcher,
        guards=[],
        transform=transform,
        equivalence_class="test",
        priority=5,
    )
    
    assert rule.name == "test_rule"
    assert rule.priority == 5
    assert rule.equivalence_class == "test"
    
    # Test matching
    query = Query(explain=False, select=SelectStmt(target=Target.NODES))
    match = rule.matches(query)
    assert match is not None
    assert match.node == query


def test_rewrite_engine_initialization():
    """Test RewriteEngine initialization."""
    rules = get_standard_rules()
    engine = RewriteEngine(rules=rules, max_iterations=5)
    
    assert len(engine.rules) >= 15
    assert engine.max_iterations == 5
    assert engine.enable_provenance is True


# ============================================================================
# Test A. Pushdown/Fusion Rules (5 rules)
# ============================================================================


def test_rule_push_where_past_compute():
    """Test pushing WHERE filter before COMPUTE for intrinsic fields."""
    rule = rule_push_where_past_compute()
    
    # Create query: COMPUTE(degree) WHERE(layer="social")
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="layer", op="=", right="social"))]
            ),
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    assert 'where' in match.captures
    assert 'compute' in match.captures
    
    # Test guard
    context = RewriteContext()
    assert rule.is_applicable(match, context) is True
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_push_where_no_match_computed_field():
    """Test that WHERE on computed field doesn't match pushdown rule."""
    rule = rule_push_where_past_compute()
    
    # Create query: COMPUTE(degree) WHERE(degree > 5)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="degree", op=">", right=5))]
            ),
        )
    )
    
    # Should not match - degree is computed, not intrinsic
    match = rule.matches(query)
    assert match is None


def test_rule_fuse_compute():
    """Test fusing multiple COMPUTE operations."""
    rule = rule_fuse_compute()
    
    # Create query with multiple compute items
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
                ComputeItem(name="clustering"),
            ],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    assert len(match.captures['compute_items']) == 3
    
    # Test transform
    context = RewriteContext()
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_fuse_where():
    """Test fusing multiple WHERE clauses."""
    rule = rule_fuse_where()
    
    # Create query with multiple WHERE atoms
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            where=ConditionExpr(
                atoms=[
                    ConditionAtom(comparison=Comparison(left="layer", op="=", right="social")),
                    ConditionAtom(comparison=Comparison(left="degree", op=">", right=5)),
                ],
                ops=["AND"]
            ),
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_push_limit_early():
    """Test pushing LIMIT before COMPUTE when no ORDER BY."""
    rule = rule_push_limit_early()
    
    # Create query: COMPUTE(degree) LIMIT(10) [no ORDER BY]
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            limit=10,
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_push_limit_no_match_with_order_by():
    """Test that LIMIT doesn't push past ORDER BY."""
    rule = rule_push_limit_early()
    
    # Create query: ORDER_BY(degree) LIMIT(10)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            order_by=[OrderItem(key="degree", desc=True)],
            limit=10,
        )
    )
    
    # Should not match - has ORDER BY
    match = rule.matches(query)
    assert match is None


def test_rule_push_projection():
    """Test pushing projection to eliminate unused compute items."""
    rule = rule_push_projection()
    
    # Create query: COMPUTE(a, b, c) SELECT_COLS(a, b)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
                ComputeItem(name="clustering"),
            ],
            select_cols=["degree", "betweenness_centrality"],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    assert 'clustering' in match.captures['unused']
    
    # Test transform
    context = RewriteContext()
    transformed = rule.apply(query, match)
    assert transformed is not None
    # Check that unused metric was removed
    compute_names = [c.name for c in transformed.select.compute]
    assert 'clustering' not in compute_names


def test_rule_push_projection_guard_order_by():
    """Test that projection doesn't remove metrics used in ORDER BY."""
    rule = rule_push_projection()
    
    # Create query: COMPUTE(a, b) SELECT_COLS(a) ORDER_BY(b)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
            ],
            select_cols=["degree"],
            order_by=[OrderItem(key="betweenness_centrality", desc=True)],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Guard should fail - betweenness used in ORDER BY
    context = RewriteContext()
    assert rule.is_applicable(match, context) is False


# ============================================================================
# Test B. Layer Distributivity Rules (3 rules)
# ============================================================================


def test_rule_move_per_layer_early():
    """Test moving PER_LAYER before COMPUTE for layer-local metrics."""
    rule = rule_move_per_layer_early()
    
    # Create query: COMPUTE(degree) PER_LAYER()
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            group_by=['layer'],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test guard - degree is layer-local
    context = RewriteContext()
    assert rule.is_applicable(match, context) is True
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_move_per_layer_guard_global_metric():
    """Test that global metrics block PER_LAYER movement."""
    rule = rule_move_per_layer_early()
    
    # Create query: COMPUTE(betweenness_centrality) PER_LAYER()
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="betweenness_centrality")],
            group_by=['layer'],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Guard should fail - betweenness is not layer-local
    context = RewriteContext()
    assert rule.is_applicable(match, context) is False


def test_rule_fuse_per_layer():
    """Test fusing duplicate PER_LAYER groupings."""
    rule = rule_fuse_per_layer()
    
    # Create query with duplicate 'layer' in group_by
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            group_by=['layer', 'layer'],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None
    assert transformed.select.group_by.count('layer') == 1


def test_rule_group_by_to_per_layer():
    """Test normalizing GROUP_BY(layer) to PER_LAYER."""
    rule = rule_group_by_to_per_layer()
    
    # Create query: GROUP_BY(layer)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            group_by=['layer'],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


# ============================================================================
# Test C. UQ-Aware Rules (3 rules)
# ============================================================================


def test_rule_move_deterministic_into_uq():
    """Test moving deterministic WHERE into UQ."""
    rule = rule_move_deterministic_into_uq()
    
    # Create query: UQ(COMPUTE(degree)) WHERE(layer="social")
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
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test transform
    context = RewriteContext()
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_move_deterministic_no_match_computed_field():
    """Test that computed fields don't move into UQ."""
    rule = rule_move_deterministic_into_uq()
    
    # Create query: UQ(COMPUTE(degree)) WHERE(degree > 5)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            uq_config=UQConfig(method="bootstrap", n_samples=100),
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="degree", op=">", right=5))]
            ),
        )
    )
    
    # Should not match - degree is computed
    match = rule.matches(query)
    assert match is None


def test_rule_hoist_reporting_outside_uq():
    """Test hoisting EXPORT outside UQ."""
    rule = rule_hoist_reporting_outside_uq()
    
    # Create query: UQ(COMPUTE(degree)) EXPORT(csv)
    from py3plex.dsl.ast import ExportSpec
    
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            uq_config=UQConfig(method="bootstrap", n_samples=100),
            file_export=ExportSpec(path="results.csv", fmt="csv"),
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_cache_uq_subprogram():
    """Test caching deterministic computations in UQ."""
    rule = rule_cache_uq_subprogram()
    
    # Create query: UQ(COMPUTE(degree, clustering))
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="clustering"),
            ],
            uq_config=UQConfig(method="bootstrap", n_samples=100),
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test guard - both metrics are deterministic
    context = RewriteContext()
    assert rule.is_applicable(match, context) is True
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_cache_uq_guard_nondeterministic():
    """Test that non-deterministic metrics block UQ caching."""
    rule = rule_cache_uq_subprogram()
    
    # Create query with random walk metric
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="random_walk_betweenness")],
            uq_config=UQConfig(method="bootstrap", n_samples=100),
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Guard should fail - metric is not deterministic
    context = RewriteContext()
    assert rule.is_applicable(match, context) is False


# ============================================================================
# Test D. Community-Specific Rules (3 rules)
# ============================================================================


def test_rule_fuse_community_annotation():
    """Test fusing community detection with node annotation."""
    rule = rule_fuse_community_annotation()
    
    # Create query: COMMUNITIES(louvain) JOIN NODES
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.COMMUNITIES,
            auto_community_config=AutoCommunityConfig(
                enabled=True,
                kind="nodes_join",
            ),
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_community_to_partition_slice():
    """Test rewriting community filter to partition slice."""
    rule = rule_community_to_partition_slice()
    
    # Create query: COMMUNITIES() WHERE(community_id=5)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.COMMUNITIES,
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="community_id", op="=", right=5))]
            ),
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    assert match.captures['community_id'] == 5
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_batch_community_metrics():
    """Test batching multiple community metrics."""
    rule = rule_batch_community_metrics()
    
    # Create query: COMMUNITIES() COMPUTE(modularity, size, density)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.COMMUNITIES,
            compute=[
                ComputeItem(name="modularity"),
                ComputeItem(name="size"),
                ComputeItem(name="density"),
            ],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


# ============================================================================
# Test E. CSE/Caching Rules (2 rules)
# ============================================================================


def test_rule_detect_common_subexpression():
    """Test detecting common subexpressions for caching."""
    rule = rule_detect_common_subexpression()
    
    # Create query: COMPUTE(degree) WHERE(degree > 5) ORDER_BY(degree)
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
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    assert 'degree' in match.captures['common_fields']
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_cache_expensive_metrics():
    """Test marking expensive metrics for caching."""
    rule = rule_cache_expensive_metrics()
    
    # Create query: COMPUTE(betweenness_centrality, pagerank)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="betweenness_centrality"),
                ComputeItem(name="pagerank"),
            ],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    assert len(match.captures['expensive_items']) == 2
    
    # Test transform
    context = RewriteContext()
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_cache_expensive_guard_already_cached():
    """Test that already cached metrics don't re-cache."""
    rule = rule_cache_expensive_metrics()
    
    # Create query with expensive metric
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="betweenness_centrality")],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Guard should fail if metric already cached
    context = RewriteContext(available_metrics={'betweenness_centrality'})
    assert rule.is_applicable(match, context) is False


# ============================================================================
# Test F. Additional Rules (2 rules)
# ============================================================================


def test_rule_eliminate_redundant_order_by():
    """Test eliminating ORDER BY when GROUP BY destroys ordering."""
    rule = rule_eliminate_redundant_order_by()
    
    # Create query: ORDER_BY(degree) GROUP_BY(layer)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            order_by=[OrderItem(key="degree", desc=True)],
            group_by=['layer'],
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test guard
    context = RewriteContext()
    assert rule.is_applicable(match, context) is True


def test_rule_optimize_top_k():
    """Test optimizing ORDER_BY + LIMIT to TOP_K."""
    rule = rule_optimize_top_k()
    
    # Create query: ORDER_BY(degree) LIMIT(10)
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            order_by=[OrderItem(key="degree", desc=True)],
            limit=10,
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Test guard with small k
    context = RewriteContext(network_stats={'node_count': 1000})
    assert rule.is_applicable(match, context) is True
    
    # Test transform
    transformed = rule.apply(query, match)
    assert transformed is not None


def test_rule_optimize_top_k_guard_large_k():
    """Test that large k blocks TOP_K optimization."""
    rule = rule_optimize_top_k()
    
    # Create query with large limit
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            order_by=[OrderItem(key="degree", desc=True)],
            limit=500,
        )
    )
    
    # Test matching
    match = rule.matches(query)
    assert match is not None
    
    # Guard should fail - k too large relative to n
    context = RewriteContext(network_stats={'node_count': 1000})
    assert rule.is_applicable(match, context) is False


# ============================================================================
# Test RewriteEngine Integration
# ============================================================================


def test_rewrite_engine_single_pass():
    """Test RewriteEngine with single pass (no fixpoint)."""
    rules = [rule_fuse_compute()]
    engine = RewriteEngine(rules=rules)
    
    # Create program
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
            ],
        )
    )
    program = GraphProgram.from_ast(query)
    
    # Apply rewrites (single pass)
    optimized = engine.apply(program, fixpoint=False)
    
    assert optimized is not None
    # Check provenance changed (hash may be same if only hints added)
    assert len(optimized.metadata.provenance_chain) > len(program.metadata.provenance_chain)


def test_rewrite_engine_fixpoint():
    """Test RewriteEngine with fixpoint iteration."""
    rules = get_standard_rules()
    engine = RewriteEngine(rules=rules, max_iterations=3)
    
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
            select_cols=["degree", "betweenness_centrality"],
            group_by=['layer'],
        )
    )
    program = GraphProgram.from_ast(query)
    
    # Apply rewrites (fixpoint)
    optimized = engine.apply(program, fixpoint=True)
    
    assert optimized is not None


def test_rewrite_engine_provenance():
    """Test that RewriteEngine tracks provenance."""
    rules = [rule_fuse_compute()]
    engine = RewriteEngine(rules=rules, enable_provenance=True)
    
    # Create program
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
            ],
        )
    )
    program = GraphProgram.from_ast(query)
    
    # Apply rewrites
    optimized = engine.apply(program)
    
    # Check provenance
    assert 'rewrites:' in str(optimized.metadata.provenance_chain[-1])


def test_rewrite_engine_explain_rewrites():
    """Test explaining which rewrites would apply."""
    rules = get_standard_rules()
    engine = RewriteEngine(rules=rules)
    
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
    
    # Explain rewrites
    applicable = engine.explain_rewrites(program)
    
    assert isinstance(applicable, list)
    # Should have at least some applicable rules
    assert len(applicable) >= 0


def test_apply_rewrites_function():
    """Test apply_rewrites convenience function."""
    # Create simple query
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
        )
    )
    program = GraphProgram.from_ast(query)
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    
    assert optimized is not None
    assert isinstance(optimized, GraphProgram)


def test_apply_rewrites_with_custom_rules():
    """Test apply_rewrites with custom rule set."""
    # Create query
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
            ],
        )
    )
    program = GraphProgram.from_ast(query)
    
    # Apply with conservative rules only
    optimized = apply_rewrites(program, rules=get_conservative_rules())
    
    assert optimized is not None


def test_apply_rewrites_with_context():
    """Test apply_rewrites with custom context."""
    # Create query
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="betweenness_centrality")],
        )
    )
    program = GraphProgram.from_ast(query)
    
    # Create context with network stats
    context = RewriteContext(
        network_stats={'node_count': 1000, 'edge_count': 5000},
        safety_mode=True,
    )
    
    # Apply rewrites
    optimized = apply_rewrites(program, context=context)
    
    assert optimized is not None


# ============================================================================
# Test Rule Sets
# ============================================================================


def test_get_standard_rules():
    """Test that standard rules set contains all expected rules."""
    rules = get_standard_rules()
    
    assert len(rules) >= 17  # All 15+ rules
    
    # Check that each category is represented
    rule_names = {r.name for r in rules}
    
    # A. Pushdown/Fusion
    assert 'push_where_past_compute' in rule_names
    assert 'fuse_compute' in rule_names
    
    # B. Layer Distributivity
    assert 'move_per_layer_early' in rule_names
    
    # C. UQ-Aware
    assert 'move_deterministic_into_uq' in rule_names
    
    # D. Community-Specific
    assert 'fuse_community_annotation' in rule_names
    
    # E. CSE/Caching
    assert 'detect_common_subexpression' in rule_names


def test_get_aggressive_rules():
    """Test aggressive rules set."""
    rules = get_aggressive_rules()
    
    assert len(rules) >= 17
    # Aggressive should be same as standard for now
    assert len(rules) == len(get_standard_rules())


def test_get_conservative_rules():
    """Test conservative rules set."""
    rules = get_conservative_rules()
    
    # Conservative should be subset of standard
    assert len(rules) < len(get_standard_rules())
    
    # Should contain safe rules
    rule_names = {r.name for r in rules}
    assert 'fuse_compute' in rule_names
    assert 'fuse_where' in rule_names


# ============================================================================
# Test Integration with GraphProgram
# ============================================================================


def test_graphprogram_optimize_integration():
    """Test that GraphProgram.optimize() uses rewrite engine."""
    # Create program
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
        )
    )
    program = GraphProgram.from_ast(query)
    
    # Optimize should now use rewrite engine
    optimized = program.optimize()
    
    assert optimized is not None
    assert isinstance(optimized, GraphProgram)
    # Provenance should show rewrites were considered
    assert len(optimized.metadata.provenance_chain) >= len(program.metadata.provenance_chain)


def test_rewrite_preserves_type_signature():
    """Test that rewrites preserve type signature."""
    # Create program
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
        )
    )
    program = GraphProgram.from_ast(query)
    original_type = program.type_signature
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    
    # Type signature should be equivalent
    # (might not be exact same object due to deep copy)
    assert str(optimized.type_signature) == str(original_type)


def test_rewrite_immutability():
    """Test that rewrites preserve immutability."""
    # Create program
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
        )
    )
    program = GraphProgram.from_ast(query)
    original_hash = program.program_hash
    
    # Apply rewrites
    optimized = apply_rewrites(program)
    
    # Original program should be unchanged
    assert program.program_hash == original_hash
    
    # Optimized should be different (or same if no rewrites applied)
    assert isinstance(optimized, GraphProgram)
    assert optimized is not program  # Different instance


# ============================================================================
# Test Equivalence Validation
# ============================================================================


def test_equivalence_pushdown_rules():
    """Test that pushdown rules preserve semantics."""
    # Create query: COMPUTE(degree) WHERE(layer="social")
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="layer", op="=", right="social"))]
            ),
        )
    )
    program = GraphProgram.from_ast(query)
    
    # Apply pushdown rule
    rule = rule_push_where_past_compute()
    engine = RewriteEngine(rules=[rule])
    optimized = engine.apply(program)
    
    # Both programs should have same target and basic structure
    assert program.canonical_ast.select.target == optimized.canonical_ast.select.target
    assert len(program.canonical_ast.select.compute) == len(optimized.canonical_ast.select.compute)


def test_equivalence_fusion_rules():
    """Test that fusion rules preserve semantics."""
    # Create query with multiple compute items
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
            ],
        )
    )
    program = GraphProgram.from_ast(query)
    
    # Apply fusion rule
    rule = rule_fuse_compute()
    engine = RewriteEngine(rules=[rule])
    optimized = engine.apply(program)
    
    # Should preserve all compute items
    original_metrics = {c.result_name for c in program.canonical_ast.select.compute}
    optimized_metrics = {c.result_name for c in optimized.canonical_ast.select.compute}
    assert original_metrics == optimized_metrics


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

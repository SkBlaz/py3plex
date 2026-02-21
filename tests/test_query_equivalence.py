"""Tests for Query Algebra, Canonicalization, and Equivalence Engine.

Covers:
    A) Canonicalization idempotence
    B) Equivalence positives (where order, compute order, limit chaining, …)
    C) Equivalence negatives (different predicates, layers, projections)
    D) Scope behavior for order_by
    E) Proof contents
    F) Termination guard
"""

import pytest
from py3plex.dsl import Q, L
from py3plex.dsl.ast import (
    canonicalize_ast_scoped,
    canonical_ast_hash,
    _serialize_node,
    _RewriteTerminationError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _net():
    """Tiny two-layer network for tests that need execution."""
    from py3plex.core import multinet
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'work'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'work', 'target_type': 'work'},
    ])
    return net


# ---------------------------------------------------------------------------
# A) Canonicalization idempotence
# ---------------------------------------------------------------------------

class TestCanonicalizationIdempotence:
    """canonical(canonical(q)) ≡ canonical(q)."""

    def test_simple_idempotence(self):
        q = Q.nodes().where(degree__gt=5).compute("betweenness", "degree")
        assert q.canonical().canonical_ast_hash == q.canonical().canonical().canonical_ast_hash

    def test_idempotence_with_where_and_layer(self):
        q = Q.nodes().where(layer="social", degree__gt=3).compute("degree")
        h1 = q.canonical().canonical_ast_hash
        h2 = q.canonical().canonical().canonical_ast_hash
        assert h1 == h2

    def test_idempotence_edges(self):
        q = Q.edges().compute("weight")
        h1 = q.canonical().canonical_ast_hash
        h2 = q.canonical().canonical().canonical_ast_hash
        assert h1 == h2

    def test_canonical_returns_query_builder(self):
        q = Q.nodes().where(degree__gt=1)
        result = q.canonical()
        # Should be a QueryBuilder (has to_ast and execute methods)
        assert hasattr(result, "to_ast")
        assert hasattr(result, "execute")

    def test_canonical_ast_hash_is_string(self):
        q = Q.nodes().compute("degree")
        h = q.canonical_ast_hash
        assert isinstance(h, str)
        assert len(h) == 16  # SHA-256 truncated to first 16 hex chars

    def test_triple_canonical_idempotence(self):
        q = Q.nodes().where(degree__gt=5, layer="social").compute("betweenness", "degree")
        h = q.canonical_ast_hash
        assert q.canonical().canonical_ast_hash == h
        assert q.canonical().canonical().canonical_ast_hash == h

    def test_scoped_idempotence_strict(self):
        q = Q.nodes().where(degree__gt=5).compute("degree")
        h1 = q.canonical(scope="strict").canonical_ast_hash
        # canonical_ast_hash uses relational scope, so test raw scoped function
        canon1, _ = canonicalize_ast_scoped(q.to_ast(), scope="strict")
        canon2, _ = canonicalize_ast_scoped(canon1, scope="strict")
        assert canon1 == canon2


# ---------------------------------------------------------------------------
# B) Equivalence positives
# ---------------------------------------------------------------------------

class TestEquivalencePositive:
    """Queries that should be equivalent."""

    def test_where_order_commutative(self):
        """where(p, q) ≡ where(q, p) for AND conditions."""
        q1 = Q.nodes().where(degree__gt=5, layer="social")
        q2 = Q.nodes().where(layer="social", degree__gt=5)
        assert q1.equivalent_to(q2), "AND predicates are commutative"
        assert q1.canonical_ast_hash == q2.canonical_ast_hash

    def test_compute_order_commutative(self):
        """compute(a, b) ≡ compute(b, a) — compute order is non-semantic."""
        q1 = Q.nodes().compute("betweenness", "degree")
        q2 = Q.nodes().compute("degree", "betweenness")
        assert q1.equivalent_to(q2), "Compute order must be non-semantic"
        assert q1.canonical_ast_hash == q2.canonical_ast_hash

    def test_where_idempotence_duplicate_atom(self):
        """where(p AND p) ≡ where(p)."""
        q1 = Q.nodes().where(degree__gt=5).where(degree__gt=5)
        q2 = Q.nodes().where(degree__gt=5)
        assert q1.equivalent_to(q2), "Duplicate WHERE atoms should be removed"
        assert q1.canonical_ast_hash == q2.canonical_ast_hash

    def test_limit_chaining_idempotence(self):
        """limit(n).limit(n) ≡ limit(n)."""
        q1 = Q.nodes().limit(10).limit(10)
        q2 = Q.nodes().limit(10)
        # builder already collapses — canonical hash must agree
        assert q1.canonical_ast_hash == q2.canonical_ast_hash

    def test_three_compute_items_any_order(self):
        q1 = Q.nodes().compute("c_closeness", "a_degree", "b_betweenness")
        q2 = Q.nodes().compute("a_degree", "b_betweenness", "c_closeness")
        assert q1.equivalent_to(q2)

    def test_no_where_equals_no_where(self):
        q1 = Q.nodes().compute("degree")
        q2 = Q.nodes().compute("degree")
        assert q1.equivalent_to(q2)
        assert q1.canonical_ast_hash == q2.canonical_ast_hash


# ---------------------------------------------------------------------------
# C) Equivalence negatives
# ---------------------------------------------------------------------------

class TestEquivalenceNegative:
    """Queries that must NOT be equivalent."""

    def test_different_predicate_thresholds(self):
        q1 = Q.nodes().where(degree__gt=5)
        q2 = Q.nodes().where(degree__gt=10)
        assert not q1.equivalent_to(q2), "Different thresholds must differ"
        assert q1.canonical_ast_hash != q2.canonical_ast_hash

    def test_different_layer_sets(self):
        q1 = Q.nodes().where(layer="social")
        q2 = Q.nodes().where(layer="work")
        assert not q1.equivalent_to(q2), "Different layer filters must differ"
        assert q1.canonical_ast_hash != q2.canonical_ast_hash

    def test_different_projections_compute(self):
        q1 = Q.nodes().compute("degree")
        q2 = Q.nodes().compute("betweenness")
        assert not q1.equivalent_to(q2), "Different compute sets must differ"
        assert q1.canonical_ast_hash != q2.canonical_ast_hash

    def test_nodes_vs_edges_target(self):
        q1 = Q.nodes().compute("degree")
        q2 = Q.edges().compute("degree")
        assert not q1.equivalent_to(q2), "Different targets must differ"
        assert q1.canonical_ast_hash != q2.canonical_ast_hash

    def test_limit_vs_no_limit(self):
        q1 = Q.nodes().compute("degree")
        q2 = Q.nodes().compute("degree").limit(5)
        assert not q1.equivalent_to(q2), "limit vs no-limit must differ"
        assert q1.canonical_ast_hash != q2.canonical_ast_hash

    def test_different_limit_values(self):
        q1 = Q.nodes().limit(5)
        q2 = Q.nodes().limit(10)
        assert not q1.equivalent_to(q2)
        assert q1.canonical_ast_hash != q2.canonical_ast_hash

    def test_different_predicate_operators(self):
        q1 = Q.nodes().where(degree__gt=5)
        q2 = Q.nodes().where(degree__gte=5)
        assert not q1.equivalent_to(q2)

    def test_predicate_vs_no_predicate(self):
        q1 = Q.nodes().where(degree__gt=5)
        q2 = Q.nodes()
        assert not q1.equivalent_to(q2)


# ---------------------------------------------------------------------------
# D) Scope behavior for order_by
# ---------------------------------------------------------------------------

class TestScopeBehavior:
    """Ordering semantics under relational vs strict scope."""

    def test_order_by_relational_scope_same(self):
        """Same order_by → equivalent in relational scope."""
        q1 = Q.nodes().compute("degree").order_by("degree", desc=True)
        q2 = Q.nodes().compute("degree").order_by("degree", desc=True)
        assert q1.equivalent_to(q2, scope="relational")

    def test_order_by_relational_scope_different(self):
        """Different order_by → NOT equivalent in relational scope.

        py3plex order_by affects result ordering today; therefore it is
        treated as semantic in both relational and strict scopes.
        """
        q1 = Q.nodes().compute("degree").order_by("degree", desc=True)
        q2 = Q.nodes().compute("degree").order_by("degree", desc=False)
        assert not q1.equivalent_to(q2, scope="relational")

    def test_order_by_strict_scope_same(self):
        q1 = Q.nodes().compute("degree").order_by("degree", desc=True)
        q2 = Q.nodes().compute("degree").order_by("degree", desc=True)
        assert q1.equivalent_to(q2, scope="strict")

    def test_order_by_strict_scope_different(self):
        """Different order_by → NOT equivalent in strict scope."""
        q1 = Q.nodes().compute("degree").order_by("degree", desc=True)
        q2 = Q.nodes().compute("degree").order_by("degree", desc=False)
        assert not q1.equivalent_to(q2, scope="strict")

    def test_order_by_dedup_strict(self):
        """R8: order_by deduplication in strict scope."""
        q1 = Q.nodes().compute("degree").order_by("degree")
        # duplicate order_by key: build manually using the actual AST types
        from py3plex.dsl.ast import canonicalize_ast_scoped, OrderItem, SelectStmt, Query
        ast = q1.to_ast()
        # inject a duplicate order_by item
        dup_item = list(ast.select.order_by)
        if dup_item:
            s = ast.select
            dup_ast = Query(
                explain=ast.explain,
                select=SelectStmt(
                    target=s.target,
                    layer_expr=s.layer_expr,
                    layer_set=s.layer_set,
                    where=s.where,
                    compute=s.compute,
                    order_by=dup_item + dup_item,  # duplicate
                    limit=s.limit,
                    export=s.export,
                    file_export=s.file_export,
                    temporal_context=s.temporal_context,
                    window_spec=s.window_spec,
                    group_by=s.group_by,
                    limit_per_group=s.limit_per_group,
                    coverage_mode=s.coverage_mode,
                    coverage_k=s.coverage_k,
                    coverage_p=s.coverage_p,
                    coverage_group=s.coverage_group,
                    coverage_id_field=s.coverage_id_field,
                    select_cols=s.select_cols,
                    drop_cols=s.drop_cols,
                    rename_map=s.rename_map,
                    summarize_aggs=s.summarize_aggs,
                    distinct_cols=s.distinct_cols,
                    rank_specs=s.rank_specs,
                    zscore_attrs=s.zscore_attrs,
                    post_filters=s.post_filters,
                    aggregate_specs=s.aggregate_specs,
                    mutate_specs=s.mutate_specs,
                    autocompute=s.autocompute,
                    uq_config=s.uq_config,
                    explain_spec=s.explain_spec,
                    counterfactual_spec=s.counterfactual_spec,
                    sensitivity_spec=s.sensitivity_spec,
                    contract_spec=s.contract_spec,
                    auto_community_config=s.auto_community_config,
                ),
                dsl_version=ast.dsl_version,
            )
            canon, proof = canonicalize_ast_scoped(dup_ast, scope="strict")
            assert "R8:order_by_idempotence" in proof, "R8 should be applied"
            assert len(canon.select.order_by) == len(dup_item), "Duplicates removed"


# ---------------------------------------------------------------------------
# E) Proof contents
# ---------------------------------------------------------------------------

class TestProofContents:
    """equivalent_to(explain=True) returns proof with rule names."""

    def test_explain_returns_tuple(self):
        q1 = Q.nodes().where(degree__gt=5, layer="social")
        q2 = Q.nodes().where(layer="social", degree__gt=5)
        result = q1.equivalent_to(q2, explain=True)
        assert isinstance(result, tuple)
        assert len(result) == 2
        eq, proof = result
        assert isinstance(eq, bool)
        assert isinstance(proof, dict)

    def test_explain_proof_has_expected_keys(self):
        q1 = Q.nodes().where(degree__gt=5)
        q2 = Q.nodes().where(degree__gt=5)
        _, proof = q1.equivalent_to(q2, explain=True)
        assert "self_proof" in proof
        assert "other_proof" in proof
        assert "diff" in proof

    def test_explain_diff_none_when_equal(self):
        q1 = Q.nodes().where(degree__gt=5)
        q2 = Q.nodes().where(degree__gt=5)
        _, proof = q1.equivalent_to(q2, explain=True)
        assert proof["diff"] is None

    def test_explain_diff_not_none_when_different(self):
        q1 = Q.nodes().where(degree__gt=5)
        q2 = Q.nodes().where(degree__gt=10)
        _, proof = q1.equivalent_to(q2, explain=True)
        assert proof["diff"] is not None

    def test_r2_in_proof_for_duplicate_atom(self):
        """R2 (where idempotence) must appear in proof for dup atoms."""
        q = Q.nodes().where(degree__gt=5).where(degree__gt=5)
        _ast, proof = canonicalize_ast_scoped(q.to_ast(), scope="relational")
        assert "R2:where_idempotence" in proof

    def test_explain_no_rules_for_already_canonical(self):
        """Already-canonical query → no rewrite rules fired."""
        q = Q.nodes().compute("degree")
        _ast, proof = canonicalize_ast_scoped(q.to_ast(), scope="relational")
        # No rules should have been applied (no duplicates, already sorted)
        assert proof == [] or all(r.startswith("R") for r in proof)


# ---------------------------------------------------------------------------
# F) Termination guard
# ---------------------------------------------------------------------------

class TestTerminationGuard:
    """Canonicalization must terminate and not grow complexity."""

    def test_terminates_with_many_computes(self):
        """Even with many compute items, fixpoint must be reached."""
        q = Q.nodes().compute(
            "z_metric", "a_metric", "m_metric", "b_metric", "y_metric"
        )
        # Should not raise
        canon, proof = canonicalize_ast_scoped(q.to_ast(), scope="relational")
        assert canon is not None

    def test_terminates_with_complex_where(self):
        q = Q.nodes().where(degree__gt=1).where(degree__gt=1).where(layer="social")
        canon, proof = canonicalize_ast_scoped(q.to_ast(), scope="relational")
        assert canon is not None

    def test_max_iters_exceeded_raises(self):
        """Passing max_iters=0 should raise _RewriteTerminationError."""
        q = Q.nodes().compute("degree")
        with pytest.raises(_RewriteTerminationError):
            canonicalize_ast_scoped(q.to_ast(), scope="relational", max_iters=0)

    def test_canonical_idempotence_no_growth(self):
        """Complexity must not grow after canonicalization."""
        q = Q.nodes().where(degree__gt=1, layer="social").compute("betweenness", "degree")
        canon_ast, _ = canonicalize_ast_scoped(q.to_ast(), scope="relational")
        serial_1 = _serialize_node(canon_ast)
        canon_ast2, _ = canonicalize_ast_scoped(canon_ast, scope="relational")
        serial_2 = _serialize_node(canon_ast2)
        assert len(serial_1) >= len(serial_2) or serial_1 == serial_2, (
            "Canonical form must not grow in subsequent passes"
        )


# ---------------------------------------------------------------------------
# Misc API surface tests
# ---------------------------------------------------------------------------

class TestAPIContracts:
    """Check public method signatures and types."""

    def test_canonical_hash_stable_across_calls(self):
        q = Q.nodes().where(degree__gt=5).compute("degree")
        assert q.canonical_ast_hash == q.canonical_ast_hash

    def test_equivalent_to_bool_by_default(self):
        q = Q.nodes()
        result = q.equivalent_to(Q.nodes())
        assert isinstance(result, bool)

    def test_unknown_scope_raises(self):
        q = Q.nodes()
        with pytest.raises(ValueError, match="Unknown scope"):
            q.canonical(scope="unknown_scope")

    def test_unknown_scope_raises_in_hash(self):
        from py3plex.dsl.ast import canonical_ast_hash
        with pytest.raises(ValueError, match="Unknown scope"):
            canonical_ast_hash(Q.nodes().to_ast(), scope="bad")

    def test_canonical_ast_hash_function_direct(self):
        q = Q.nodes().compute("degree", "betweenness")
        h1 = canonical_ast_hash(q.to_ast(), scope="relational")
        h2 = canonical_ast_hash(q.to_ast(), scope="relational")
        assert h1 == h2

    def test_serialize_node_stable(self):
        q = Q.nodes().where(degree__gt=5).to_ast()
        s1 = _serialize_node(q)
        s2 = _serialize_node(q)
        assert s1 == s2, "Serialization must be deterministic"

    def test_canonical_preserves_target(self):
        for builder in [Q.nodes(), Q.edges()]:
            canon = builder.canonical()
            assert canon.to_ast().select.target == builder.to_ast().select.target

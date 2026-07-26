from types import SimpleNamespace

from py3plex.optimizer.cost_model import CostEstimate, CostModel, NetworkStats
from py3plex.optimizer.logical_plan import (
    LogicalPlanBuilder,
    _get_condition_list,
    _get_layer_list,
)
from py3plex.optimizer.optimizer import Optimizer, optimize_query
from py3plex.optimizer.physical_plan import (
    PhysicalLayerPushdown,
    PhysicalLimitEarly,
    PhysicalPlan,
    PhysicalPlanBuilder,
    PhysicalTopKHeap,
)
from py3plex.optimizer.plan_nodes import (
    LogicalAggregate,
    LogicalCompute,
    LogicalFilter,
    LogicalGroupByLayer,
    LogicalLayerFilter,
    LogicalLimit,
    LogicalNullModel,
    LogicalOrderBy,
    LogicalProject,
    LogicalScanEdges,
    LogicalScanNodes,
    LogicalTopK,
    LogicalUQ,
)
from py3plex.optimizer.rules import (
    CombineAdjacentFilters,
    ConvertAggregateToHashIfSmallGroups,
    ConvertOrderByLimitToTopK,
    EarlyLimitPushdown,
    MergeMultipleComputesIntoSinglePass,
    PushFilterBelowCompute,
    PushLayerFilterBelowCompute,
    ReorderFiltersBySelectivity,
    RemoveRedundantProject,
    RuleEngine,
    ShortCircuitEmptyLayer,
)


class _MockLayerExprPublic:
    def __init__(self, names):
        self.names = names


class _MockLayerExprPrivate:
    def __init__(self, names):
        self._names = names


class _MockNetwork:
    def __init__(self):
        self.layers = ["a", "b"]
        self._nodes = [("n1", "a"), ("n2", "a"), ("n1", "b")]
        self._edges = [
            ("n1", "n2", "a", "a"),
            ("n1", "n1", "a", "b"),
        ]

    def get_nodes(self):
        return self._nodes

    def get_edges(self):
        return self._edges


def _first_child_chain(root):
    """Return node type names by following only the first-child pointer chain."""
    out = []
    cur = root
    while cur is not None:
        out.append(type(cur).__name__)
        cur = cur.children[0] if getattr(cur, "children", None) else None
    return out


def test_logical_helpers_for_conditions_and_layers():
    s1 = SimpleNamespace(where_clause=None, layer_expr=None)
    assert _get_condition_list(s1) == []
    assert _get_layer_list(s1) == []

    s2 = SimpleNamespace(where_clause={"a": 1}, layer_expr=_MockLayerExprPublic(["x", "y"]))
    assert _get_condition_list(s2) == [{"a": 1}]
    assert _get_layer_list(s2) == ["x", "y"]

    s3 = SimpleNamespace(
        where_clause=[{"a": 1}, {"b": 2}],
        layer_expr=_MockLayerExprPrivate(("k", "m")),
    )
    assert _get_condition_list(s3) == [{"a": 1}, {"b": 2}]
    assert _get_layer_list(s3) == ["k", "m"]


def test_logical_plan_builder_fallback_without_select():
    ast = SimpleNamespace(select=None)
    root = LogicalPlanBuilder(ast).build()
    assert isinstance(root, LogicalScanNodes)


def test_logical_plan_builder_builds_expected_chain():
    select = SimpleNamespace(
        target="nodes",
        layer_expr=_MockLayerExprPublic(["social"]),
        where_clause=[{"field": "degree", "op": ">", "value": 2}],
        compute_spec=["degree", "pagerank"],
        group_mode="per_layer",
        aggregate_spec={"avg_degree": "mean(degree)"},
        coverage_spec={"mode": "k", "k": 2},
        order_spec=["degree"],
        order_desc=True,
        limit=5,
        uq_spec={"method": "bootstrap", "n_samples": 5},
        null_model_spec={"method": "configuration"},
        select_columns=["node", "degree"],
    )
    ast = SimpleNamespace(select=select)
    root = LogicalPlanBuilder(ast).build()
    chain = _first_child_chain(root)
    assert chain[:6] == [
        "LogicalProject",
        "LogicalNullModel",
        "LogicalUQ",
        "LogicalLimit",
        "LogicalOrderBy",
        "LogicalCoverage",
    ]


def test_network_stats_from_network_and_fallback():
    stats = NetworkStats.from_network(_MockNetwork())
    assert stats.node_count == 3
    assert stats.edge_count == 2
    assert stats.layer_count == 2
    assert stats.avg_degree > 0
    assert stats.density >= 0

    class _BrokenNet:
        def get_nodes(self):
            raise RuntimeError("boom")

    fallback = NetworkStats.from_network(_BrokenNet())
    assert fallback.node_count == 0
    assert fallback.edge_count == 0


def test_cost_estimate_add_and_tree_cost():
    c1 = CostEstimate(cpu_cost=1.0, total_cost=2.0, estimated_rows=10)
    c2 = CostEstimate(memory_cost=2.0, total_cost=3.0, estimated_rows=7)
    c3 = c1 + c2
    assert c3.cpu_cost == 1.0
    assert c3.memory_cost == 2.0
    assert c3.total_cost == 5.0
    assert c3.estimated_rows == 10

    root = LogicalFilter(children=[LogicalScanNodes()], conditions=[{"field": "degree"}])
    root.children[0].estimated_rows = 100
    cm = CostModel(NetworkStats(node_count=100, edge_count=200, layer_count=3))
    total = cm.total_tree_cost(root)
    assert total > 0


def test_cost_model_estimates_cover_key_operator_types():
    stats = NetworkStats(node_count=1000, edge_count=5000, layer_count=5)
    cm = CostModel(stats)

    scan_nodes = cm.estimate(LogicalScanNodes())
    scan_edges = cm.estimate(LogicalScanEdges())
    assert scan_nodes.estimated_rows == 1000
    assert scan_edges.estimated_rows == 5000

    layer_filter = LogicalLayerFilter(
        children=[LogicalScanNodes(estimated_rows=1000)], layers=["a", "b"]
    )
    lf_est = cm.estimate(layer_filter)
    assert 0 < lf_est.estimated_rows <= 1000

    filt = LogicalFilter(
        children=[LogicalScanNodes(estimated_rows=1000)],
        conditions=[{"field": "degree", "op": ">", "value": 3}],
    )
    f_est = cm.estimate(filt)
    assert f_est.estimated_rows <= 1000

    comp = LogicalCompute(
        children=[LogicalScanNodes(estimated_rows=1000)],
        measures=["betweenness_centrality", "degree"],
    )
    comp_est = cm.estimate(comp)
    assert comp_est.total_cost > 0

    order = LogicalOrderBy(children=[LogicalScanNodes(estimated_rows=100)], keys=["degree"])
    ord_est = cm.estimate(order)
    assert ord_est.total_cost > 0

    uq = LogicalUQ(children=[LogicalScanNodes(estimated_rows=100)], uq_spec={"n_samples": 11})
    uq_est = cm.estimate(uq)
    assert uq_est.total_cost > 0

    nm = LogicalNullModel(children=[LogicalScanNodes(estimated_rows=100)], null_model_spec={})
    nm_est = cm.estimate(nm)
    assert nm_est.total_cost > 0


def test_physical_layer_pushdown_topk_limit_and_plan_to_dict():
    net = _MockNetwork()
    pushed = PhysicalLayerPushdown(layers=["a"]).execute({"network": net})
    assert pushed == [("n1", "a"), ("n2", "a")]

    items = ["a", "b", "c"]
    # Mix scalar and UQ-style dict values to exercise both supported key formats.
    attrs = {"score": {"a": 1.0, "b": {"mean": 5.0}, "c": 2.0}}
    top_desc = PhysicalTopKHeap(k=2, key="score", desc=True).execute(
        {"items": items, "attributes": attrs}
    )
    top_asc = PhysicalTopKHeap(k=2, key="score", desc=False).execute(
        {"items": items, "attributes": attrs}
    )
    assert top_desc[0] == "b"
    assert len(top_asc) == 2

    assert PhysicalLimitEarly(n=2).execute({"items": [1, 2, 3]}) == [1, 2]
    # n=0 is treated as "no truncation" in the operator implementation.
    assert PhysicalLimitEarly(n=0).execute({"items": [1, 2, 3]}) == [1, 2, 3]

    plan = PhysicalPlan(root=PhysicalLimitEarly(n=1), estimated_cost=1.2, plan_hash="abc")
    p = plan.to_dict()
    assert p["plan_hash"] == "abc"
    assert p["tree"]["type"] == "PhysicalLimitEarly"


def test_physical_plan_builder_operator_selection_paths():
    builder = PhysicalPlanBuilder()

    lf = LogicalFilter(
        children=[LogicalScanNodes()],
        conditions=[{"field": "degree", "op": ">", "value": 1}],
    )
    p1 = builder.build(lf)
    assert p1.root.__class__.__name__ == "PhysicalFilterVectorized"

    lf2 = LogicalFilter(children=[LogicalScanNodes()], conditions=["degree > x"])
    p2 = builder.build(lf2)
    assert p2.root.__class__.__name__ == "PhysicalFilterPython"

    agg_small = LogicalAggregate(children=[LogicalScanNodes()], aggregations={"x": "count()"})
    agg_small.estimated_rows = 5
    p3 = builder.build(agg_small)
    assert p3.root.__class__.__name__ == "PhysicalAggregateHash"

    agg_big = LogicalAggregate(children=[LogicalScanNodes()], aggregations={"x": "count()"})
    agg_big.estimated_rows = 50000
    p4 = builder.build(agg_big)
    assert p4.root.__class__.__name__ == "PhysicalAggregateSort"
    assert len(p4.plan_hash) == 16


def test_push_layer_filter_below_compute_rule():
    plan = LogicalCompute(
        measures=["degree"],
        children=[LogicalLayerFilter(layers=["x"], children=[LogicalScanNodes()])],
    )
    rule = PushLayerFilterBelowCompute()
    assert rule.match(plan) is True
    rewritten = rule.apply(plan)
    assert type(rewritten).__name__ == "LogicalLayerFilter"
    assert type(rewritten.children[0]).__name__ == "LogicalCompute"


def test_push_filter_below_compute_respects_condition_references():
    rule = PushFilterBelowCompute()

    safe = LogicalCompute(
        measures=["degree"],
        children=[
            LogicalFilter(
                children=[LogicalScanNodes()],
                conditions=[{"field": "layer", "op": "==", "value": "social"}],
            )
        ],
    )
    assert rule.match(safe) is True

    unsafe = LogicalCompute(
        measures=["degree"],
        children=[
            LogicalFilter(
                children=[LogicalScanNodes()],
                conditions=[{"field": "degree", "op": ">", "value": 2}],
            )
        ],
    )
    assert rule.match(unsafe) is False


def test_combine_adjacent_filters_merges_conditions_inner_then_outer():
    inner = LogicalFilter(
        children=[LogicalScanNodes()],
        conditions=[{"field": "layer", "op": "==", "value": "social"}],
    )
    outer = LogicalFilter(
        children=[inner],
        conditions=[{"field": "degree", "op": ">", "value": 2}],
    )

    rule = CombineAdjacentFilters()
    assert rule.match(outer) is True

    merged = rule.apply(outer)
    assert merged.children == inner.children
    assert merged.conditions == inner.conditions + outer.conditions


def test_reorder_filters_by_selectivity_sorts_conditions():
    plan = LogicalFilter(
        children=[LogicalScanNodes()],
        conditions=[
            {"field": "degree", "op": ">", "value": 2},
            {"field": "name", "op": "=", "value": "Alice"},
            {"field": "layer", "op": "==", "value": "social"},
        ],
    )

    rule = ReorderFiltersBySelectivity()
    assert rule.match(plan) is True

    reordered = rule.apply(plan)
    assert reordered.conditions[0]["field"] == "layer"
    assert reordered.conditions[1]["field"] == "name"
    assert reordered.conditions[2]["field"] == "degree"


def test_rewrite_rules_for_topk_project_limit_and_empty_layer():
    order_limit = LogicalOrderBy(
        keys=["degree"], desc=True, children=[LogicalLimit(n=10, children=[LogicalScanNodes()])]
    )
    converted = ConvertOrderByLimitToTopK().apply(order_limit)
    assert isinstance(converted, LogicalTopK)
    assert converted.k == 10

    projected = LogicalProject(columns=[], children=[LogicalScanNodes()])
    removed = RemoveRedundantProject().apply(projected)
    assert isinstance(removed, LogicalScanNodes)

    root = LogicalLimit(n=4, children=[LogicalFilter(children=[LogicalScanNodes()])])
    pushed = EarlyLimitPushdown().apply(root)
    assert isinstance(pushed.children[0].children[0], LogicalLimit)

    agg = LogicalAggregate(estimated_rows=10, children=[LogicalScanNodes()])
    out = ConvertAggregateToHashIfSmallGroups().apply(agg)
    assert getattr(out, "use_hash", False) is True

    empty_layer = LogicalLayerFilter(layers=[], children=[LogicalScanNodes()])
    assert ShortCircuitEmptyLayer().match(empty_layer) is True
    assert type(ShortCircuitEmptyLayer().apply(empty_layer)).__name__ == "LogicalEmptyScan"


def test_merge_compute_rule_and_rule_engine_rewrite():
    nested = LogicalCompute(
        measures=["pagerank"],
        children=[LogicalCompute(measures=["degree"], children=[LogicalScanNodes()])],
    )
    merged = MergeMultipleComputesIntoSinglePass().apply(nested)
    assert merged.measures == ["pagerank", "degree"]
    assert isinstance(merged.children[0], LogicalScanNodes)

    # RuleEngine should walk and rewrite children too.
    root = LogicalGroupByLayer(children=[nested])
    rewritten, applied = RuleEngine(max_iter=2).rewrite(root)
    assert isinstance(rewritten, LogicalGroupByLayer)
    assert isinstance(rewritten.children[0], LogicalCompute)
    assert "MergeMultipleComputesIntoSinglePass" in applied


def test_optimizer_optimize_and_optimize_query_end_to_end():
    # Build logical plan directly and optimize.
    logical = LogicalLimit(n=3, children=[LogicalScanNodes()])
    opt = Optimizer(enable_rule_based=False)
    plan, metadata = opt.optimize(logical, NetworkStats(node_count=9, edge_count=11, layer_count=2))
    assert len(plan.plan_hash) == 16
    assert metadata["enabled"] is True
    assert metadata["backend"] == "networkx"
    assert "optimizer_time_ms" in metadata

    # One-shot optimize_query from a tiny AST-like object.
    ast = SimpleNamespace(select=SimpleNamespace(target="nodes"))
    physical, meta = optimize_query(ast, network=_MockNetwork(), enable_rule_based=False)
    assert physical.backend == "networkx"
    assert isinstance(meta["rules_applied"], list)
    assert meta["enabled"] is True

import pytest

from py3plex.dsl import Q
from py3plex.dsl.errors import DslExecutionError
from py3plex.optimizer.plan_nodes import (
    LogicalCompute,
    LogicalFilter,
    LogicalLayerFilter,
    LogicalLimit,
    LogicalOp,
    LogicalOrderBy,
    LogicalScanNodes,
)
from py3plex.optimizer.rules import (
    CollapseNestedLimits,
    CombineAdjacentFilters,
    ConstantPredicateSimplification,
    DeduplicateComputations,
    OptimizationRule,
    PruneNestedLayerFilters,
    RuleEngine,
    plan_fingerprint,
)


def _evaluate(plan, rows):
    if isinstance(plan, LogicalScanNodes):
        return list(rows)
    if len(plan.children) != 1:
        raise AssertionError("test evaluator expects unary plans")
    result = _evaluate(plan.children[0], rows)
    if isinstance(plan, LogicalLayerFilter):
        return [row for row in result if row["layer"] in plan.layers]
    if isinstance(plan, LogicalFilter):
        for condition in plan.conditions:
            field, op, value = (
                condition["field"],
                condition["op"],
                condition["value"],
            )
            comparisons = {
                ">": lambda left: left > value,
                "==": lambda left: left == value,
            }
            result = [row for row in result if comparisons[op](row[field])]
        return result
    if isinstance(plan, LogicalCompute):
        return result
    if isinstance(plan, LogicalOrderBy):
        return sorted(result, key=lambda row: row[plan.keys[0]], reverse=plan.desc)
    if isinstance(plan, LogicalLimit):
        return result[: plan.n] if plan.n > 0 else []
    raise AssertionError(f"unsupported test operator {type(plan).__name__}")


def _compound_plan():
    return LogicalLimit(
        n=3,
        children=[
            LogicalOrderBy(
                keys=["degree"],
                desc=True,
                children=[
                    LogicalCompute(
                        measures=["degree", "degree"],
                        computation_signatures=[
                            '{"name": "degree"}',
                            '{"name": "degree"}',
                        ],
                        children=[
                            LogicalFilter(
                                conditions=[{"field": "degree", "op": ">", "value": 1}],
                                children=[
                                    LogicalFilter(
                                        conditions=[
                                            {"field": "degree", "op": "==", "value": 2}
                                        ],
                                        children=[
                                            LogicalLayerFilter(
                                                layers=["social"],
                                                children=[
                                                    LogicalLayerFilter(
                                                        layers=["social", "work"],
                                                        children=[LogicalScanNodes()],
                                                    )
                                                ],
                                            )
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [{"id": "a", "layer": "social", "degree": 2}],
        [
            {"id": "a", "layer": "social", "degree": 2},
            {"id": "b", "layer": "work", "degree": 3},
            {"id": "c", "layer": "social", "degree": 5},
            {"id": "d", "layer": "social", "degree": 1},
        ],
    ],
)
def test_compound_rewrites_preserve_plan_results(rows):
    plan = _compound_plan()
    result = RuleEngine().optimize(plan)

    assert _evaluate(plan, rows) == _evaluate(result.optimized_plan, rows)
    assert {"R001", "R004", "R006"}.issubset(result.trace.rules_applied)


def test_filter_fusion_preserves_inner_then_outer_predicate_order():
    plan = LogicalFilter(
        conditions=[{"field": "degree", "op": ">", "value": 1}],
        children=[
            LogicalFilter(
                conditions=[{"field": "degree", "op": "==", "value": 2}],
                children=[LogicalScanNodes()],
            )
        ],
    )

    optimized = RuleEngine(rules=[CombineAdjacentFilters()]).optimize(plan)
    assert optimized.optimized_plan.conditions == [
        {"field": "degree", "op": "==", "value": 2},
        {"field": "degree", "op": ">", "value": 1},
    ]
    assert _evaluate(plan, [{"degree": 2}, {"degree": 3}]) == _evaluate(
        optimized.optimized_plan, [{"degree": 2}, {"degree": 3}]
    )


def test_constant_predicate_simplification_and_layer_intersection():
    plan = LogicalFilter(
        conditions=[True],
        children=[
            LogicalLayerFilter(
                layers=["b", "a"],
                children=[
                    LogicalLayerFilter(
                        layers=["a", "b", "c"],
                        children=[LogicalScanNodes()],
                    )
                ],
            )
        ],
    )
    rewritten = RuleEngine(
        rules=[ConstantPredicateSimplification(), PruneNestedLayerFilters()]
    ).optimize(plan)

    assert rewritten.optimized_plan.conditions == []
    layer_filter = rewritten.optimized_plan.children[0]
    assert layer_filter.layers == ["a", "b"]


def test_compute_deduplication_is_conservative():
    deterministic = LogicalCompute(
        measures=["degree", "degree"],
        computation_signatures=['{"name":"degree"}', '{"name":"degree"}'],
    )
    result = RuleEngine(rules=[DeduplicateComputations()]).optimize(deterministic)
    assert result.optimized_plan.measures == ["degree"]

    stochastic = LogicalCompute(
        measures=["pagerank", "pagerank"],
        computation_signatures=['{"name":"pagerank"}', '{"name":"pagerank"}'],
    )
    result = RuleEngine(rules=[DeduplicateComputations()]).optimize(stochastic)
    assert result.optimized_plan.measures == ["pagerank", "pagerank"]


def test_nested_limit_collapse_and_semantic_equivalence():
    plan = LogicalLimit(n=2, children=[LogicalLimit(n=4, children=[LogicalScanNodes()])])
    optimized = RuleEngine(rules=[CollapseNestedLimits()]).optimize(plan)

    assert optimized.optimized_plan.n == 2
    rows = [{"id": i} for i in range(6)]
    assert _evaluate(plan, rows) == _evaluate(optimized.optimized_plan, rows)


def test_optimizer_fingerprints_are_stable_and_optimization_is_idempotent():
    plan = _compound_plan()
    first = RuleEngine().optimize(plan)
    second = RuleEngine().optimize(first.optimized_plan)

    assert first.trace.optimized_fingerprint == second.trace.optimized_fingerprint
    assert plan_fingerprint(first.optimized_plan) == plan_fingerprint(
        RuleEngine().optimize(plan).optimized_plan
    )
    assert first.trace.rules_applied == RuleEngine().optimize(plan).trace.rules_applied


def test_rule_engine_custom_subset_and_zero_rules():
    plan = _compound_plan()
    only_fusion = RuleEngine(rules=[CombineAdjacentFilters()]).optimize(plan)
    no_rules = RuleEngine(rules=[]).optimize(plan)

    assert only_fusion.trace.rules_applied == ["R001"]
    assert no_rules.trace.rules_applied == []
    assert no_rules.trace.passes == 1


def test_rule_engine_rejects_duplicate_ids_and_nonconvergence():
    class ToggleRule(OptimizationRule):
        id = "T001"
        name = "toggle"
        description = "Changes a structural marker on every pass."

        def match(self, plan):
            return isinstance(plan, LogicalScanNodes)

        def apply(self, plan):
            rewritten = LogicalScanNodes(schema=dict(plan.schema))
            rewritten.schema["toggle"] = not rewritten.schema.get("toggle", False)
            return rewritten

    with pytest.raises(DslExecutionError, match="Duplicate optimizer rule ID"):
        RuleEngine(rules=[ToggleRule(), ToggleRule()])
    with pytest.raises(DslExecutionError, match="cycle detected"):
        RuleEngine(rules=[ToggleRule()], max_iter=8).optimize(LogicalScanNodes())


def test_optimizer_rejects_malformed_plan_and_execute_can_disable_optimizer():
    malformed = LogicalOp(children=["not a plan"])
    with pytest.raises(DslExecutionError, match="Invalid children"):
        RuleEngine().optimize(malformed)

    from py3plex.core import multinet

    network = multinet.multi_layer_network(directed=False)
    network.add_edges(
        [
            {
                "source": "a",
                "target": "b",
                "source_type": "social",
                "target_type": "social",
            }
        ]
    )
    query = Q.nodes().compute("degree")
    baseline = query.execute(network, optimize=False, progress=False)
    optimized = query.execute(network, optimize=True, progress=False)

    assert baseline.items == optimized.items
    assert baseline.attributes == optimized.attributes
    assert baseline.meta["optimizer"]["enabled"] is False
    assert optimized.meta["optimizer"]["enabled"] is True

    explained = query.execute(network, explain_plan=True, progress=False)
    details = explained.explain_plan()
    assert details["original_logical_plan"]
    assert details["optimized_logical_plan"]
    assert isinstance(details["optimization_trace"]["events"], list)

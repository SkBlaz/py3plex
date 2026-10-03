"""Hypothesis checks for optimizer equivalence and determinism."""

import json
import operator

import pytest
from hypothesis import given, settings, strategies as st

from py3plex.optimizer.plan_nodes import (
    LogicalCompute,
    LogicalFilter,
    LogicalLayerFilter,
    LogicalLimit,
    LogicalScanNodes,
)
from py3plex.optimizer.rules import RuleEngine, plan_fingerprint


_LAYERS = ("social", "work", "hobby")
_COMPARISONS = {
    "==": operator.eq,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


def _build_plan(allowed_layers, lower_bound, lower_op, upper_bound, upper_op, limits):
    signatures = [json.dumps({"name": "degree"}, sort_keys=True)] * 2
    plan = LogicalScanNodes()
    plan = LogicalLayerFilter(layers=list(_LAYERS), children=[plan])
    plan = LogicalLayerFilter(layers=list(allowed_layers), children=[plan])
    plan = LogicalFilter(
        conditions=[
            {"field": "degree", "op": lower_op, "value": lower_bound}
        ],
        children=[plan],
    )
    plan = LogicalFilter(
        conditions=[
            {"field": "degree", "op": upper_op, "value": upper_bound}
        ],
        children=[plan],
    )
    plan = LogicalCompute(
        measures=["degree", "degree"],
        computation_signatures=signatures,
        children=[plan],
    )
    for limit in limits:
        plan = LogicalLimit(n=limit, children=[plan])
    return plan


def _evaluate(plan, rows):
    if isinstance(plan, LogicalScanNodes):
        return list(rows)

    result = _evaluate(plan.children[0], rows)
    if isinstance(plan, LogicalLayerFilter):
        return [row for row in result if row["layer"] in plan.layers]
    if isinstance(plan, LogicalFilter):
        for condition in plan.conditions:
            compare = _COMPARISONS[condition["op"]]
            result = [
                row
                for row in result
                if compare(row[condition["field"]], condition["value"])
            ]
        return result
    if isinstance(plan, LogicalCompute):
        return result
    if isinstance(plan, LogicalLimit):
        return result[: plan.n]
    raise AssertionError(f"unexpected plan node: {type(plan).__name__}")


@pytest.mark.property
@settings(max_examples=50, deadline=None, derandomize=True)
@given(
    rows=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=5),
            st.sampled_from(_LAYERS),
            st.integers(min_value=0, max_value=10),
        ),
        max_size=20,
    ),
    allowed_layers=st.lists(
        st.sampled_from(_LAYERS), min_size=1, max_size=len(_LAYERS), unique=True
    ),
    lower_bound=st.integers(min_value=0, max_value=10),
    lower_op=st.sampled_from(tuple(_COMPARISONS)),
    upper_bound=st.integers(min_value=0, max_value=10),
    upper_op=st.sampled_from(tuple(_COMPARISONS)),
    limits=st.lists(st.integers(min_value=0, max_value=20), min_size=2, max_size=3),
)
def test_generated_compound_rewrites_preserve_results_and_are_idempotent(
    rows,
    allowed_layers,
    lower_bound,
    lower_op,
    upper_bound,
    upper_op,
    limits,
):
    plan = _build_plan(
        allowed_layers, lower_bound, lower_op, upper_bound, upper_op, limits
    )
    network_rows = [
        {"id": node_id, "layer": layer, "degree": degree}
        for node_id, layer, degree in rows
    ]

    first_result = RuleEngine().optimize(plan)
    optimized = first_result.optimized_plan
    optimized_again = RuleEngine().optimize(optimized).optimized_plan

    assert _evaluate(plan, network_rows) == _evaluate(optimized, network_rows)
    assert {"R001", "R004", "R006", "R007"}.issubset(
        first_result.trace.rules_applied
    )
    assert plan_fingerprint(optimized) == plan_fingerprint(optimized_again)
    assert plan_fingerprint(optimized) == plan_fingerprint(
        RuleEngine().optimize(plan).optimized_plan
    )

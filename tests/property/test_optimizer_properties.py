#!/usr/bin/env python3
"""
Property-based tests for the optimizer.plan_nodes module.

Tests logical/physical plan node construction, default field values,
and basic structural invariants.
"""

import pytest
from hypothesis import given, settings, strategies as st

# Import optimizer plan nodes
try:
    from py3plex.optimizer.plan_nodes import (
        LogicalOp,
        LogicalScanNodes,
        LogicalScanEdges,
        LogicalFilter,
        LogicalLayerFilter,
        LogicalCompute,
        LogicalAggregate,
        LogicalGroupByLayer,
        LogicalGroupByLayerPair,
        LogicalCoverage,
        LogicalOrderBy,
        LogicalLimit,
        LogicalProject,
        LogicalTopK,
        LogicalEmptyScan,
        PhysicalOp,
        PhysicalNodeScanNX,
        PhysicalEdgeScanNX,
        PhysicalFilterPython,
        PhysicalFilterVectorized,
        PhysicalComputeNetworkX,
        PhysicalTopKHeap,
        PhysicalLimitEarly,
    )
    OPTIMIZER_AVAILABLE = True
except ImportError:
    OPTIMIZER_AVAILABLE = False
    pytest.skip("optimizer.plan_nodes not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_identifier = st.text(
    min_size=1, max_size=30,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
)
_identifier_list = st.lists(_identifier, min_size=0, max_size=5)
_pos_int = st.integers(min_value=0, max_value=1000)
_selectivity = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


# ---------------------------------------------------------------------------
# Base nodes – defaults
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_op_default_children_empty():
    """LogicalOp defaults to no children."""
    op = LogicalOp()
    assert op.children == []


@pytest.mark.property
def test_logical_op_default_schema_empty():
    """LogicalOp defaults to empty schema dict."""
    op = LogicalOp()
    assert op.schema == {}


@pytest.mark.property
def test_logical_op_estimated_rows_defaults_none():
    """LogicalOp.estimated_rows defaults to None."""
    op = LogicalOp()
    assert op.estimated_rows is None


@pytest.mark.property
def test_physical_op_default_costs_zero():
    """PhysicalOp defaults to zero estimated and actual cost."""
    op = PhysicalOp()
    assert op.estimated_cost == 0.0
    assert op.actual_cost == 0.0


# ---------------------------------------------------------------------------
# LogicalScanNodes / LogicalScanEdges
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_scan_nodes_is_logical_op():
    """LogicalScanNodes is a subclass of LogicalOp."""
    node = LogicalScanNodes()
    assert isinstance(node, LogicalOp)


@pytest.mark.property
def test_logical_scan_edges_is_logical_op():
    """LogicalScanEdges is a subclass of LogicalOp."""
    node = LogicalScanEdges()
    assert isinstance(node, LogicalOp)


# ---------------------------------------------------------------------------
# LogicalFilter
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_filter_default_conditions_empty():
    """LogicalFilter defaults to no conditions."""
    flt = LogicalFilter()
    assert flt.conditions == []


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(selectivity=_selectivity)
def test_logical_filter_selectivity_stored(selectivity):
    """LogicalFilter stores the provided selectivity."""
    flt = LogicalFilter(selectivity=selectivity)
    assert flt.selectivity == selectivity


# ---------------------------------------------------------------------------
# LogicalLayerFilter
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_layer_filter_default_layers_empty():
    """LogicalLayerFilter defaults to empty layers list."""
    flt = LogicalLayerFilter()
    assert flt.layers == []


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(layers=_identifier_list)
def test_logical_layer_filter_stores_layers(layers):
    """LogicalLayerFilter stores the provided layers list."""
    flt = LogicalLayerFilter(layers=layers)
    assert flt.layers == layers


# ---------------------------------------------------------------------------
# LogicalCompute
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_compute_default_measures_empty():
    """LogicalCompute defaults to no measures."""
    node = LogicalCompute()
    assert node.measures == []


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(measures=_identifier_list)
def test_logical_compute_stores_measures(measures):
    """LogicalCompute stores the provided measures list."""
    node = LogicalCompute(measures=measures)
    assert node.measures == measures


# ---------------------------------------------------------------------------
# LogicalAggregate
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_aggregate_defaults():
    """LogicalAggregate has empty aggregations and group_by by default."""
    agg = LogicalAggregate()
    assert agg.aggregations == {}
    assert agg.group_by == []


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(group_by=_identifier_list)
def test_logical_aggregate_stores_group_by(group_by):
    """LogicalAggregate stores the group_by list."""
    agg = LogicalAggregate(group_by=group_by)
    assert agg.group_by == group_by


# ---------------------------------------------------------------------------
# LogicalGroupByLayer / LogicalGroupByLayerPair
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_group_by_layer_is_logical_op():
    """LogicalGroupByLayer is a LogicalOp subclass."""
    node = LogicalGroupByLayer()
    assert isinstance(node, LogicalOp)


@pytest.mark.property
def test_logical_group_by_layer_pair_is_logical_op():
    """LogicalGroupByLayerPair is a LogicalOp subclass."""
    node = LogicalGroupByLayerPair()
    assert isinstance(node, LogicalOp)


# ---------------------------------------------------------------------------
# LogicalCoverage
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_coverage_default_mode_all():
    """LogicalCoverage defaults to mode='all'."""
    cov = LogicalCoverage()
    assert cov.mode == "all"


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(mode=st.sampled_from(["all", "any", "at_least", "fraction"]))
def test_logical_coverage_stores_mode(mode):
    """LogicalCoverage stores the provided mode."""
    cov = LogicalCoverage(mode=mode)
    assert cov.mode == mode


# ---------------------------------------------------------------------------
# LogicalOrderBy
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_order_by_defaults():
    """LogicalOrderBy defaults to empty keys and ascending order."""
    ob = LogicalOrderBy()
    assert ob.keys == []
    assert ob.desc is False


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(desc=st.booleans())
def test_logical_order_by_stores_desc(desc):
    """LogicalOrderBy stores the desc flag."""
    ob = LogicalOrderBy(desc=desc)
    assert ob.desc == desc


# ---------------------------------------------------------------------------
# LogicalLimit
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_limit_default_n_zero():
    """LogicalLimit defaults n to 0."""
    lim = LogicalLimit()
    assert lim.n == 0


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=_pos_int)
def test_logical_limit_stores_n(n):
    """LogicalLimit stores the provided n."""
    lim = LogicalLimit(n=n)
    assert lim.n == n


# ---------------------------------------------------------------------------
# LogicalTopK
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_topk_defaults():
    """LogicalTopK has sensible defaults."""
    topk = LogicalTopK()
    assert topk.k == 10
    assert topk.key == ""
    assert topk.desc is True


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(k=st.integers(min_value=1, max_value=500), key=_identifier)
def test_logical_topk_stores_k_and_key(k, key):
    """LogicalTopK stores k and key."""
    topk = LogicalTopK(k=k, key=key)
    assert topk.k == k
    assert topk.key == key


# ---------------------------------------------------------------------------
# LogicalProject
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_project_default_columns_empty():
    """LogicalProject defaults to no columns."""
    proj = LogicalProject()
    assert proj.columns == []


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(columns=_identifier_list)
def test_logical_project_stores_columns(columns):
    """LogicalProject stores the provided columns list."""
    proj = LogicalProject(columns=columns)
    assert proj.columns == columns


# ---------------------------------------------------------------------------
# LogicalEmptyScan
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_empty_scan_is_logical_op():
    """LogicalEmptyScan is a LogicalOp subclass."""
    node = LogicalEmptyScan()
    assert isinstance(node, LogicalOp)


# ---------------------------------------------------------------------------
# Physical nodes
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_physical_node_scan_is_physical_op():
    """PhysicalNodeScanNX is a PhysicalOp subclass."""
    node = PhysicalNodeScanNX()
    assert isinstance(node, PhysicalOp)


@pytest.mark.property
def test_physical_edge_scan_is_physical_op():
    """PhysicalEdgeScanNX is a PhysicalOp subclass."""
    node = PhysicalEdgeScanNX()
    assert isinstance(node, PhysicalOp)


@pytest.mark.property
def test_physical_filter_python_default_conditions_empty():
    """PhysicalFilterPython defaults to no conditions."""
    node = PhysicalFilterPython()
    assert node.conditions == []


@pytest.mark.property
def test_physical_filter_vectorized_default_conditions_empty():
    """PhysicalFilterVectorized defaults to no conditions."""
    node = PhysicalFilterVectorized()
    assert node.conditions == []


@pytest.mark.property
def test_physical_compute_networkx_default_measures_empty():
    """PhysicalComputeNetworkX defaults to no measures."""
    node = PhysicalComputeNetworkX()
    assert node.measures == []


@pytest.mark.property
def test_physical_topk_heap_defaults():
    """PhysicalTopKHeap has sensible defaults."""
    node = PhysicalTopKHeap()
    assert node.k == 10
    assert node.key == ""
    assert node.desc is True


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=_pos_int)
def test_physical_limit_early_stores_n(n):
    """PhysicalLimitEarly stores the provided n."""
    node = PhysicalLimitEarly(n=n)
    assert node.n == n


# ---------------------------------------------------------------------------
# Tree construction (children)
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_logical_tree_children_assignment():
    """Logical nodes can be composed via children list."""
    scan = LogicalScanNodes()
    flt = LogicalFilter(children=[scan])
    assert len(flt.children) == 1
    assert flt.children[0] is scan


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(n=st.integers(min_value=0, max_value=5))
def test_logical_tree_children_count(n):
    """LogicalOp children list has correct length after construction."""
    children = [LogicalScanNodes() for _ in range(n)]
    op = LogicalFilter(children=children)
    assert len(op.children) == n


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])

"""Property-based tests for the DSL selection fast path.

Tests algebraic invariants and correctness properties of the fast-path
selection module (:mod:`py3plex.dsl.fastpath`).

Covered properties
------------------
1. FastPlan.summary() always returns a non-empty, well-formed string.
2. FastIndex parallel arrays are always consistent in length.
3. fast_select_nodes always returns a subset of the index nodes list.
4. All nodes returned by fast_select_nodes satisfy the declared degree bounds.
5. All nodes returned by fast_select_nodes belong to the declared allowed
   layers when a layer filter is specified.
6. fast_select_edges always returns a subset of the index edges list.
7. All edges returned by fast_select_edges satisfy the declared degree bounds.
8. Monotonicity: increasing node_degree_min produces fewer-or-equal results.
9. Monotonicity: decreasing node_degree_max produces fewer-or-equal results.
10. Idempotence: running fast_select_nodes twice on the same index gives the
    same result in the same order.
11. Equivalence: for eligible queries the fast path returns the same *set* of
    node tuples as the DSL v2 baseline executor.
12. Provenance flag is always a bool (never None) in every code path.
13. When DSL_FAST_PATH_ENABLED=False, fast_path provenance flag is always False.
14. Empty-network robustness: no exception is raised for any FastPlan on an
    empty network.
15. FastPlan with impossible bounds returns an empty selection without crashing.
"""

from __future__ import annotations

import importlib
from typing import Set, Tuple

import pytest
from hypothesis import assume, given, settings, strategies as st

from py3plex.core import multinet
from py3plex.dsl.fastpath import (
    FastIndex,
    FastPlan,
    build_fast_index,
    fast_select_edges,
    fast_select_nodes,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LAYER_NAMES = ["social", "work", "family", "sport", "online"]


def _make_network(
    n_nodes: int = 6,
    layers: list[str] | None = None,
    n_edges_per_layer: int = 4,
) -> multinet.multi_layer_network:
    """Build a small multilayer network deterministically."""
    if layers is None:
        layers = ["alpha", "beta"]
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edge_list = []
    for layer in layers:
        # Chain topology: n0-n1-n2-...-n(k-1)
        for i in range(min(n_edges_per_layer, n_nodes - 1)):
            edge_list.append([f"n{i}", layer, f"n{i + 1}", layer, 1.0])
    if edge_list:
        net.add_edges(edge_list, input_type="list")
    return net


def _make_plan(
    target: str = "nodes",
    allowed_layers: Set[str] | None = None,
    node_degree_min: int | None = None,
    node_degree_max: int | None = None,
    src_degree_min: int | None = None,
    src_degree_max: int | None = None,
    dst_degree_min: int | None = None,
    dst_degree_max: int | None = None,
) -> FastPlan:
    """Convenience wrapper that also clears the private _layer_set attr."""
    plan = FastPlan(
        target=target,
        allowed_layers=allowed_layers,
        node_degree_min=node_degree_min,
        node_degree_max=node_degree_max,
        src_degree_min=src_degree_min,
        src_degree_max=src_degree_max,
        dst_degree_min=dst_degree_min,
        dst_degree_max=dst_degree_max,
    )
    plan._layer_set = None  # type: ignore[attr-defined]
    plan._layer_expr = None  # type: ignore[attr-defined]
    return plan


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

@st.composite
def degree_bound_pair(draw) -> Tuple[int, int]:
    """Draw (lo, hi) with lo <= hi in range 0..5."""
    lo = draw(st.integers(min_value=0, max_value=4))
    hi = draw(st.integers(min_value=lo, max_value=5))
    return lo, hi


@st.composite
def optional_degree_min(draw) -> int | None:
    return draw(st.one_of(st.none(), st.integers(min_value=0, max_value=5)))


@st.composite
def optional_degree_max(draw) -> int | None:
    return draw(st.one_of(st.none(), st.integers(min_value=0, max_value=5)))


@st.composite
def small_network_strategy(draw) -> multinet.multi_layer_network:
    """Randomly draw a small multilayer network."""
    n_nodes = draw(st.integers(min_value=2, max_value=8))
    n_layers = draw(st.integers(min_value=1, max_value=3))
    n_edges = draw(st.integers(min_value=1, max_value=n_nodes - 1))
    layers = [f"L{i}" for i in range(n_layers)]
    return _make_network(n_nodes=n_nodes, layers=layers, n_edges_per_layer=n_edges)


# ===========================================================================
# Property 1 – FastPlan.summary() invariants
# ===========================================================================

class TestFastPlanSummaryProperties:
    """FastPlan.summary() must always return a well-formed non-empty string."""

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        d_min=optional_degree_min(),
        d_max=optional_degree_max(),
        layers=st.one_of(
            st.none(),
            st.frozensets(st.sampled_from(_LAYER_NAMES), min_size=1, max_size=3),
        ),
    )
    def test_summary_is_nonempty_string(self, d_min, d_max, layers):
        """summary() always returns a non-empty string."""
        plan = _make_plan(
            target="nodes",
            allowed_layers=set(layers) if layers else None,
            node_degree_min=d_min,
            node_degree_max=d_max,
        )
        result = plan.summary()
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        target=st.sampled_from(["nodes", "edges"]),
        d_min=optional_degree_min(),
        d_max=optional_degree_max(),
    )
    def test_summary_contains_target(self, target, d_min, d_max):
        """summary() always includes 'target=<value>'."""
        plan = _make_plan(target=target, node_degree_min=d_min, node_degree_max=d_max)
        summary = plan.summary()
        assert f"target={target}" in summary

    @pytest.mark.property
    @settings(deadline=None, max_examples=30)
    @given(
        d_min=st.integers(min_value=0, max_value=10),
        d_max=st.integers(min_value=0, max_value=10),
    )
    def test_summary_contains_degree_info_when_set(self, d_min, d_max):
        """When degree bounds are set, summary() mentions them."""
        plan = _make_plan(node_degree_min=d_min, node_degree_max=d_max)
        summary = plan.summary()
        assert str(d_min) in summary
        assert str(d_max) in summary

    @pytest.mark.property
    @settings(deadline=None, max_examples=30)
    @given(
        layers=st.frozensets(st.sampled_from(_LAYER_NAMES), min_size=1, max_size=3),
    )
    def test_summary_contains_layer_info_when_set(self, layers):
        """When allowed_layers is set, summary() mentions them."""
        plan = _make_plan(allowed_layers=set(layers))
        summary = plan.summary()
        for layer in layers:
            assert layer in summary


# ===========================================================================
# Property 2 – FastIndex structural consistency
# ===========================================================================

class TestFastIndexConsistencyProperties:
    """FastIndex parallel arrays must always be consistent in length."""

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_node_index_parallel_arrays_same_length(self, net):
        """nodes_list, node_layers, and node_degree must be the same length."""
        plan = _make_plan(target="nodes")
        idx = build_fast_index(net, plan)
        n = len(idx.nodes_list)
        assert len(idx.node_layers) == n
        assert len(idx.node_degree) == n

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_nodes_by_layer_indices_in_bounds(self, net):
        """All indices stored in nodes_by_layer must be valid for nodes_list."""
        plan = _make_plan(target="nodes")
        idx = build_fast_index(net, plan)
        n = len(idx.nodes_list)
        for layer, indices in idx.nodes_by_layer.items():
            for i in indices:
                assert 0 <= i < n, (
                    f"Index {i} out of range [0, {n}) in layer '{layer}'"
                )

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_edge_index_parallel_arrays_same_length(self, net):
        """edges_list, edge_src_degree, and edge_dst_degree must be same length."""
        plan = _make_plan(target="edges")
        idx = build_fast_index(net, plan)
        n = len(idx.edges_list)
        assert len(idx.edge_src_degree) == n
        assert len(idx.edge_dst_degree) == n

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_edges_by_layerpair_indices_in_bounds(self, net):
        """All indices stored in edges_by_layerpair must be valid."""
        plan = _make_plan(target="edges")
        idx = build_fast_index(net, plan)
        n = len(idx.edges_list)
        for pair, indices in idx.edges_by_layerpair.items():
            for i in indices:
                assert 0 <= i < n

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_node_degrees_are_nonnegative(self, net):
        """Every value in node_degree must be >= 0."""
        plan = _make_plan(target="nodes")
        idx = build_fast_index(net, plan)
        for deg in idx.node_degree:
            assert deg >= 0

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_edge_degrees_are_nonnegative(self, net):
        """Every src/dst degree must be >= 0."""
        plan = _make_plan(target="edges")
        idx = build_fast_index(net, plan)
        for deg in idx.edge_src_degree:
            assert deg >= 0
        for deg in idx.edge_dst_degree:
            assert deg >= 0


# ===========================================================================
# Property 3 – fast_select_nodes subset and correctness
# ===========================================================================

class TestFastSelectNodesProperties:
    """Invariants for fast_select_nodes output."""

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        net=small_network_strategy(),
        d_min=optional_degree_min(),
    )
    def test_result_is_subset_of_index(self, net, d_min):
        """fast_select_nodes always returns items from idx.nodes_list."""
        plan = _make_plan(target="nodes", node_degree_min=d_min)
        idx = build_fast_index(net, plan)
        selected = fast_select_nodes(plan, idx)
        nodes_set = set(idx.nodes_list)
        for item in selected:
            assert item in nodes_set

    @pytest.mark.property
    @settings(deadline=None, max_examples=60)
    @given(
        net=small_network_strategy(),
        d_min=optional_degree_min(),
        d_max=optional_degree_max(),
    )
    def test_degree_bounds_satisfied(self, net, d_min, d_max):
        """Every selected node's degree must satisfy the declared bounds."""
        if d_min is not None and d_max is not None and d_min > d_max:
            d_min, d_max = d_max, d_min  # normalize so d_min <= d_max

        plan = _make_plan(target="nodes", node_degree_min=d_min, node_degree_max=d_max)
        idx = build_fast_index(net, plan)
        # Build a lookup map from node tuple to its degree
        deg_map = dict(zip(idx.nodes_list, idx.node_degree))
        selected = fast_select_nodes(plan, idx)
        for item in selected:
            deg = deg_map[item]
            if d_min is not None:
                assert deg >= d_min, f"Node {item} has degree {deg} < min {d_min}"
            if d_max is not None:
                assert deg <= d_max, f"Node {item} has degree {deg} > max {d_max}"

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        net=small_network_strategy(),
        layers=st.frozensets(st.just("L0"), min_size=1, max_size=1),
    )
    def test_layer_filter_respected(self, net, layers):
        """When allowed_layers is set, every returned node must be in that layer."""
        plan = _make_plan(target="nodes", allowed_layers=set(layers))
        idx = build_fast_index(net, plan)
        selected = fast_select_nodes(plan, idx)
        for node_tuple in selected:
            # node_tuple is (node_id, layer)
            assert node_tuple[1] in layers, (
                f"Node tuple {node_tuple} has layer '{node_tuple[1]}' "
                f"not in allowed_layers {layers}"
            )

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_no_filter_returns_all_index_nodes(self, net):
        """With no degree bounds or layer filter, all index nodes are returned."""
        plan = _make_plan(target="nodes")
        idx = build_fast_index(net, plan)
        selected = fast_select_nodes(plan, idx)
        assert set(selected) == set(idx.nodes_list)

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_impossible_bounds_return_empty(self, net):
        """With node_degree_min > node_degree_max the result is always empty."""
        plan = _make_plan(target="nodes", node_degree_min=1000, node_degree_max=0)
        idx = build_fast_index(net, plan)
        selected = fast_select_nodes(plan, idx)
        assert selected == []


# ===========================================================================
# Property 4 – fast_select_edges subset and correctness
# ===========================================================================

class TestFastSelectEdgesProperties:
    """Invariants for fast_select_edges output."""

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        net=small_network_strategy(),
        sd_min=optional_degree_min(),
    )
    def test_result_is_subset_of_index(self, net, sd_min):
        """fast_select_edges always returns items from idx.edges_list."""
        plan = _make_plan(target="edges", src_degree_min=sd_min)
        idx = build_fast_index(net, plan)
        selected = fast_select_edges(plan, idx)
        for item in selected:
            assert item in idx.edges_list

    @pytest.mark.property
    @settings(deadline=None, max_examples=60)
    @given(
        net=small_network_strategy(),
        sd_min=optional_degree_min(),
        sd_max=optional_degree_max(),
        dd_min=optional_degree_min(),
        dd_max=optional_degree_max(),
    )
    def test_edge_degree_bounds_satisfied(self, net, sd_min, sd_max, dd_min, dd_max):
        """Every selected edge's src/dst degree satisfies the bounds."""
        if sd_min is not None and sd_max is not None and sd_min > sd_max:
            sd_min, sd_max = sd_max, sd_min
        if dd_min is not None and dd_max is not None and dd_min > dd_max:
            dd_min, dd_max = dd_max, dd_min

        plan = _make_plan(
            target="edges",
            src_degree_min=sd_min,
            src_degree_max=sd_max,
            dst_degree_min=dd_min,
            dst_degree_max=dd_max,
        )
        idx = build_fast_index(net, plan)
        # Use id()-keyed maps because edge tuples contain dicts (unhashable).
        id_to_src_deg = {id(e): idx.edge_src_degree[i] for i, e in enumerate(idx.edges_list)}
        id_to_dst_deg = {id(e): idx.edge_dst_degree[i] for i, e in enumerate(idx.edges_list)}
        selected = fast_select_edges(plan, idx)
        for edge in selected:
            s_deg = id_to_src_deg[id(edge)]
            d_deg = id_to_dst_deg[id(edge)]
            if sd_min is not None:
                assert s_deg >= sd_min
            if sd_max is not None:
                assert s_deg <= sd_max
            if dd_min is not None:
                assert d_deg >= dd_min
            if dd_max is not None:
                assert d_deg <= dd_max

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_no_filter_returns_all_index_edges(self, net):
        """With no bounds, all index edges are returned."""
        plan = _make_plan(target="edges")
        idx = build_fast_index(net, plan)
        selected = fast_select_edges(plan, idx)
        assert selected == idx.edges_list

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_impossible_src_bounds_return_empty(self, net):
        """Impossible src degree bounds return an empty list."""
        plan = _make_plan(target="edges", src_degree_min=1000, src_degree_max=0)
        idx = build_fast_index(net, plan)
        selected = fast_select_edges(plan, idx)
        assert selected == []


# ===========================================================================
# Property 5 – Monotonicity of degree filtering
# ===========================================================================

class TestMonotonicityProperties:
    """Stricter filters must never produce more results."""

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        net=small_network_strategy(),
        lo=st.integers(min_value=0, max_value=3),
        hi=st.integers(min_value=0, max_value=3),
    )
    def test_higher_degree_min_reduces_or_equal_results(self, net, lo, hi):
        """Increasing node_degree_min never increases the result count."""
        d_min_lower = min(lo, hi)
        d_min_higher = max(lo, hi)

        plan_low = _make_plan(target="nodes", node_degree_min=d_min_lower)
        plan_high = _make_plan(target="nodes", node_degree_min=d_min_higher)

        idx = build_fast_index(net, plan_low)  # Build on unrestricted plan
        # Rebuild so the node list is the same
        idx_high = build_fast_index(net, plan_high)

        # Both index the same nodes; now select
        selected_low = fast_select_nodes(plan_low, idx)
        selected_high = fast_select_nodes(plan_high, idx_high)

        assert len(selected_high) <= len(selected_low), (
            f"Higher min {d_min_higher} should give fewer nodes than lower min "
            f"{d_min_lower}, got {len(selected_high)} vs {len(selected_low)}"
        )

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        net=small_network_strategy(),
        lo=st.integers(min_value=0, max_value=4),
        hi=st.integers(min_value=0, max_value=4),
    )
    def test_lower_degree_max_reduces_or_equal_results(self, net, lo, hi):
        """Decreasing node_degree_max never increases the result count."""
        d_max_higher = max(lo, hi)
        d_max_lower = min(lo, hi)

        plan_high = _make_plan(target="nodes", node_degree_max=d_max_higher)
        plan_low = _make_plan(target="nodes", node_degree_max=d_max_lower)

        idx = build_fast_index(net, plan_high)
        idx_low = build_fast_index(net, plan_low)

        selected_high = fast_select_nodes(plan_high, idx)
        selected_low = fast_select_nodes(plan_low, idx_low)

        assert len(selected_low) <= len(selected_high)

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        net=small_network_strategy(),
        lo=st.integers(min_value=0, max_value=3),
        hi=st.integers(min_value=0, max_value=3),
    )
    def test_higher_src_degree_min_reduces_or_equal_edges(self, net, lo, hi):
        """Increasing src_degree_min never increases edge count."""
        sd_min_lower = min(lo, hi)
        sd_min_higher = max(lo, hi)

        plan_low = _make_plan(target="edges", src_degree_min=sd_min_lower)
        plan_high = _make_plan(target="edges", src_degree_min=sd_min_higher)

        idx_low = build_fast_index(net, plan_low)
        idx_high = build_fast_index(net, plan_high)

        selected_low = fast_select_edges(plan_low, idx_low)
        selected_high = fast_select_edges(plan_high, idx_high)

        assert len(selected_high) <= len(selected_low)


# ===========================================================================
# Property 6 – Idempotence / stability
# ===========================================================================

class TestIdempotenceProperties:
    """Running the same fast selection twice must give identical results."""

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        net=small_network_strategy(),
        d_min=optional_degree_min(),
        d_max=optional_degree_max(),
    )
    def test_node_selection_is_idempotent(self, net, d_min, d_max):
        """Calling fast_select_nodes twice on the same index returns same list."""
        if d_min is not None and d_max is not None and d_min > d_max:
            d_min, d_max = d_max, d_min

        plan = _make_plan(target="nodes", node_degree_min=d_min, node_degree_max=d_max)
        idx = build_fast_index(net, plan)

        result1 = fast_select_nodes(plan, idx)
        result2 = fast_select_nodes(plan, idx)

        assert result1 == result2, (
            "fast_select_nodes is not idempotent: two calls returned different lists"
        )

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        net=small_network_strategy(),
        sd_min=optional_degree_min(),
        dd_min=optional_degree_min(),
    )
    def test_edge_selection_is_idempotent(self, net, sd_min, dd_min):
        """Calling fast_select_edges twice on the same index returns same list."""
        plan = _make_plan(target="edges", src_degree_min=sd_min, dst_degree_min=dd_min)
        idx = build_fast_index(net, plan)

        result1 = fast_select_edges(plan, idx)
        result2 = fast_select_edges(plan, idx)

        assert result1 == result2


# ===========================================================================
# Property 7 – Provenance flag consistency via the Q builder
# ===========================================================================

class TestProvenanceFlagProperties:
    """The fast_path provenance flag must always be a bool."""

    def _get_fast_path_flag(self, result) -> bool | None:
        return (
            result.meta
            .get("provenance", {})
            .get("backend", {})
            .get("fast_path")
        )

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_flag_is_bool_for_eligible_query(self, net):
        """fast_path provenance flag is always a bool, never None."""
        from py3plex.dsl import Q, L

        result = Q.nodes().execute(net)
        flag = self._get_fast_path_flag(result)
        assert isinstance(flag, bool), f"Expected bool, got {type(flag)}: {flag!r}"

    @pytest.mark.property
    @settings(deadline=None, max_examples=30)
    @given(
        net=small_network_strategy(),
        d_min=st.integers(min_value=0, max_value=4),
    )
    def test_flag_true_when_eligible_and_enabled(self, net, d_min):
        """When the query is eligible and flag is enabled, fast_path=True."""
        import py3plex.config as cfg
        from py3plex.dsl import Q

        original = cfg.DSL_FAST_PATH_ENABLED
        try:
            cfg.DSL_FAST_PATH_ENABLED = True
            result = Q.nodes().where(degree__gt=d_min).execute(net)
            flag = self._get_fast_path_flag(result)
            assert flag is True, (
                f"Expected fast_path=True for eligible query (degree__gt={d_min}), "
                f"got {flag!r}"
            )
        finally:
            cfg.DSL_FAST_PATH_ENABLED = original

    @pytest.mark.property
    @settings(deadline=None, max_examples=30)
    @given(net=small_network_strategy())
    def test_flag_false_when_disabled(self, net):
        """When DSL_FAST_PATH_ENABLED=False, fast_path is always False."""
        import py3plex.config as cfg
        from py3plex.dsl import Q

        original = cfg.DSL_FAST_PATH_ENABLED
        try:
            cfg.DSL_FAST_PATH_ENABLED = False
            result = Q.nodes().execute(net)
            flag = self._get_fast_path_flag(result)
            assert flag is False, (
                f"Expected fast_path=False when disabled, got {flag!r}"
            )
        finally:
            cfg.DSL_FAST_PATH_ENABLED = original

    @pytest.mark.property
    @settings(deadline=None, max_examples=30)
    @given(net=small_network_strategy())
    def test_flag_false_for_ineligible_query(self, net):
        """Queries with compute() are ineligible; fast_path must be False."""
        import py3plex.config as cfg
        from py3plex.dsl import Q

        original = cfg.DSL_FAST_PATH_ENABLED
        try:
            cfg.DSL_FAST_PATH_ENABLED = True
            # compute() makes the query ineligible for the fast path
            result = Q.nodes().compute("degree").execute(net)
            flag = self._get_fast_path_flag(result)
            assert flag is False, (
                f"Expected fast_path=False for query with compute(), got {flag!r}"
            )
        finally:
            cfg.DSL_FAST_PATH_ENABLED = original


# ===========================================================================
# Property 8 – Fast path / baseline equivalence
# ===========================================================================

class TestEquivalenceProperties:
    """Fast-path selection must return the same *set* as the baseline."""

    @pytest.mark.property
    @settings(deadline=None, max_examples=50)
    @given(
        net=small_network_strategy(),
        d_min=st.integers(min_value=0, max_value=3),
    )
    def test_node_fast_path_matches_baseline_set(self, net, d_min):
        """With fast path enabled vs disabled, the result sets must be equal."""
        import py3plex.config as cfg
        from py3plex.dsl import Q

        original = cfg.DSL_FAST_PATH_ENABLED

        try:
            cfg.DSL_FAST_PATH_ENABLED = True
            result_fast = Q.nodes().where(degree__gt=d_min).execute(net)

            cfg.DSL_FAST_PATH_ENABLED = False
            result_baseline = Q.nodes().where(degree__gt=d_min).execute(net)
        finally:
            cfg.DSL_FAST_PATH_ENABLED = original

        set_fast = set(result_fast.items)
        set_baseline = set(result_baseline.items)

        assert set_fast == set_baseline, (
            f"Fast path and baseline disagree for degree__gt={d_min}:\n"
            f"  fast only: {set_fast - set_baseline}\n"
            f"  baseline only: {set_baseline - set_fast}"
        )

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(net=small_network_strategy())
    def test_node_no_filter_fast_path_matches_baseline(self, net):
        """Pure node selection (no filter) gives same set in both paths."""
        import py3plex.config as cfg
        from py3plex.dsl import Q

        original = cfg.DSL_FAST_PATH_ENABLED

        try:
            cfg.DSL_FAST_PATH_ENABLED = True
            result_fast = Q.nodes().execute(net)

            cfg.DSL_FAST_PATH_ENABLED = False
            result_baseline = Q.nodes().execute(net)
        finally:
            cfg.DSL_FAST_PATH_ENABLED = original

        assert set(result_fast.items) == set(result_baseline.items)

    @pytest.mark.property
    @settings(deadline=None, max_examples=40)
    @given(
        net=small_network_strategy(),
        d_min=st.integers(min_value=0, max_value=3),
        d_max=st.integers(min_value=0, max_value=3),
    )
    def test_degree_range_fast_path_matches_baseline(self, net, d_min, d_max):
        """AND-combined degree_min and degree_max give consistent results."""
        actual_min = min(d_min, d_max)
        actual_max = max(d_min, d_max)

        import py3plex.config as cfg
        from py3plex.dsl import Q

        original = cfg.DSL_FAST_PATH_ENABLED

        try:
            cfg.DSL_FAST_PATH_ENABLED = True
            result_fast = (
                Q.nodes()
                .where(degree__gte=actual_min)
                .where(degree__lte=actual_max)
                .execute(net)
            )

            cfg.DSL_FAST_PATH_ENABLED = False
            result_baseline = (
                Q.nodes()
                .where(degree__gte=actual_min)
                .where(degree__lte=actual_max)
                .execute(net)
            )
        finally:
            cfg.DSL_FAST_PATH_ENABLED = original

        assert set(result_fast.items) == set(result_baseline.items)


# ===========================================================================
# Property 9 – Empty network robustness
# ===========================================================================

class TestEmptyNetworkRobustness:
    """No exception should be raised for any FastPlan on an empty network."""

    @pytest.mark.property
    @settings(deadline=None, max_examples=30)
    @given(
        d_min=optional_degree_min(),
        d_max=optional_degree_max(),
    )
    def test_node_index_on_empty_network(self, d_min, d_max):
        """build_fast_index + fast_select_nodes never crashes on empty networks."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        plan = _make_plan(target="nodes", node_degree_min=d_min, node_degree_max=d_max)
        idx = build_fast_index(net, plan)
        result = fast_select_nodes(plan, idx)
        assert result == []

    @pytest.mark.property
    @settings(deadline=None, max_examples=30)
    @given(
        sd_min=optional_degree_min(),
        dd_min=optional_degree_min(),
    )
    def test_edge_index_on_empty_network(self, sd_min, dd_min):
        """build_fast_index + fast_select_edges never crashes on empty networks."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        plan = _make_plan(target="edges", src_degree_min=sd_min, dst_degree_min=dd_min)
        idx = build_fast_index(net, plan)
        result = fast_select_edges(plan, idx)
        assert result == []

    @pytest.mark.property
    @settings(deadline=None, max_examples=20)
    @given(d_min=st.integers(min_value=0, max_value=4))
    def test_q_execute_on_empty_network(self, d_min):
        """Q.nodes().where(...).execute() never raises on an empty network."""
        from py3plex.dsl import Q

        net = multinet.multi_layer_network(directed=False, verbose=False)
        result = Q.nodes().where(degree__gt=d_min).execute(net)
        assert result.items == []

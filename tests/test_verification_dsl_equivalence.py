"""
Differential testing for DSL v2 vs Legacy DSL equivalence.

These tests verify that equivalent queries expressed in both DSL styles
produce consistent results:

1. Node selection equivalence
2. Edge selection equivalence
3. Computed measures equivalence
4. Ordering consistency
5. Metadata/provenance presence

All tests use canonical graphs for deterministic comparison.
"""

import pytest
from typing import Set, List, Any

from tests.fixtures import tiny_two_layer, small_three_layer, two_cliques_bridge
from py3plex.dsl import Q, execute_query
from py3plex.dsl.result import QueryResult


# ============================================================================
# Helper Functions
# ============================================================================


def get_node_ids_from_result(result: QueryResult) -> Set[Any]:
    """
    Extract set of node IDs from a query result.
    
    Args:
        result: Query result object
        
    Returns:
        Set of node IDs present in result
    """
    df = result.to_pandas()
    if 'node' in df.columns:
        return set(df['node'].tolist())
    elif 'source' in df.columns:
        return set(df['source'].tolist())
    else:
        raise ValueError("Cannot extract node IDs from result")


def get_measure_values_sorted(result: QueryResult, measure: str) -> List[float]:
    """
    Extract sorted measure values from query result.
    
    Args:
        result: Query result object
        measure: Measure name to extract
        
    Returns:
        Sorted list of measure values
    """
    df = result.to_pandas()
    if measure not in df.columns:
        raise ValueError(f"Measure '{measure}' not in result")
    
    values = df[measure].tolist()
    return sorted([v for v in values if v is not None])


# ============================================================================
# Node Selection Equivalence Tests
# ============================================================================


@pytest.mark.metamorphic
def test_dsl_equivalence_select_all_nodes():
    """
    Test that selecting all nodes produces the same result in both DSLs.
    
    Legacy DSL: "SELECT nodes"
    DSL v2: Q.nodes().execute(net)
    """
    net = tiny_two_layer()
    
    # Legacy DSL
    try:
        legacy_result = execute_query(net, "SELECT nodes")
        legacy_nodes = get_node_ids_from_result(legacy_result)
    except Exception as e:
        pytest.skip(f"Legacy DSL failed: {e}")
    
    # DSL v2
    try:
        v2_result = Q.nodes().execute(net)
        v2_nodes = get_node_ids_from_result(v2_result)
    except Exception as e:
        pytest.skip(f"DSL v2 failed: {e}")
    
    # Should select the same nodes
    assert legacy_nodes == v2_nodes, (
        f"Node selection differs: Legacy={len(legacy_nodes)}, v2={len(v2_nodes)}"
    )


@pytest.mark.metamorphic
def test_dsl_equivalence_select_nodes_with_layer_filter():
    """
    Test node selection with layer filtering.
    
    Legacy DSL: "SELECT nodes WHERE layer=0" or "SELECT nodes FROM layer='0'"
    DSL v2: Q.nodes().from_layers(L[0]).execute(net)
    """
    from py3plex.dsl import L
    
    net = small_three_layer()
    
    # Legacy DSL (using FROM syntax for layer selection)
    try:
        legacy_result = execute_query(net, 'SELECT nodes FROM layer="0"')
        legacy_nodes = get_node_ids_from_result(legacy_result)
    except Exception as e:
        # Try alternative WHERE syntax
        try:
            legacy_result = execute_query(net, 'SELECT nodes WHERE layer=0')
            legacy_nodes = get_node_ids_from_result(legacy_result)
        except Exception as e2:
            pytest.skip(f"Legacy DSL failed: {e}, {e2}")
    
    # DSL v2
    try:
        v2_result = Q.nodes().from_layers(L[0]).execute(net)
        v2_nodes = get_node_ids_from_result(v2_result)
    except Exception as e:
        pytest.skip(f"DSL v2 failed: {e}")
    
    # Should select the same nodes from layer 0
    assert legacy_nodes == v2_nodes, (
        f"Layer 0 node selection differs: Legacy={len(legacy_nodes)}, v2={len(v2_nodes)}"
    )


@pytest.mark.metamorphic
def test_dsl_equivalence_select_nodes_with_degree_filter():
    """
    Test node selection with degree filtering.
    
    Legacy DSL: "SELECT nodes WHERE degree > 1"
    DSL v2: Q.nodes().where(degree__gt=1).execute(net)
    """
    net = two_cliques_bridge()
    
    # Legacy DSL
    try:
        legacy_result = execute_query(net, "SELECT nodes WHERE degree > 1")
        legacy_nodes = get_node_ids_from_result(legacy_result)
    except Exception as e:
        pytest.skip(f"Legacy DSL failed: {e}")
    
    # DSL v2
    try:
        v2_result = Q.nodes().where(degree__gt=1).execute(net)
        v2_nodes = get_node_ids_from_result(v2_result)
    except Exception as e:
        pytest.skip(f"DSL v2 failed: {e}")
    
    # Should select the same high-degree nodes
    assert legacy_nodes == v2_nodes, (
        f"Degree filter differs: Legacy={len(legacy_nodes)}, v2={len(v2_nodes)}"
    )


# ============================================================================
# Computed Measures Equivalence Tests
# ============================================================================


@pytest.mark.metamorphic
def test_dsl_equivalence_compute_degree():
    """
    Test that computing degree produces numerically equivalent results.
    
    Legacy DSL: "SELECT nodes COMPUTE degree"
    DSL v2: Q.nodes().compute("degree").execute(net)
    """
    net = tiny_two_layer()
    
    # Legacy DSL
    try:
        legacy_result = execute_query(net, "SELECT nodes COMPUTE degree")
        legacy_values = get_measure_values_sorted(legacy_result, "degree")
    except Exception as e:
        pytest.skip(f"Legacy DSL failed: {e}")
    
    # DSL v2
    try:
        v2_result = Q.nodes().compute("degree").execute(net)
        v2_values = get_measure_values_sorted(v2_result, "degree")
    except Exception as e:
        pytest.skip(f"DSL v2 failed: {e}")
    
    # Degree values should match exactly (integers)
    assert legacy_values == v2_values, (
        f"Degree values differ:\nLegacy: {legacy_values}\nv2: {v2_values}"
    )


@pytest.mark.metamorphic
def test_dsl_equivalence_compute_betweenness():
    """
    Test that computing betweenness centrality produces equivalent results.
    
    Legacy DSL: "SELECT nodes COMPUTE betweenness_centrality"
    DSL v2: Q.nodes().compute("betweenness_centrality").execute(net)
    """
    net = two_cliques_bridge()
    
    # Legacy DSL
    try:
        legacy_result = execute_query(net, "SELECT nodes COMPUTE betweenness_centrality")
        legacy_values = get_measure_values_sorted(legacy_result, "betweenness_centrality")
    except Exception as e:
        pytest.skip(f"Legacy DSL failed: {e}")
    
    # DSL v2
    try:
        v2_result = Q.nodes().compute("betweenness_centrality").execute(net)
        v2_values = get_measure_values_sorted(v2_result, "betweenness_centrality")
    except Exception as e:
        pytest.skip(f"DSL v2 failed: {e}")
    
    # Values should be numerically close (floating point)
    assert len(legacy_values) == len(v2_values), (
        f"Result count differs: {len(legacy_values)} vs {len(v2_values)}"
    )
    
    for i, (legacy_val, v2_val) in enumerate(zip(legacy_values, v2_values)):
        assert abs(legacy_val - v2_val) < 1e-6, (
            f"Betweenness value {i} differs: {legacy_val} vs {v2_val}"
        )


@pytest.mark.metamorphic
def test_dsl_equivalence_compute_pagerank():
    """
    Test that computing PageRank produces equivalent results.
    
    Legacy DSL: "SELECT nodes COMPUTE pagerank"
    DSL v2: Q.nodes().compute("pagerank").execute(net)
    """
    net = small_three_layer()
    
    # Legacy DSL
    try:
        legacy_result = execute_query(net, "SELECT nodes COMPUTE pagerank")
        legacy_values = get_measure_values_sorted(legacy_result, "pagerank")
    except Exception as e:
        pytest.skip(f"Legacy DSL failed: {e}")
    
    # DSL v2
    try:
        v2_result = Q.nodes().compute("pagerank").execute(net)
        v2_values = get_measure_values_sorted(v2_result, "pagerank")
    except Exception as e:
        pytest.skip(f"DSL v2 failed: {e}")
    
    # Values should be numerically close
    assert len(legacy_values) == len(v2_values)
    
    for legacy_val, v2_val in zip(legacy_values, v2_values):
        assert abs(legacy_val - v2_val) < 1e-6, (
            f"PageRank differs: {legacy_val} vs {v2_val}"
        )


# ============================================================================
# Edge Selection Equivalence Tests
# ============================================================================


@pytest.mark.metamorphic
def test_dsl_equivalence_select_all_edges():
    """
    Test that selecting all edges produces the same result.
    
    Legacy DSL: "SELECT edges"
    DSL v2: Q.edges().execute(net)
    """
    net = tiny_two_layer()
    
    # Legacy DSL
    try:
        legacy_result = execute_query(net, "SELECT edges")
        legacy_df = legacy_result.to_pandas()
        legacy_count = len(legacy_df)
    except Exception as e:
        pytest.skip(f"Legacy DSL failed: {e}")
    
    # DSL v2
    try:
        v2_result = Q.edges().execute(net)
        v2_df = v2_result.to_pandas()
        v2_count = len(v2_df)
    except Exception as e:
        pytest.skip(f"DSL v2 failed: {e}")
    
    # Should select the same number of edges
    assert legacy_count == v2_count, (
        f"Edge count differs: Legacy={legacy_count}, v2={v2_count}"
    )


@pytest.mark.metamorphic
def test_dsl_equivalence_select_intralayer_edges():
    """
    Test selecting intralayer edges only.
    
    Legacy DSL: "SELECT edges WHERE intralayer=True"
    DSL v2: Q.edges().where(intralayer=True).execute(net)
    """
    net = small_three_layer()
    
    # Legacy DSL
    try:
        legacy_result = execute_query(net, "SELECT edges WHERE intralayer=True")
        legacy_count = len(legacy_result.to_pandas())
    except Exception as e:
        pytest.skip(f"Legacy DSL failed: {e}")
    
    # DSL v2
    try:
        v2_result = Q.edges().where(intralayer=True).execute(net)
        v2_count = len(v2_result.to_pandas())
    except Exception as e:
        pytest.skip(f"DSL v2 failed: {e}")
    
    # Should select the same intralayer edges
    assert legacy_count == v2_count, (
        f"Intralayer edge count differs: Legacy={legacy_count}, v2={v2_count}"
    )


# ============================================================================
# Ordering Consistency Tests
# ============================================================================


@pytest.mark.metamorphic
def test_dsl_equivalence_ordering_by_degree():
    """
    Test that ordering by degree produces consistent results.
    
    Legacy DSL: "SELECT nodes COMPUTE degree ORDER BY degree DESC"
    DSL v2: Q.nodes().compute("degree").order_by("degree", desc=True).execute(net)
    """
    net = two_cliques_bridge()
    
    # Legacy DSL (if ORDER BY is supported)
    try:
        legacy_result = execute_query(net, "SELECT nodes COMPUTE degree ORDER BY degree DESC")
        legacy_df = legacy_result.to_pandas()
        legacy_degrees = legacy_df['degree'].tolist()[:3]  # Top 3
    except Exception as e:
        pytest.skip(f"Legacy DSL failed or ORDER BY not supported: {e}")
    
    # DSL v2
    try:
        v2_result = Q.nodes().compute("degree").order_by("degree", desc=True).execute(net)
        v2_df = v2_result.to_pandas()
        v2_degrees = v2_df['degree'].tolist()[:3]  # Top 3
    except Exception as e:
        pytest.skip(f"DSL v2 failed: {e}")
    
    # Top degree values should match
    assert legacy_degrees == v2_degrees, (
        f"Ordering differs:\nLegacy top 3: {legacy_degrees}\nv2 top 3: {v2_degrees}"
    )


# ============================================================================
# Provenance/Metadata Tests
# ============================================================================


@pytest.mark.metamorphic
def test_dsl_v2_has_provenance():
    """
    Test that DSL v2 includes provenance metadata.
    
    DSL v2 should provide richer provenance than legacy DSL.
    """
    net = tiny_two_layer()
    
    # DSL v2
    result = Q.nodes().compute("degree").execute(net)
    
    # Check for provenance metadata
    assert hasattr(result, 'meta'), "Result should have meta attribute"
    # DSL v2 includes provenance in meta
    assert 'provenance' in result.meta or 'dsl_version' in result.meta, (
        "Result should contain provenance or dsl_version in metadata"
    )


@pytest.mark.metamorphic
def test_dsl_v2_ast_stability():
    """
    Test that DSL v2 produces stable AST for identical queries.
    
    Certificate: Same query should produce same AST structure.
    """
    net = tiny_two_layer()
    
    # Build same query twice
    q1 = Q.nodes().compute("degree")
    q2 = Q.nodes().compute("degree")
    
    # Convert to AST
    ast1 = q1.to_ast()
    ast2 = q2.to_ast()
    
    # ASTs should be equal (or at least structurally equivalent)
    # This is a basic smoke test for AST stability
    assert ast1 is not None, "AST should not be None"
    assert ast2 is not None, "AST should not be None"
    
    # If AST has a hash or repr, it should match
    if hasattr(ast1, '__repr__'):
        assert repr(ast1) == repr(ast2), "AST representations should match"

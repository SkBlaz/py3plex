"""Regression tests for GraphProgram execution cache identity."""
import pytest

from py3plex.dsl import Param, Q
from py3plex.dsl.program import GraphProgram, clear_global_cache, get_global_cache
from py3plex.dsl.program.cache import execution_fingerprint
from py3plex.core import multinet


def test_parameter_bindings_change_execution_identity():
    low = execution_fingerprint(seed=42, params={"threshold": 1})
    high = execution_fingerprint(seed=42, params={"threshold": 10})
    assert low != high


def test_execution_identity_canonicalizes_mapping_order():
    left = execution_fingerprint(seed=42, params={"a": 1, "b": 2})
    right = execution_fingerprint(seed=42, params={"b": 2, "a": 1})
    assert left == right


def test_execution_identity_preserves_value_types():
    assert execution_fingerprint(seed=1, params={"x": 1}) != execution_fingerprint(
        seed=1, params={"x": True}
    )
    assert execution_fingerprint(seed=1, params={"x": [1]}) != execution_fingerprint(
        seed=1, params={"x": (1,)}
    )


def test_execution_identity_includes_planner_and_explain_options():
    base = execution_fingerprint(seed=1)
    assert base != execution_fingerprint(seed=1, planner_config={"mode": "fast"})
    assert base != execution_fingerprint(seed=1, explain_plan=True)


def test_unsupported_or_nonfinite_parameters_are_rejected_for_cache():
    with pytest.raises(TypeError, match="Cannot cache"):
        execution_fingerprint(seed=1, params={"x": object()})
    with pytest.raises(ValueError, match="Non-finite"):
        execution_fingerprint(seed=1, params={"x": float("nan")})


def test_parameterized_seeded_programs_do_not_reuse_other_bindings():
    clear_global_cache()
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "low", "type": "L", "score": 2},
            {"source": "high", "type": "L", "score": 20},
        ]
    )
    program = GraphProgram.from_ast(
        Q.nodes().where(score__gt=Param.int("threshold")).to_ast()
    )

    low_threshold = program.execute(net, params={"threshold": 1}, seed=42, progress=False)
    high_threshold = program.execute(net, params={"threshold": 10}, seed=42, progress=False)

    assert len(low_threshold.items) == 2
    assert len(high_threshold.items) == 1
    assert get_global_cache().size() == 2


def test_plain_degree_recomputes_on_auto_and_honors_explicit_cache(monkeypatch):
    from py3plex.core.multinet import multi_layer_network
    from py3plex.dsl import Q
    from py3plex.dsl.program.cache import ProgramCache

    cache = ProgramCache()
    monkeypatch.setattr("py3plex.dsl.program.cache._global_cache", cache)
    net = multi_layer_network(directed=False)
    net.add_edges([["a", "L", "b", "L", 1]], input_type="list")
    program = Q.nodes().compute("degree").compile()
    def run(policy):
        return program.execute(net, seed=42, progress=False, cache_policy=policy)
    assert run("auto").attributes == run("auto").attributes
    assert cache.size() == 0
    first = run("enabled")
    assert run("enabled").attributes == first.attributes
    assert cache.statistics()["hits"] == 1
    net.core_network.add_edge(("a", "L"), ("b", "L"))
    assert run("enabled").attributes["degree"][("a", "L")] == 2


def test_streamed_fingerprint_matches_tagged_graph_tuple():
    import networkx as nx
    from py3plex.dsl.program.cache import _fingerprint_value, graph_fingerprint

    for kind in (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph):
        graph = kind()
        graph.add_edge("ä", 2, details={"nested": [True, None, 3]})
        graph.add_edge("ä", 2, weight=2.3)
        edges = graph.edges(keys=True, data=True) if graph.is_multigraph() else graph.edges(data=True)
        reference = (kind.__name__, graph.is_directed(), None, None, None, None,
                     None, graph.graph, list(graph.nodes(data=True)), list(edges), [])
        assert graph_fingerprint(graph) == _fingerprint_value(reference)

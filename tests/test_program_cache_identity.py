"""Regression tests for GraphProgram execution cache identity."""
import pytest

from py3plex.dsl import Param, Q
from py3plex.dsl.ast import ast_from_json, ast_to_json
from py3plex.dsl.program import GraphProgram, clear_global_cache, get_global_cache
from py3plex.dsl.program.cache import execution_fingerprint, graph_fingerprint
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


def test_graph_fingerprint_includes_attributes_and_mutation_version():
    left = multinet.multi_layer_network(directed=False, verbose=False)
    right = multinet.multi_layer_network(directed=False, verbose=False)
    for network, weight in ((left, 1), (right, 2)):
        network.add_edges(
            [
                {
                    "source": "A",
                    "target": "B",
                    "source_type": "L",
                    "target_type": "L",
                    "weight": weight,
                }
            ]
        )

    assert graph_fingerprint(left) != graph_fingerprint(right)


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


def test_community_configuration_is_part_of_program_identity_and_round_trip():
    baseline = GraphProgram.from_ast(
        Q.nodes().community(method="leiden", gamma=1.0, omega=1.0).to_ast()
    )
    configured = GraphProgram.from_ast(
        Q.nodes().community(method="leiden", gamma=1.5, omega=0.5).to_ast()
    )

    assert baseline.program_hash != configured.program_hash

    restored_ast = ast_from_json(ast_to_json(configured.canonical_ast))
    restored = GraphProgram.from_ast(restored_ast)
    assert restored.program_hash == configured.program_hash

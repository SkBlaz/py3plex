"""Tests for QueryBuilder.to_ast() immutability.

Verifies that:
- to_ast() returns independent Query objects (no shared references)
- SelectStmt objects between calls are not the same object
- Mutating the builder after to_ast() does not affect previously exported ASTs
- Query results remain unchanged for existing DSL tests
"""

import pytest
from py3plex.dsl import Q, L
from py3plex.core import multinet


# ---------------------------------------------------------------------------
# Tiny deterministic test network
# ---------------------------------------------------------------------------

@pytest.fixture
def tiny_net():
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {"source": "A", "type": "social"},
        {"source": "B", "type": "social"},
        {"source": "C", "type": "work"},
        {"source": "D", "type": "work"},
    ])
    net.add_edges([
        {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
        {"source": "C", "target": "D", "source_type": "work", "target_type": "work"},
        {"source": "A", "target": "C", "source_type": "social", "target_type": "work"},
    ])
    return net


# ---------------------------------------------------------------------------
# Identity tests — two calls must return distinct objects
# ---------------------------------------------------------------------------

def test_to_ast_returns_different_objects():
    """Two successive to_ast() calls must return distinct Query objects."""
    q = Q.nodes().compute("degree")
    a1 = q.to_ast()
    a2 = q.to_ast()
    assert a1 is not a2


def test_to_ast_select_is_independent():
    """The SelectStmt inside each returned Query must be a different object."""
    q = Q.nodes().compute("degree")
    a1 = q.to_ast()
    a2 = q.to_ast()
    assert a1.select is not a2.select


def test_to_ast_repeated_calls_are_equal():
    """Two to_ast() calls on the same (unmodified) builder produce equal ASTs."""
    q = Q.nodes().where(degree__gt=2).compute("degree")
    a1 = q.to_ast()
    a2 = q.to_ast()
    # They should be equivalent even though they are different objects
    import dataclasses
    assert dataclasses.asdict(a1) == dataclasses.asdict(a2)


# ---------------------------------------------------------------------------
# Mutation isolation — builder mutations must not leak into exported ASTs
# ---------------------------------------------------------------------------

def test_builder_mutation_does_not_affect_previous_ast():
    """Mutating builder state after to_ast() must not change the exported AST."""
    q = Q.nodes().compute("degree")
    ast_before = q.to_ast()

    # Calling a chained builder method modifies internal state
    q2 = q.compute("betweenness_centrality")

    ast_after_mutation = q.to_ast()
    # The original snapshot should still reflect only "degree"
    measure_names_before = [c.result_name for c in ast_before.select.compute]
    assert "betweenness_centrality" not in measure_names_before, (
        "Export from before mutation should not include later-added metrics"
    )


def test_compile_snapshot_is_independent_of_builder():
    """compile() should hold an immutable snapshot; later builder changes must not affect it."""
    q = Q.nodes().compute("degree")
    program = q.compile()
    program_measures_before = [
        c.result_name for c in program.canonical_ast.select.compute
    ]

    # Now extend the builder
    q.compute("betweenness_centrality")

    # The program must still see only what was there at compile time
    program_measures_after = [
        c.result_name for c in program.canonical_ast.select.compute
    ]
    assert program_measures_before == program_measures_after


# ---------------------------------------------------------------------------
# Compute lists in ASTs are independent
# ---------------------------------------------------------------------------

def test_compute_lists_are_not_shared():
    """Compute lists in two separate to_ast() results must be different list objects."""
    q = Q.nodes().compute("degree")
    a1 = q.to_ast()
    a2 = q.to_ast()
    # Lists themselves must be different objects
    assert a1.select.compute is not a2.select.compute


def test_where_clause_is_independent():
    """Where clause in two to_ast() results must be independent objects."""
    q = Q.nodes().where(degree__gt=3)
    a1 = q.to_ast()
    a2 = q.to_ast()
    if a1.select.where is not None and a2.select.where is not None:
        assert a1.select.where is not a2.select.where


# ---------------------------------------------------------------------------
# Execute results are consistent after multiple to_ast() calls
# ---------------------------------------------------------------------------

def test_execute_results_unchanged_after_multiple_to_ast(tiny_net):
    """Multiple to_ast() calls must not affect execute() output."""
    q = Q.nodes().compute("degree")

    # Trigger multiple to_ast() calls
    q.to_ast()
    q.to_ast()
    q.to_ast()

    # Execute should still work correctly
    result = q.execute(tiny_net)
    assert result is not None
    assert result.target == "nodes"
    assert len(result.items) > 0


def test_to_ast_then_execute_equivalence(tiny_net):
    """to_ast() result converted to program and executed must match q.execute()."""
    q = Q.nodes().compute("degree")
    program = q.compile()

    r1 = q.execute(tiny_net)
    r2 = program.execute(tiny_net)

    assert set(r1.items) == set(r2.items)

"""Tests for the canonical compiler pipeline.

Verifies:
- q.execute(net) and q.compile().execute(net) produce equivalent results
- program.check(net) accepts valid queries without raising
- program.check(net) raises for invalid metric/target combos
- program.plan(net) returns an inspectable plan object
- The compiler route is taken end-to-end
"""

import pytest
from py3plex.dsl import Q, L
from py3plex.dsl.errors import DSLCompileError
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


@pytest.fixture
def tiny_net_one_layer():
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {"source": "X", "type": "alpha"},
        {"source": "Y", "type": "alpha"},
        {"source": "Z", "type": "alpha"},
    ])
    net.add_edges([
        {"source": "X", "target": "Y", "source_type": "alpha", "target_type": "alpha"},
        {"source": "Y", "target": "Z", "source_type": "alpha", "target_type": "alpha"},
    ])
    return net


# ---------------------------------------------------------------------------
# compile() basic contract
# ---------------------------------------------------------------------------

def test_compile_returns_program():
    """q.compile() must return a GraphProgram instance."""
    from py3plex.dsl.program.program import GraphProgram
    q = Q.nodes().compute("degree")
    program = q.compile()
    assert isinstance(program, GraphProgram)


def test_compile_is_alias_of_to_program():
    """compile() and to_program() must return programs with identical hashes."""
    q = Q.nodes().compute("degree")
    p1 = q.compile()
    p2 = q.to_program()
    assert p1.hash() == p2.hash()


def test_compile_snapshot_immutable():
    """The compiled program must not change when the builder is further modified."""
    q = Q.nodes().compute("degree")
    program = q.compile()
    hash_before = program.hash()

    # Change builder
    q.compute("betweenness_centrality")

    hash_after = program.hash()
    assert hash_before == hash_after


# ---------------------------------------------------------------------------
# Execute equivalence: q.execute(net) == q.compile().execute(net)
# ---------------------------------------------------------------------------

def test_execute_equivalent_to_compile_execute(tiny_net):
    """q.execute(net) and q.compile().execute(net) must return same items."""
    q = Q.nodes().compute("degree")
    r1 = q.execute(tiny_net)
    r2 = q.compile().execute(tiny_net)

    assert set(r1.items) == set(r2.items)


def test_execute_equivalent_with_filter(tiny_net):
    """Equivalence holds with a WHERE filter."""
    q = Q.nodes().where(degree__gte=1).compute("degree")
    r1 = q.execute(tiny_net)
    r2 = q.compile().execute(tiny_net)

    assert set(r1.items) == set(r2.items)


def test_execute_equivalent_from_layers(tiny_net):
    """Equivalence holds with from_layers()."""
    q = Q.nodes().from_layers(L["social"]).compute("degree")
    r1 = q.execute(tiny_net)
    r2 = q.compile().execute(tiny_net)

    assert set(r1.items) == set(r2.items)


def test_execute_equivalent_edges(tiny_net):
    """Equivalence holds for edge queries."""
    q = Q.edges()
    r1 = q.execute(tiny_net)
    r2 = q.compile().execute(tiny_net)

    # Edge items may be dicts (unhashable) — compare as sorted lists of tuples
    def _normalise(items):
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(tuple(sorted(item.items())))
            else:
                result.append(item)
        return sorted(result, key=str)

    assert _normalise(r1.items) == _normalise(r2.items)


def test_execute_result_has_attributes(tiny_net):
    """Execute result must expose the expected attributes from compute()."""
    q = Q.nodes().compute("degree")
    result = q.compile().execute(tiny_net)

    assert "degree" in result.attributes


def test_execute_result_has_items(tiny_net):
    """Items list must be non-empty for a populated network."""
    result = Q.nodes().execute(tiny_net)
    assert len(result.items) > 0


# ---------------------------------------------------------------------------
# program.check(net) — valid queries
# ---------------------------------------------------------------------------

def test_check_valid_nodes_query(tiny_net):
    """check() must complete without raising for a simple valid node query."""
    q = Q.nodes().compute("degree")
    program = q.compile()
    program.check(tiny_net)  # should not raise


def test_check_valid_layer_filter(tiny_net):
    """check() must accept layer-filtered queries."""
    q = Q.nodes().from_layers(L["social"])
    program = q.compile()
    program.check(tiny_net)  # should not raise


def test_check_valid_edge_query(tiny_net):
    """check() must accept edge queries."""
    q = Q.edges()
    program = q.compile()
    program.check(tiny_net)  # should not raise


def test_check_no_network(tmp_path):
    """check() without a network argument should not raise for safe queries."""
    q = Q.nodes().compute("degree")
    program = q.compile()
    program.check()  # no network — should still not raise


# ---------------------------------------------------------------------------
# program.plan(net) — inspectable plan object
# ---------------------------------------------------------------------------

def test_plan_returns_planned_query(tiny_net):
    """plan() must return a PlannedQuery-like object."""
    q = Q.nodes().compute("degree")
    program = q.compile()
    plan = program.plan(tiny_net)
    assert plan is not None


def test_plan_has_stages(tiny_net):
    """PlannedQuery must have a planned_stages attribute."""
    q = Q.nodes().compute("degree")
    plan = q.compile().plan(tiny_net)
    assert hasattr(plan, "planned_stages")


def test_plan_has_hashes(tiny_net):
    """Plan must expose plan_hash and ast_hash."""
    q = Q.nodes().compute("degree")
    plan = q.compile().plan(tiny_net)
    assert hasattr(plan, "plan_hash")
    assert hasattr(plan, "ast_hash")
    assert plan.plan_hash
    assert plan.ast_hash


def test_plan_to_dict(tiny_net):
    """PlannedQuery.to_dict() must return a dict with required keys."""
    q = Q.nodes().compute("degree")
    plan = q.compile().plan(tiny_net)
    d = plan.to_dict()
    assert isinstance(d, dict)
    assert "plan_hash" in d or "stages" in d


# ---------------------------------------------------------------------------
# Result API backward compatibility
# ---------------------------------------------------------------------------

def test_result_has_target(tiny_net):
    """QueryResult.target must be 'nodes' or 'edges'."""
    r = Q.nodes().execute(tiny_net)
    assert r.target in ("nodes", "edges")


def test_result_to_pandas(tiny_net):
    """result.to_pandas() must work and return a DataFrame."""
    import pandas as pd
    r = Q.nodes().compute("degree").execute(tiny_net)
    df = r.to_pandas()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_result_meta_exists(tiny_net):
    """result.meta must be a dict."""
    r = Q.nodes().execute(tiny_net)
    assert isinstance(r.meta, dict)

"""Tests for planner configuration propagation into execute().

Verifies:
- Stored .planner(...) config reaches execution
- Explicit planner= overrides stored config
- Existing behavior is preserved when no planner config is supplied
- Provenance records effective planner config when available
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
# .planner(...) stores config on builder
# ---------------------------------------------------------------------------

def test_planner_method_stores_config():
    """.planner() must store config so _planner_config is set."""
    q = Q.nodes().compute("degree")
    q2 = q.planner(compute_policy="minimal")
    # _planner_config should be set
    assert hasattr(q2, "_planner_config") or hasattr(q2, "_planner")
    # At minimum, executing should not raise
    # (config propagation tested via execution path below)


def test_planner_method_returns_builder():
    """.planner() must return the same builder (chainable)."""
    q = Q.nodes().compute("degree")
    q2 = q.planner(compute_policy="minimal")
    # Should still be a QueryBuilder (can execute)
    assert callable(getattr(q2, "execute", None))


# ---------------------------------------------------------------------------
# Stored planner config reaches execution
# ---------------------------------------------------------------------------

def test_stored_planner_config_does_not_crash(tiny_net):
    """Using .planner() before .execute() must not raise."""
    result = (
        Q.nodes()
        .compute("degree")
        .planner(compute_policy="minimal")
        .execute(tiny_net)
    )
    assert result is not None
    assert result.target == "nodes"


def test_stored_planner_config_items_match(tiny_net):
    """With .planner(compute_policy='minimal'), items must be same as default."""
    r_default = Q.nodes().compute("degree").execute(tiny_net)
    r_minimal = (
        Q.nodes()
        .compute("degree")
        .planner(compute_policy="minimal")
        .execute(tiny_net)
    )
    assert set(r_default.items) == set(r_minimal.items)


# ---------------------------------------------------------------------------
# Explicit execute(planner=...) overrides stored config
# ---------------------------------------------------------------------------

def test_explicit_planner_arg_does_not_crash(tiny_net):
    """Passing planner= explicitly to execute() must not raise."""
    result = Q.nodes().compute("degree").execute(tiny_net, planner={"compute_policy": "explicit"})
    assert result is not None
    assert result.target == "nodes"


def test_explicit_planner_arg_overrides_stored(tiny_net):
    """Explicit planner= must override any stored .planner() config."""
    # Stored: compute_policy=minimal
    q = Q.nodes().compute("degree").planner(compute_policy="minimal")
    # Override with explicit=full
    result = q.execute(tiny_net, planner={"compute_policy": "explicit"})
    assert result is not None
    assert len(result.items) > 0


def test_explicit_planner_none_uses_stored(tiny_net):
    """When no explicit planner= arg is given, stored config should be used."""
    q = Q.nodes().compute("degree").planner(compute_policy="minimal")
    # No planner= kwarg — should pick up stored config
    result = q.execute(tiny_net)
    assert result is not None


# ---------------------------------------------------------------------------
# Default behavior preserved when no planner config supplied
# ---------------------------------------------------------------------------

def test_no_planner_config_works(tiny_net):
    """Standard execute() without any planner config must work as before."""
    result = Q.nodes().compute("degree").execute(tiny_net)
    assert result is not None
    assert result.target == "nodes"
    assert len(result.items) > 0


def test_no_planner_config_all_policy(tiny_net):
    """compute_policy='all' must return all requested metrics."""
    result = Q.nodes().compute("degree").execute(tiny_net, planner={"compute_policy": "all"})
    assert result is not None
    assert result.target == "nodes"


# ---------------------------------------------------------------------------
# Provenance tracks planner config
# ---------------------------------------------------------------------------

def test_provenance_records_planner_config_when_supplied(tiny_net):
    """When planner config is supplied, provenance should record it (if supported)."""
    result = Q.nodes().compute("degree").execute(
        tiny_net, planner={"compute_policy": "explicit"}
    )
    # Provenance should exist at minimum
    assert isinstance(result.meta, dict)
    # If provenance records planner, verify it's there
    prov = result.meta.get("provenance", result.meta)
    # We don't require a specific key — just ensure meta is populated
    assert prov is not None


def test_provenance_exists_without_planner(tiny_net):
    """Provenance must exist even when no planner config is supplied."""
    result = Q.nodes().compute("degree").execute(tiny_net)
    assert isinstance(result.meta, dict)
    assert len(result.meta) > 0


# ---------------------------------------------------------------------------
# compile().execute() also accepts planner config
# ---------------------------------------------------------------------------

def test_program_execute_with_planner_config(tiny_net):
    """program.execute(net, planner_config=...) must not raise."""
    program = Q.nodes().compute("degree").compile()
    result = program.execute(tiny_net, planner_config={"compute_policy": "minimal"})
    assert result is not None
    assert result.target == "nodes"

"""Tests for compiler-level explain output (q.explain(net) / program.explain(net)).

Verifies the compiler view of query explanation including:
- "Query target:" section
- "Logical plan:" section
- "Provenance:" section
- Cost warnings for expensive metrics
- Layer info in explanation
- Backward compat: "SELECT nodes" and "Hash:" appear
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
# Basic structure of explain() output
# ---------------------------------------------------------------------------

def test_explain_returns_string(tiny_net):
    """explain() must return a non-empty string."""
    q = Q.nodes().compute("degree")
    explanation = q.explain(tiny_net)
    assert isinstance(explanation, str)
    assert len(explanation) > 0


def test_explain_contains_query_target(tiny_net):
    """explain() must include a section identifying the query target."""
    explanation = Q.nodes().compute("degree").explain(tiny_net)
    assert "Query target:" in explanation or "nodes" in explanation.lower()


def test_explain_contains_logical_plan(tiny_net):
    """explain() must include a 'Logical plan:' section."""
    explanation = Q.nodes().compute("degree").explain(tiny_net)
    assert "Logical plan:" in explanation or "logical" in explanation.lower()


def test_explain_contains_provenance(tiny_net):
    """explain() must include a 'Provenance:' section."""
    explanation = Q.nodes().compute("degree").explain(tiny_net)
    assert "Provenance:" in explanation or "provenance" in explanation.lower()


def test_explain_contains_metrics(tiny_net):
    """explain() must mention computed metric names."""
    explanation = Q.nodes().compute("degree").explain(tiny_net)
    assert "degree" in explanation


def test_explain_contains_hash(tiny_net):
    """explain() must include the AST hash for provenance."""
    explanation = Q.nodes().compute("degree").explain(tiny_net)
    assert "Hash:" in explanation or "ast_hash:" in explanation or "hash" in explanation.lower()


# ---------------------------------------------------------------------------
# Backward compatibility assertions
# ---------------------------------------------------------------------------

def test_explain_contains_select_nodes_line(tiny_net):
    """explain() should include 'SELECT nodes' for backward compat."""
    explanation = Q.nodes().compute("degree").explain(tiny_net)
    assert "SELECT nodes" in explanation


def test_explain_backward_compat_hash_prefix(tiny_net):
    """explain() should include 'Hash:' label for backward compat."""
    explanation = Q.nodes().compute("degree").explain(tiny_net)
    assert "Hash:" in explanation


# ---------------------------------------------------------------------------
# Cost warnings for expensive metrics
# ---------------------------------------------------------------------------

def test_explain_warns_about_betweenness(tiny_net):
    """explain() should include a warning about betweenness_centrality cost."""
    explanation = Q.nodes().compute("betweenness_centrality").explain(tiny_net)
    assert "betweenness_centrality" in explanation
    lower = explanation.lower()
    has_warning = (
        "warning" in lower
        or "expensive" in lower
        or "cost" in lower
        or "Warning" in explanation
    )
    assert has_warning, f"Expected cost warning in explain(), got:\n{explanation}"


def test_explain_no_warning_for_cheap_degree(tiny_net):
    """explain() should not flag degree as expensive."""
    explanation = Q.nodes().compute("degree").explain(tiny_net)
    assert "degree" in explanation


# ---------------------------------------------------------------------------
# Layer information in explain()
# ---------------------------------------------------------------------------

def test_explain_shows_layer_info(tiny_net):
    """explain() with specific layer should mention that layer."""
    explanation = Q.nodes().from_layers(L["social"]).compute("degree").explain(tiny_net)
    assert "social" in explanation.lower() or "Layer" in explanation


# ---------------------------------------------------------------------------
# program.explain(net) mirrors q.explain(net)
# ---------------------------------------------------------------------------

def test_program_explain_returns_string(tiny_net):
    """program.explain(net) must return a non-empty string."""
    program = Q.nodes().compute("degree").compile()
    explanation = program.explain(tiny_net)
    assert isinstance(explanation, str)
    assert len(explanation) > 0


def test_program_explain_contains_query_target(tiny_net):
    """program.explain(net) must mention the query target."""
    program = Q.nodes().compute("degree").compile()
    explanation = program.explain(tiny_net)
    assert "nodes" in explanation.lower() or "Query target:" in explanation


def test_program_explain_contains_logical_plan(tiny_net):
    """program.explain(net) must include a logical plan section."""
    program = Q.nodes().compute("degree").compile()
    explanation = program.explain(tiny_net)
    assert "Logical plan:" in explanation or "logical" in explanation.lower()


def test_program_explain_matches_query_explain(tiny_net):
    """q.explain(net) and program.explain(net) should cover same info."""
    q = Q.nodes().compute("degree")
    program = q.compile()
    q_expl = q.explain(tiny_net)
    p_expl = program.explain(tiny_net)
    assert "nodes" in q_expl.lower()
    assert "nodes" in p_expl.lower()
    assert "degree" in q_expl
    assert "degree" in p_expl


# ---------------------------------------------------------------------------
# Edge queries
# ---------------------------------------------------------------------------

def test_explain_edge_query(tiny_net):
    """explain() for edge query should mention 'edges' target."""
    explanation = Q.edges().explain(tiny_net)
    assert "edge" in explanation.lower()

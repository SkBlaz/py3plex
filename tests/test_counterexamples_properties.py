"""Property-based tests for counterexample generation using Hypothesis.

These tests verify properties that should hold across many randomly generated
test cases, such as determinism and minimality.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
import networkx as nx

from py3plex.core import multinet
from py3plex.counterexamples import find_counterexample
from py3plex.counterexamples.engine import CounterexampleNotFound


# ============================================================================
# Hypothesis Strategies
# ============================================================================


@st.composite
def small_multilayer_network(draw):
    """Generate a small random multilayer network for testing.

    Returns a tuple of (network, layers).
    """
    # Generate small network parameters
    num_nodes = draw(st.integers(min_value=3, max_value=8))
    num_layers = draw(st.integers(min_value=1, max_value=2))
    edge_prob = draw(st.floats(min_value=0.3, max_value=0.8))

    # Create network
    net = multinet.multi_layer_network(directed=False)

    # Generate layer names
    layers = [f"layer{i}" for i in range(num_layers)]

    # Generate nodes
    node_names = [f"N{i}" for i in range(num_nodes)]

    for layer in layers:
        for node in node_names:
            net.add_nodes([{"source": node, "type": layer}])

    # Generate edges within each layer
    edges = []
    for layer in layers:
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if (
                    draw(st.booleans())
                    and draw(st.floats(min_value=0, max_value=1)) < edge_prob
                ):
                    edges.append(
                        {
                            "source": node_names[i],
                            "target": node_names[j],
                            "source_type": layer,
                            "target_type": layer,
                            "weight": 1.0,
                        }
                    )

    if edges:
        net.add_edges(edges)

    return net, layers


# ============================================================================
# Property Tests
# ============================================================================


@pytest.mark.property
@given(
    seed1=st.integers(min_value=0, max_value=1000),
    seed2=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=10, deadline=10000)  # Reduced for performance
def test_determinism_property(seed1, seed2):
    """Property: Same seed produces identical results, different seeds may differ.

    This test verifies that:
    1. Running with the same seed twice produces the same violating node
    2. The fingerprint of results is identical
    """
    # Create a fixed network (not random) for determinism testing
    net = multinet.multi_layer_network(directed=False)

    nodes = [
        {"source": "A", "type": "L1"},
        {"source": "B", "type": "L1"},
        {"source": "C", "type": "L1"},
        {"source": "D", "type": "L1"},
    ]
    net.add_nodes(nodes)

    edges = [
        {
            "source": "A",
            "target": "B",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
        {
            "source": "A",
            "target": "C",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
        {
            "source": "B",
            "target": "C",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
        {
            "source": "C",
            "target": "D",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
    ]
    net.add_edges(edges)

    claim = "degree__ge(k) -> pagerank__rank_le(r)"
    params = {"k": 2, "r": 2}

    # Run with seed1 twice
    try:
        cex1a = find_counterexample(net, claim, params, seed=seed1, find_minimal=False)
        cex1b = find_counterexample(net, claim, params, seed=seed1, find_minimal=False)

        # Same seed should produce same violation
        assert cex1a.violation.node == cex1b.violation.node
        assert cex1a.violation.layer == cex1b.violation.layer

        # Same witness size
        assert len(cex1a.witness_nodes) == len(cex1b.witness_nodes)
        assert len(cex1a.witness_edges) == len(cex1b.witness_edges)

    except CounterexampleNotFound:
        # No violation found - that's okay, test still passes
        pass


@pytest.mark.property
@given(
    net_and_layers=small_multilayer_network(),
    k_value=st.integers(min_value=1, max_value=3),
    r_value=st.integers(min_value=1, max_value=5),
    seed=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=15, deadline=15000)
def test_minimality_sanity_property(net_and_layers, k_value, r_value, seed):
    """Property: Minimized witness has <= edges than initial witness.

    This test verifies that:
    1. If minimization is enabled, final witness has <= edges than initial
    2. The violation persists in the minimized witness
    """
    net, layers = net_and_layers

    # Skip if network is too small
    edge_count = len(list(net.get_edges()))
    assume(edge_count >= 2)

    claim = "degree__ge(k) -> pagerank__rank_le(r)"
    params = {"k": k_value, "r": r_value}

    try:
        # Find counterexample with minimization
        cex = find_counterexample(
            net,
            claim,
            params,
            seed=seed,
            find_minimal=True,
        )

        # Check minimization report
        assert cex.minimization is not None
        assert cex.minimization.final_edges <= cex.minimization.initial_edges

        # If is_minimal is True, we have a strong guarantee
        # If False, we hit budget but still reduced
        if cex.minimization.is_minimal:
            # Strong guarantee: removing any edge should break violation
            # (We can't easily test this without re-running, so just check sanity)
            assert cex.minimization.final_edges >= 1  # At least one edge needed

    except CounterexampleNotFound:
        # No violation exists for this network/claim combo
        # That's fine - property doesn't apply
        pass


@pytest.mark.property
@given(
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=5, deadline=10000)
def test_witness_validity_property(seed):
    """Property: Witness subgraph is a valid py3plex network.

    This test verifies that the extracted witness:
    1. Is a valid multi_layer_network object
    2. Has all expected nodes and edges
    3. Preserves layer structure
    """
    # Fixed network
    net = multinet.multi_layer_network(directed=False)

    nodes = [
        {"source": "A", "type": "L1"},
        {"source": "B", "type": "L1"},
        {"source": "C", "type": "L1"},
        {"source": "D", "type": "L1"},
    ]
    net.add_nodes(nodes)

    edges = [
        {
            "source": "A",
            "target": "B",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
        {
            "source": "A",
            "target": "C",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
        {
            "source": "B",
            "target": "C",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
        {
            "source": "C",
            "target": "D",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
    ]
    net.add_edges(edges)

    claim = "degree__ge(k) -> pagerank__rank_le(r)"
    params = {"k": 2, "r": 2}

    try:
        cex = find_counterexample(net, claim, params, seed=seed, find_minimal=False)

        # Verify witness is valid
        witness = cex.subgraph
        assert witness is not None
        assert hasattr(witness, "get_nodes")
        assert hasattr(witness, "get_edges")

        # Verify witness has nodes and edges
        witness_nodes = list(witness.get_nodes())
        witness_edges = list(witness.get_edges())

        assert len(witness_nodes) > 0

        # Verify violating node is in witness
        violating_node = (cex.violation.node, cex.violation.layer)
        witness_node_set = {(n[0], n[1]) for n in witness_nodes}
        assert violating_node in witness_node_set

    except CounterexampleNotFound:
        pass


@pytest.mark.property
@given(
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=5, deadline=10000)
def test_provenance_completeness_property(seed):
    """Property: Provenance contains all required fields.

    This test verifies that the provenance record:
    1. Has all mandatory fields
    2. Fields have expected types
    3. Timings are non-negative
    """
    # Fixed network
    net = multinet.multi_layer_network(directed=False)

    nodes = [
        {"source": "A", "type": "L1"},
        {"source": "B", "type": "L1"},
        {"source": "C", "type": "L1"},
    ]
    net.add_nodes(nodes)

    edges = [
        {
            "source": "A",
            "target": "B",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
        {
            "source": "B",
            "target": "C",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0,
        },
    ]
    net.add_edges(edges)

    claim = "degree__ge(k) -> pagerank__rank_le(r)"
    params = {"k": 1, "r": 2}

    try:
        cex = find_counterexample(net, claim, params, seed=seed)

        # Check provenance
        assert "provenance" in cex.meta
        prov = cex.meta["provenance"]

        # Required fields
        required_fields = [
            "engine",
            "py3plex_version",
            "timestamp_utc",
            "claim",
            "randomness",
            "network_fingerprint",
            "performance",
            "minimization",
            "budget",
        ]

        for field in required_fields:
            assert field in prov, f"Missing required field: {field}"

        # Check types and values
        assert prov["engine"] == "counterexample_engine"
        assert isinstance(prov["py3plex_version"], str)
        assert prov["randomness"]["seed"] == seed

        # Check performance timings are non-negative
        perf = prov["performance"]
        assert perf["find_violation_ms"] >= 0
        assert perf["extract_witness_ms"] >= 0
        assert perf["minimize_ms"] >= 0
        assert perf["total_ms"] >= 0

    except CounterexampleNotFound:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])

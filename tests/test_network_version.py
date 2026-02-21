"""Tests for the network_version mutation counter in multi_layer_network.

Verifies:
- Fresh network starts at version 0.
- add_nodes increments version by exactly 1.
- add_edges increments version by exactly 1 (even when it adds implicit nodes).
- Multiple mutation calls increment monotonically.
- load_network increments version by exactly 1.
- Non-mutating calls (get_nodes, get_edges) do not change the version.
- Provenance captures network_version correctly.
"""

import os
import tempfile

import pytest

from py3plex.core.multinet import multi_layer_network


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _simple_net() -> multi_layer_network:
    """Return a fresh empty multilayer network."""
    return multi_layer_network(network_type="multilayer", directed=False)


def _net_with_nodes() -> multi_layer_network:
    net = _simple_net()
    net.add_nodes([
        {"source": "A", "type": "layer1"},
        {"source": "B", "type": "layer1"},
    ])
    return net


# ---------------------------------------------------------------------------
# Basic versioning tests
# ---------------------------------------------------------------------------

class TestNetworkVersionBasics:
    def test_initial_version_is_zero(self):
        net = _simple_net()
        assert net.network_version == 0

    def test_network_version_property_accessible(self):
        net = _simple_net()
        # Must be an int
        assert isinstance(net.network_version, int)

    def test_add_nodes_increments_by_one(self):
        net = _simple_net()
        before = net.network_version
        net.add_nodes([{"source": "A", "type": "layer1"}])
        assert net.network_version == before + 1

    def test_add_edges_increments_by_one(self):
        net = _net_with_nodes()
        before = net.network_version
        net.add_edges([
            {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1"}
        ])
        assert net.network_version == before + 1

    def test_add_edges_with_new_nodes_increments_by_one(self):
        """add_edges that introduces new nodes must still bump version exactly once."""
        net = _simple_net()
        before = net.network_version
        net.add_edges([
            {"source": "X", "target": "Y", "source_type": "layer1", "target_type": "layer1"}
        ])
        # Must be exactly 1, not 2 (no double-bump from internal node creation)
        assert net.network_version == before + 1

    def test_remove_nodes_increments_by_one(self):
        net = _net_with_nodes()
        before = net.network_version
        net.remove_nodes([{"source": "A", "type": "layer1"}])
        assert net.network_version == before + 1

    def test_remove_edges_increments_by_one(self):
        net = _net_with_nodes()
        net.add_edges([
            {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1"}
        ])
        before = net.network_version
        net.remove_edges(
            [{"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1"}],
            input_type="dict",
        )
        assert net.network_version == before + 1

    def test_multiple_mutations_monotonically_increasing(self):
        net = _simple_net()
        versions = [net.network_version]
        net.add_nodes([{"source": "A", "type": "layer1"}])
        versions.append(net.network_version)
        net.add_nodes([{"source": "B", "type": "layer1"}])
        versions.append(net.network_version)
        net.add_edges([
            {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1"}
        ])
        versions.append(net.network_version)

        # Check strictly increasing
        for i in range(1, len(versions)):
            assert versions[i] > versions[i - 1]

    def test_non_mutating_get_nodes_does_not_change_version(self):
        net = _net_with_nodes()
        v_before = net.network_version
        _ = list(net.get_nodes())
        assert net.network_version == v_before

    def test_non_mutating_get_edges_does_not_change_version(self):
        net = _net_with_nodes()
        net.add_edges([
            {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1"}
        ])
        v_before = net.network_version
        _ = list(net.get_edges())
        assert net.network_version == v_before


# ---------------------------------------------------------------------------
# load_network test
# ---------------------------------------------------------------------------

class TestNetworkVersionLoadNetwork:
    def test_load_network_increments_by_one(self, tmp_path):
        """load_network() must bump version exactly once."""
        # Create a minimal multiedgelist file
        edge_file = tmp_path / "test_net.tsv"
        edge_file.write_text("A layer1 B layer1 1\n")

        net = _simple_net()
        before = net.network_version
        net.load_network(str(edge_file), input_type="multiedgelist")
        assert net.network_version == before + 1

    def test_version_after_load_is_one(self, tmp_path):
        edge_file = tmp_path / "test_net2.tsv"
        edge_file.write_text("X layer1 Y layer1 1\n")

        net = _simple_net()
        net.load_network(str(edge_file), input_type="multiedgelist")
        assert net.network_version == 1


# ---------------------------------------------------------------------------
# Provenance integration test
# ---------------------------------------------------------------------------

class TestNetworkVersionInProvenance:
    def test_provenance_includes_network_version(self):
        """Provenance built after mutations must contain correct network_version."""
        from py3plex.dsl.provenance import ProvenanceBuilder

        net = _simple_net()
        net.add_nodes([{"source": "A", "type": "layer1"}])
        net.add_edges([
            {"source": "A", "target": "A", "source_type": "layer1", "target_type": "layer1"}
        ])
        expected_version = net.network_version

        builder = ProvenanceBuilder(engine="test")
        builder.set_network(net)
        prov = builder.build()

        # build() returns a dict
        assert prov["network_version"] == expected_version

    def test_provenance_network_version_starts_at_zero_for_empty_net(self):
        from py3plex.dsl.provenance import ProvenanceBuilder

        net = _simple_net()
        builder = ProvenanceBuilder(engine="test")
        builder.set_network(net)
        prov = builder.build()

        # build() returns a dict; freshly constructed network has version 0
        assert prov["network_version"] == 0

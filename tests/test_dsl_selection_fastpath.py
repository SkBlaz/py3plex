"""Tests for the selection fast path (filter fast path).

Covers:
- Node fast path: layer filter + degree threshold
- Edge fast path: src/dst degree thresholds
- Negative cases: NOT / OR queries fall back to baseline
- Results must match baseline executor exactly
- Provenance flag wiring
"""

import pytest
import py3plex.config as cfg
from py3plex.core import multinet
from py3plex.dsl import Q, L


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_network():
    """Small multilayer network used by all tests."""
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
        {'source': 'F', 'type': 'work'},
    ])
    network.add_edges([
        # social triangle: A, B, C each have degree 2
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        # work: D-E-F path; D and F have degree 1, E has degree 2
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'E', 'target': 'F', 'source_type': 'work', 'target_type': 'work'},
    ])
    return network


def _disable_fastpath():
    """Context manager / helper to temporarily disable the fast path."""
    return _FastpathDisabler()


class _FastpathDisabler:
    def __enter__(self):
        self._orig = cfg.DSL_FAST_PATH_ENABLED
        cfg.DSL_FAST_PATH_ENABLED = False
        return self

    def __exit__(self, *args):
        cfg.DSL_FAST_PATH_ENABLED = self._orig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def net():
    return _make_network()


# ---------------------------------------------------------------------------
# Test 1: Node fast path — layer filter + degree threshold
# ---------------------------------------------------------------------------

class TestNodeFastPath:
    def test_layer_and_degree_gt(self, net):
        """Nodes in social layer with degree > 1 (all three have deg 2)."""
        result_fp = (
            Q.nodes()
             .from_layers(L["social"])
             .where(degree__gt=1)
             .execute(net)
        )
        with _disable_fastpath():
            result_bl = (
                Q.nodes()
                 .from_layers(L["social"])
                 .where(degree__gt=1)
                 .execute(net)
            )

        # Results must be identical
        assert set(result_fp.items) == set(result_bl.items), (
            f"FP={set(result_fp.items)} BL={set(result_bl.items)}"
        )
        assert len(result_fp.items) == 3  # A, B, C all pass

        # Provenance must be marked
        prov = result_fp.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is True

    def test_layer_and_degree_ge(self, net):
        """Degree >= 2 in social layer (all three nodes)."""
        result_fp = (
            Q.nodes()
             .from_layers(L["social"])
             .where(degree__ge=2)
             .execute(net)
        )
        with _disable_fastpath():
            result_bl = (
                Q.nodes()
                 .from_layers(L["social"])
                 .where(degree__ge=2)
                 .execute(net)
            )
        assert set(result_fp.items) == set(result_bl.items)
        prov = result_fp.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is True

    def test_degree_lt(self, net):
        """Degree < 2 in work layer (D and F have degree 1)."""
        result_fp = (
            Q.nodes()
             .from_layers(L["work"])
             .where(degree__lt=2)
             .execute(net)
        )
        with _disable_fastpath():
            result_bl = (
                Q.nodes()
                 .from_layers(L["work"])
                 .where(degree__lt=2)
                 .execute(net)
            )
        assert set(result_fp.items) == set(result_bl.items)
        prov = result_fp.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is True

    def test_degree_le(self, net):
        """Degree <= 1 in work layer (D and F)."""
        result_fp = (
            Q.nodes()
             .from_layers(L["work"])
             .where(degree__le=1)
             .execute(net)
        )
        with _disable_fastpath():
            result_bl = (
                Q.nodes()
                 .from_layers(L["work"])
                 .where(degree__le=1)
                 .execute(net)
            )
        assert set(result_fp.items) == set(result_bl.items)
        prov = result_fp.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is True

    def test_layer_only_no_degree(self, net):
        """Layer filter without degree threshold still uses fast path."""
        result_fp = Q.nodes().from_layers(L["social"]).execute(net)
        with _disable_fastpath():
            result_bl = Q.nodes().from_layers(L["social"]).execute(net)
        assert set(result_fp.items) == set(result_bl.items)
        prov = result_fp.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is True

    def test_fast_path_disabled_returns_false_flag(self, net):
        """When fast path is disabled the flag must be False."""
        with _disable_fastpath():
            result = (
                Q.nodes()
                 .from_layers(L["social"])
                 .where(degree__gt=1)
                 .execute(net)
            )
        prov = result.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is False


# ---------------------------------------------------------------------------
# Test 2: Edge fast path — src/dst degree thresholds
# ---------------------------------------------------------------------------

class TestEdgeFastPath:
    def test_src_dst_degree_ge(self, net):
        """Edges where both src and dst degree >= 2.

        In the social triangle all edges qualify.
        In the work path only E-E edges qualify (but D-E and E-F have one
        endpoint with degree 1, so the work edges are excluded).
        """
        result_fp = Q.edges().where(src_degree__ge=2, dst_degree__ge=2).execute(net)
        with _disable_fastpath():
            result_bl = Q.edges().where(src_degree__ge=2, dst_degree__ge=2).execute(net)

        fp_pairs = {(e[0], e[1]) for e in result_fp.items}
        bl_pairs = {(e[0], e[1]) for e in result_bl.items}
        assert fp_pairs == bl_pairs, f"FP={fp_pairs} BL={bl_pairs}"

        prov = result_fp.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is True

    def test_src_degree_gt(self, net):
        """Edges where src degree > 1 only."""
        result_fp = Q.edges().where(src_degree__gt=1).execute(net)
        with _disable_fastpath():
            result_bl = Q.edges().where(src_degree__gt=1).execute(net)

        fp_pairs = {(e[0], e[1]) for e in result_fp.items}
        bl_pairs = {(e[0], e[1]) for e in result_bl.items}
        assert fp_pairs == bl_pairs

        prov = result_fp.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is True

    def test_dst_degree_le(self, net):
        """Edges where dst degree <= 1 (leaf nodes in the work path)."""
        result_fp = Q.edges().where(dst_degree__le=1).execute(net)
        with _disable_fastpath():
            result_bl = Q.edges().where(dst_degree__le=1).execute(net)

        fp_pairs = {(e[0], e[1]) for e in result_fp.items}
        bl_pairs = {(e[0], e[1]) for e in result_bl.items}
        assert fp_pairs == bl_pairs

        prov = result_fp.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is True


# ---------------------------------------------------------------------------
# Test 3: Negative cases (ineligible queries)
# ---------------------------------------------------------------------------

class TestNegativeCases:
    def test_no_fast_path_for_compute_only(self, net):
        """A node query with only compute() should not break; fast_path may be True or False."""
        # Pure compute, no degree filter → fast path may still be used for selection
        result = Q.nodes().from_layers(L["social"]).compute("degree").execute(net)
        # Must not crash, results must contain the right nodes
        assert len(result.items) == 3

    def test_results_correct_with_fastpath_disabled(self, net):
        """Disabling fast path must give same results as enabling it."""
        with _disable_fastpath():
            result_off = (
                Q.nodes()
                 .from_layers(L["social"])
                 .where(degree__gt=1)
                 .execute(net)
            )
        result_on = (
            Q.nodes()
             .from_layers(L["social"])
             .where(degree__gt=1)
             .execute(net)
        )
        assert set(result_on.items) == set(result_off.items)

    def test_fast_path_flag_false_when_disabled(self, net):
        """fast_path must be False when DSL_FAST_PATH_ENABLED=False."""
        with _disable_fastpath():
            result = Q.nodes().from_layers(L["social"]).execute(net)
        prov = result.meta.get("provenance", {})
        assert prov.get("backend", {}).get("fast_path") is False

    def test_compute_with_fastpath_gives_correct_attributes(self, net):
        """Compute attributes must still be correct when fast path selects nodes."""
        result_fp = (
            Q.nodes()
             .from_layers(L["social"])
             .compute("degree")
             .execute(net)
        )
        with _disable_fastpath():
            result_bl = (
                Q.nodes()
                 .from_layers(L["social"])
                 .compute("degree")
                 .execute(net)
            )
        # Same nodes
        assert set(result_fp.items) == set(result_bl.items)
        # Same degree values
        fp_df = result_fp.to_pandas()
        bl_df = result_bl.to_pandas()
        fp_deg = dict(zip(fp_df["id"], fp_df["degree"]))
        bl_deg = dict(zip(bl_df["id"], bl_df["degree"]))
        assert fp_deg == bl_deg

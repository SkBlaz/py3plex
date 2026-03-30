"""Unit tests for py3plex.sensitivity.perturbations."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "py3plex"
    / "sensitivity"
    / "perturbations.py"
)

_SPEC = importlib.util.spec_from_file_location("py3plex_sensitivity_perturbations", MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
perturbations = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(perturbations)


class FakeNetwork:
    """Small multilayer-like test network for perturbation unit tests."""

    def __init__(self, edges):
        # key: (src, src_layer, dst, dst_layer), value: weight
        self._edges = dict.fromkeys(edges, 1.0)

    def get_layers(self):
        layers = {edge[1] for edge in self._edges}.union({edge[3] for edge in self._edges})
        return sorted(layers)

    def get_edges(self, data=False):
        if not data:
            return list(self._edges.keys())
        result = []
        for src, src_layer, dst, dst_layer in self._edges:
            payload = {"weight": self._edges[(src, src_layer, dst, dst_layer)]}
            result.append(((src, src_layer), (dst, dst_layer), payload))
        return result

    def remove_edge(self, edge):
        del self._edges[tuple(edge)]

    def add_edge(self, src, dst, src_layer, dst_layer, weight=1.0):
        self._edges[(src, src_layer, dst, dst_layer)] = weight


def make_network():
    """Create a network with two layers and enough edges for perturbation."""
    return FakeNetwork(
        [
            ("A", "social", "B", "social"),
            ("B", "social", "C", "social"),
            ("C", "social", "D", "social"),
            ("D", "social", "A", "social"),
            ("A", "work", "B", "work"),
            ("B", "work", "C", "work"),
            ("C", "work", "D", "work"),
            ("D", "work", "A", "work"),
        ]
    )


class TestEdgeDrop:
    def test_edge_drop_zero_fraction_returns_unchanged(self):
        network = make_network()
        before = set(network.get_edges(data=False))

        perturbed = perturbations.edge_drop(network, fraction=0.0, seed=42, layer_aware=True)

        assert set(perturbed.get_edges(data=False)) == before
        assert set(network.get_edges(data=False)) == before
        assert perturbed is not network

    @pytest.mark.parametrize("fraction", [-0.1, 1.1])
    def test_edge_drop_fraction_bounds(self, fraction):
        with pytest.raises(ValueError, match="Fraction must be in \\[0, 1\\]"):
            perturbations.edge_drop(make_network(), fraction=fraction, seed=42)

    def test_edge_drop_reproducible_with_seed(self):
        network = make_network()
        p1 = perturbations.edge_drop(network, fraction=0.5, seed=42, layer_aware=True)
        p2 = perturbations.edge_drop(network, fraction=0.5, seed=42, layer_aware=True)

        assert set(p1.get_edges(data=False)) == set(p2.get_edges(data=False))

    def test_edge_drop_layer_aware_respects_layer_counts(self):
        network = make_network()
        perturbed = perturbations.edge_drop(network, fraction=0.5, seed=42, layer_aware=True)

        social_edges = [e for e in perturbed.get_edges(data=False) if e[1] == "social" and e[3] == "social"]
        work_edges = [e for e in perturbed.get_edges(data=False) if e[1] == "work" and e[3] == "work"]

        assert len(social_edges) == 2
        assert len(work_edges) == 2
        assert len(perturbed.get_edges(data=False)) == 4

    def test_edge_drop_different_seeds_produce_different_drops(self):
        network = make_network()
        p1 = perturbations.edge_drop(network, fraction=0.5, seed=1, layer_aware=False)
        p2 = perturbations.edge_drop(network, fraction=0.5, seed=2, layer_aware=False)

        assert set(p1.get_edges(data=False)) != set(p2.get_edges(data=False))


class TestDegreePreservingRewire:
    @pytest.mark.parametrize("fraction", [-0.1, 1.1])
    def test_degree_preserving_rewire_fraction_bounds(self, fraction):
        with pytest.raises(ValueError, match="Fraction must be in \\[0, 1\\]"):
            perturbations.degree_preserving_rewire(make_network(), fraction=fraction, seed=42)

    def test_degree_preserving_rewire_returns_network_with_same_edge_count(self):
        network = make_network()
        before_edges = network.get_edges(data=False)

        perturbed = perturbations.degree_preserving_rewire(
            network, fraction=0.5, seed=42, max_attempts=50, layer_aware=True
        )

        assert len(perturbed.get_edges(data=False)) == len(before_edges)
        assert {edge[1] for edge in perturbed.get_edges(data=False)} == {"social", "work"}

    def test_degree_preserving_rewire_reproducible(self):
        network = make_network()
        p1 = perturbations.degree_preserving_rewire(
            network, fraction=0.5, seed=42, max_attempts=50, layer_aware=True
        )
        p2 = perturbations.degree_preserving_rewire(
            network, fraction=0.5, seed=42, max_attempts=50, layer_aware=True
        )

        assert set(p1.get_edges(data=False)) == set(p2.get_edges(data=False))


class TestApplyPerturbation:
    def test_apply_perturbation_edge_drop_dispatch(self):
        network = make_network()
        perturbed = perturbations.apply_perturbation(
            network, method="edge_drop", strength=0.5, seed=42, layer_aware=True
        )

        assert len(perturbed.get_edges(data=False)) == 4

    def test_apply_perturbation_degree_preserving_dispatch(self):
        network = make_network()
        perturbed = perturbations.apply_perturbation(
            network,
            method="degree_preserving_rewire",
            strength=0.5,
            seed=42,
            layer_aware=True,
            max_attempts=50,
        )

        assert len(perturbed.get_edges(data=False)) == len(network.get_edges(data=False))

    def test_apply_perturbation_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unknown perturbation method"):
            perturbations.apply_perturbation(make_network(), method="does_not_exist", strength=0.2, seed=42)

    def test_apply_perturbation_forwards_kwargs(self, monkeypatch):
        captured = {}

        def fake_edge_drop(network, fraction, seed=None, layer_aware=True):
            captured["fraction"] = fraction
            captured["seed"] = seed
            captured["layer_aware"] = layer_aware
            return network

        monkeypatch.setattr(perturbations, "edge_drop", fake_edge_drop)

        net = make_network()
        out = perturbations.apply_perturbation(
            net, method="edge_drop", strength=0.3, seed=7, layer_aware=False
        )

        assert out is net
        assert captured == {"fraction": 0.3, "seed": 7, "layer_aware": False}

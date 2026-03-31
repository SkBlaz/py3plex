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

_SPEC = importlib.util.spec_from_file_location("perturbations_module", MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
perturbations = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(perturbations)

# NOTE: The package-level import path (`from py3plex.sensitivity import perturbations`)
# is intentionally avoided here because importing `py3plex` triggers optional heavy
# dependencies (e.g., matplotlib) that are not required for testing this module.
# We load only the target module directly to keep the unit tests isolated.
_EDGE_TUPLE_SRC_LAYER_INDEX = 1
_EDGE_TUPLE_DST_LAYER_INDEX = 3


class FakeNetwork:
    """Minimal multilayer-like network adapter for perturbation tests.

    This fake implements only the methods used by perturbation helpers:
    ``get_layers()``, ``get_edges(data=...)``, ``remove_edge(...)``, and
    ``add_edge(...)``. It stores edges in canonical
    ``(src, src_layer, dst, dst_layer)`` tuple form and supports ``deepcopy``.
    """

    def __init__(self, edges):
        # key: (src, src_layer, dst, dst_layer), value: weight
        self._edges = dict.fromkeys(edges, 1.0)

    def get_layers(self):
        layers = {edge[_EDGE_TUPLE_SRC_LAYER_INDEX] for edge in self._edges}.union(
            {edge[_EDGE_TUPLE_DST_LAYER_INDEX] for edge in self._edges}
        )
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

    def __deepcopy__(self, memo):
        copied = type(self)([])
        copied._edges = self._edges.copy()
        return copied


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


def make_large_network():
    """Create a larger network to reduce random-collision risk in seed tests."""
    edges = []
    for layer in ("social", "work"):
        for i in range(10):
            src = f"N{i}"
            dst = f"N{(i + 1) % 10}"
            edges.append((src, layer, dst, layer))
    return FakeNetwork(edges)


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

        social_edges = [
            e
            for e in perturbed.get_edges(data=False)
            if e[_EDGE_TUPLE_SRC_LAYER_INDEX] == "social"
            and e[_EDGE_TUPLE_DST_LAYER_INDEX] == "social"
        ]
        work_edges = [
            e
            for e in perturbed.get_edges(data=False)
            if e[_EDGE_TUPLE_SRC_LAYER_INDEX] == "work"
            and e[_EDGE_TUPLE_DST_LAYER_INDEX] == "work"
        ]

        assert len(social_edges) == 2
        assert len(work_edges) == 2
        assert len(perturbed.get_edges(data=False)) == 4

    def test_edge_drop_different_seeds_produce_different_drops(self):
        network = make_large_network()
        p1 = perturbations.edge_drop(network, fraction=0.3, seed=1, layer_aware=False)
        p2 = perturbations.edge_drop(network, fraction=0.3, seed=2, layer_aware=False)

        assert set(p1.get_edges(data=False)) != set(p2.get_edges(data=False))

    def test_edge_drop_fraction_one_drops_all_edges(self):
        network = make_network()
        perturbed = perturbations.edge_drop(network, fraction=1.0, seed=42, layer_aware=False)

        assert perturbed.get_edges(data=False) == []


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
        assert {
            edge[_EDGE_TUPLE_SRC_LAYER_INDEX] for edge in perturbed.get_edges(data=False)
        } == {"social", "work"}

    def test_degree_preserving_rewire_reproducible(self):
        network = make_network()
        p1 = perturbations.degree_preserving_rewire(
            network, fraction=0.5, seed=42, max_attempts=50, layer_aware=True
        )
        p2 = perturbations.degree_preserving_rewire(
            network, fraction=0.5, seed=42, max_attempts=50, layer_aware=True
        )

        assert set(p1.get_edges(data=False)) == set(p2.get_edges(data=False))

    def test_degree_preserving_rewire_fraction_zero_keeps_edges(self):
        network = make_network()
        before = set(network.get_edges(data=False))

        perturbed = perturbations.degree_preserving_rewire(
            network, fraction=0.0, seed=42, max_attempts=50, layer_aware=True
        )

        assert set(perturbed.get_edges(data=False)) == before


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

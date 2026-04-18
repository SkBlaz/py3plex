"""Tests for py3plex.algorithms.requirements_registry."""

from __future__ import annotations

from types import ModuleType

from py3plex.algorithms import requirements_registry as rr
from py3plex.requirements import AlgoRequirements, NetworkCapabilities


def test_global_registry_has_known_algorithms() -> None:
    assert rr.is_algorithm_registered("pagerank")
    assert rr.get_algorithm_requirements("pagerank") is not None


def test_algorithm_registry_register_function_attaches_requirements() -> None:
    registry = rr.AlgorithmRegistry()
    req = rr.GENERAL_MULTILAYER_REQS

    def algo():
        return None

    registry.register_function(algo, req)

    assert registry.get_by_function(algo) == req
    assert getattr(algo, "requirements") == req


def test_algorithm_registry_list_algorithms_can_filter_by_compatibility() -> None:
    registry = rr.AlgorithmRegistry()
    req = AlgoRequirements(
        allowed_modes=("single",),
        replica_model=("none",),
        interlayer_coupling=("none",),
        requires_edge_weights=False,
        requires_positive_weights=False,
        supports_directed=True,
        supports_undirected=True,
        uses_randomness=False,
        requires_seed_for_repro=False,
        supports_uq=False,
    )
    registry.register("only_single", req)

    class _SingleNet:
        def capabilities(self):
            return NetworkCapabilities(
                mode="single",
                replica_model="none",
                interlayer_coupling="none",
                directed=False,
                weighted=False,
            )

    class _MultilayerNet:
        def capabilities(self):
            return NetworkCapabilities(
                mode="multilayer",
                replica_model="partial",
                interlayer_coupling="explicit_edges",
                directed=False,
                weighted=False,
            )

    assert "only_single" in registry.list_algorithms(_SingleNet())
    assert "only_single" not in registry.list_algorithms(_MultilayerNet())


def test_validate_module_reports_unregistered_functions() -> None:
    module = ModuleType("dummy_module")

    def public_algorithm():
        return 1

    def _private_algorithm():
        return 2

    module.public_algorithm = public_algorithm
    module._private_algorithm = _private_algorithm

    valid, unregistered = rr.validate_module(module, strict=False)
    assert valid is False
    assert "public_algorithm" in unregistered
    assert "_private_algorithm" not in unregistered

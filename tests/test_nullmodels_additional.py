"""Additional tests for py3plex.nullmodels."""

import pytest

from py3plex.core import multinet
from py3plex.nullmodels.executor import generate_null_model
from py3plex.nullmodels.models import ModelRegistry, _copy_network, model_registry


@pytest.fixture
def simple_network():
    """Create a tiny multilayer network for executor tests."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["A", "L1", "B", "L1", 1.0],
            ["B", "L1", "C", "L1", 1.0],
        ],
        input_type="list",
    )
    return net


def test_copy_network_prefers_native_copy_method():
    """_copy_network should delegate to network.copy when available."""

    class Dummy:
        def __init__(self):
            self.called = False

        def copy(self):
            self.called = True
            return "copied"

    dummy = Dummy()
    result = _copy_network(dummy)

    assert dummy.called is True
    assert result == "copied"


def test_copy_network_handles_missing_core_network_attribute():
    """_copy_network should still preserve directed flag without core_network."""

    class Barebones:
        def __init__(self, directed):
            self.directed = directed
            self.core_network = None

    original = Barebones(directed=True)
    copied = _copy_network(original)

    assert getattr(copied, "directed", False) is True
    assert (
        getattr(copied, "core_network", None) is None
        or copied.core_network.number_of_nodes() == 0
    )


def test_generate_null_model_increments_seed_per_sample():
    """generate_null_model should advance seed for each produced sample."""
    seen_seeds = []

    @model_registry.register("seed_tracker")
    def _seed_tracker(network, seed=None, **kwargs):  # noqa: ANN001
        seen_seeds.append(seed)
        return f"sample-{seed}"

    try:
        result = generate_null_model(
            network=object(),
            model="seed_tracker",
            num_samples=3,
            seed=5,
        )
    finally:
        model_registry._models.pop("seed_tracker", None)
        model_registry._descriptions.pop("seed_tracker", None)

    assert seen_seeds == [5, 6, 7]
    assert list(result) == ["sample-5", "sample-6", "sample-7"]


def test_generate_null_model_zero_samples(simple_network):
    """Requesting zero samples should return an empty result."""
    result = generate_null_model(
        simple_network,
        model="configuration",
        num_samples=0,
        seed=0,
    )

    assert len(result) == 0
    assert result.samples == []
    assert result.meta["model"] == "configuration"


def test_model_registry_error_lists_known_models():
    """ValueError should include known model names for easier debugging."""
    registry = ModelRegistry()

    @registry.register("alpha")
    def _alpha(network):  # noqa: ANN001
        return network

    with pytest.raises(ValueError) as excinfo:
        registry.get("beta")

    assert "alpha" in str(excinfo.value)

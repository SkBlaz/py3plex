import pytest

from types import SimpleNamespace

from py3plex.core import multinet
from py3plex.dsl import Param, Q
from py3plex.dsl.errors import DslExecutionError, ParameterMissingError


def _simple_network():
    """Create a tiny multilayer network for executor tests."""
    net = multinet.multi_layer_network(directed=False)
    net.add_edges(
        [
            {
                "source": "u",
                "target": "v",
                "source_type": "l1",
                "target_type": "l1",
            }
        ]
    )
    return net


def test_execute_on_network_without_core_returns_warning():
    """Executor should gracefully handle objects without core_network."""
    result = Q.nodes().execute(SimpleNamespace())

    assert result.items == []
    assert result.meta.get("warning") == "Network has no core_network"


def test_limit_param_without_binding_raises_parameter_missing():
    """Limit parameters must be provided at execution time."""
    net = _simple_network()
    query = Q.nodes().limit(Param.int("k"))

    with pytest.raises(ParameterMissingError):
        query.execute(net)


def test_window_unknown_aggregation_raises_dsl_error():
    """Unsupported window aggregation should raise a clear DSL error."""
    snapshot = _simple_network()

    class DummyTemporalNetwork:
        def __init__(self, snap):
            self.snapshot = snap

        def window_iter(
            self, window_size, step=None, start=None, end=None, return_type="snapshot"
        ):
            yield 0, window_size, self.snapshot

    temporal_net = DummyTemporalNetwork(snapshot)
    query = Q.nodes().window(1.0, aggregation="avg")

    with pytest.raises(DslExecutionError, match="Unknown aggregation mode: 'avg'"):
        query.execute(temporal_net)

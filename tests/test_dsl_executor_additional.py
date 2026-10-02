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


@pytest.fixture
def limit_network():
    net = _simple_network()
    net.add_edges([{
        "source": "v", "target": "w", "source_type": "l1", "target_type": "l1"
    }])
    net.assign_partition({("u", "l1"): 0, ("v", "l1"): 1, ("w", "l1"): 2})
    return net


@pytest.mark.parametrize("target", ["nodes", "edges", "communities"])
@pytest.mark.parametrize("limit", [-2, -1, 0, 1, 10])
@pytest.mark.parametrize("parameterized", [False, True])
def test_global_limit_semantics(limit_network, target, limit, parameterized):
    query = getattr(Q, target)().limit(Param.int("n") if parameterized else limit)
    original_limit = query.to_ast().select.limit
    result = query.execute(limit_network, **({"n": limit} if parameterized else {}))
    totals = {"nodes": 3, "edges": 2, "communities": 3}
    expected = 0 if limit <= 0 else min(limit, totals[target])
    assert result.count == expected
    assert len(result.items) == expected
    assert query.to_ast().select.limit == original_limit


@pytest.mark.parametrize("mode", ["computed", "early", "grouped"])
@pytest.mark.parametrize("parameterized", [False, True])
def test_negative_limit_with_selection_stages(limit_network, mode, parameterized):
    query = Q.nodes().compute("degree")
    if mode == "computed":
        query.order_by("-degree")
    elif mode == "early":
        query.order_by("layer")
    else:
        query.per_layer()
    query.limit(Param.int("n") if parameterized else -1)
    result = query.execute(limit_network, **({"n": -1} if parameterized else {}))
    assert result.items == []
    assert result.count == 0


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

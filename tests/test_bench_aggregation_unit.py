import numpy as np
import pytest
import scipy.sparse as sp

from benchmarks import bench_aggregation


def test_legacy_aggregate_sum_matches_vectorized_with_default_weight():
    edges = np.array(
        [
            [0, 0, 1],  # defaults to weight=1
            [1, 0, 1],  # same edge in another layer
            [0, 1, 2],  # another edge with default weight
        ],
        dtype=float,
    )

    legacy = bench_aggregation.legacy_aggregate_sum(edges)
    vectorized = bench_aggregation.aggregate_layers(edges, reducer="sum", to_sparse=False)

    assert legacy.shape == (3, 3)
    assert legacy[0, 1] == pytest.approx(2.0)  # two unit-weight edges collapsed
    assert legacy[1, 2] == pytest.approx(1.0)
    np.testing.assert_array_equal(vectorized, legacy)


def test_legacy_aggregate_sum_empty_edges_returns_zero_matrix():
    empty = np.empty((0, 4))

    result = bench_aggregation.legacy_aggregate_sum(empty)

    assert result.shape == (1, 1)
    assert result[0, 0] == 0.0


def test_generate_edges_respects_bounds_and_shape():
    bench = bench_aggregation.TestAggregationBenchmarks()
    np.random.seed(123)

    edges = bench._generate_edges(n_edges=10, n_layers=3, n_nodes=5)

    assert edges.shape == (10, 4)
    assert np.all(edges[:, 0] < 3)
    assert np.all(edges[:, 1] < 5)
    assert np.all(edges[:, 2] < 5)
    assert np.all((0.0 <= edges[:, 3]) & (edges[:, 3] <= 1.0))


def test_legacy_aggregate_sum_with_weights():
    edges = np.array(
        [
            [0, 0, 1, 2.5],
            [1, 0, 1, 0.5],  # same edge, different layer, different weight
            [0, 2, 0, 1.25],
        ]
    )

    result = bench_aggregation.legacy_aggregate_sum(edges)

    assert result.shape == (3, 3)
    assert result[0, 1] == pytest.approx(3.0)  # weights summed across layers
    assert result[2, 0] == pytest.approx(1.25)


def test_bench_wrappers_forward_reducer_and_sparse_flags(monkeypatch):
    bench = bench_aggregation.TestAggregationBenchmarks()
    dummy_edges = np.array([[0, 0, 1, 1.0], [1, 1, 0, 2.0]], dtype=float)
    aggregator_calls = []

    def fake_aggregate(edges, *, reducer, to_sparse):
        aggregator_calls.append((reducer, to_sparse, edges.copy()))
        return {"reducer": reducer, "to_sparse": to_sparse}

    monkeypatch.setattr(bench_aggregation, "aggregate_layers", fake_aggregate)

    class DummyBenchmark:
        def __call__(self, func, *args, **kwargs):
            return func(*args, **kwargs)

    dummy = DummyBenchmark()

    bench.test_bench_vectorized_tiny(dummy, dummy_edges)
    bench.test_bench_vectorized_small(dummy, dummy_edges)
    bench.test_bench_vectorized_medium(dummy, dummy_edges)
    bench.test_bench_vectorized_large(dummy, dummy_edges)
    bench.test_bench_vectorized_multilayer(dummy, dummy_edges)
    bench.test_bench_dense_output(dummy, dummy_edges)
    bench.test_bench_mean_reducer(dummy, dummy_edges)
    bench.test_bench_max_reducer(dummy, dummy_edges)

    expected = [
        ("sum", True),
        ("sum", True),
        ("sum", True),
        ("sum", True),
        ("sum", True),
        ("sum", False),
        ("mean", True),
        ("max", True),
    ]
    assert [(r, s) for r, s, _ in aggregator_calls] == expected
    # Edges are passed through unchanged
    for _, _, passed_edges in aggregator_calls:
        np.testing.assert_array_equal(passed_edges, dummy_edges)


def test_speedup_vs_legacy_small_monkeypatched(monkeypatch):
    bench = bench_aggregation.TestAggregationBenchmarks()
    dummy_edges = np.array([[0, 0, 1, 1.0], [1, 1, 2, 2.0]], dtype=float)
    dense_result = np.array(
        [
            [0.0, 3.0, 0.0],
            [0.0, 0.0, 2.0],
            [0.0, 0.0, 0.0],
        ]
    )

    perf_calls = iter([0.0, 1.0, 1.0, 3.0])  # vec_time=1.0, legacy=2.0 → speedup=2×
    monkeypatch.setattr(bench_aggregation.time, "perf_counter", lambda: next(perf_calls))
    monkeypatch.setattr(
        bench_aggregation,
        "aggregate_layers",
        lambda edges, reducer="sum", to_sparse=False: dense_result,
    )
    monkeypatch.setattr(
        bench_aggregation, "legacy_aggregate_sum", lambda edges: dense_result
    )

    bench.test_speedup_vs_legacy_small(dummy_edges)


def test_speedup_vs_legacy_small_fails_when_speedup_too_low(monkeypatch):
    bench = bench_aggregation.TestAggregationBenchmarks()
    dummy_edges = np.array([[0, 0, 1, 1.0]], dtype=float)
    dense_result = np.array([[0.0, 1.0], [0.0, 0.0]])

    perf_calls = iter([0.0, 2.0, 2.0, 3.0])  # vec_time=2.0, legacy=1.0 → speedup=0.5×
    monkeypatch.setattr(bench_aggregation.time, "perf_counter", lambda: next(perf_calls))
    monkeypatch.setattr(
        bench_aggregation,
        "aggregate_layers",
        lambda edges, reducer="sum", to_sparse=False: dense_result,
    )
    monkeypatch.setattr(bench_aggregation, "legacy_aggregate_sum", lambda edges: dense_result)

    with pytest.raises(AssertionError, match="below 2× target"):
        bench.test_speedup_vs_legacy_small(dummy_edges)


def test_speedup_target_sparse_output_monkeypatched(monkeypatch):
    bench = bench_aggregation.TestAggregationBenchmarks()
    dummy_edges = np.array([[0, 0, 0, 1.0], [1, 0, 0, 1.0]], dtype=float)
    sparse_result = sp.csr_matrix(np.array([[0.0, 1.0], [0.0, 0.0]]))

    perf_calls = iter([0.0, 1.0, 1.0, 4.0])  # vec_time=1.0, legacy=3.0 → speedup=3×
    monkeypatch.setattr(bench_aggregation.time, "perf_counter", lambda: next(perf_calls))
    monkeypatch.setattr(
        bench_aggregation,
        "aggregate_layers",
        lambda edges, reducer="sum", to_sparse=True: sparse_result,
    )
    monkeypatch.setattr(
        bench_aggregation, "legacy_aggregate_sum", lambda edges: sparse_result.toarray()
    )

    bench.test_speedup_target_1m_edges(dummy_edges)
    assert sparse_result.nnz == 1


def test_scalability_linear_scaling_mocked_timing(monkeypatch):
    scaler = bench_aggregation.TestScalabilityCharacteristics()

    # 4 iterations * 2 calls each
    perf_calls = iter([0.0, 0.1, 0.1, 0.6, 0.6, 1.6, 1.6, 6.6])
    monkeypatch.setattr(bench_aggregation.time, "perf_counter", lambda: next(perf_calls))
    monkeypatch.setattr(
        bench_aggregation, "aggregate_layers", lambda edges, reducer="sum", to_sparse=True: None
    )

    scaler.test_linear_scaling_edges()


def test_scalability_layer_impact_mocked_timing(monkeypatch):
    scaler = bench_aggregation.TestScalabilityCharacteristics()

    # 4 iterations * 2 calls each
    perf_calls = iter([0.0, 0.1, 0.1, 0.2, 0.2, 0.3, 0.3, 0.45])
    monkeypatch.setattr(bench_aggregation.time, "perf_counter", lambda: next(perf_calls))
    monkeypatch.setattr(
        bench_aggregation, "aggregate_layers", lambda edges, reducer="sum", to_sparse=True: None
    )

    scaler.test_layer_count_impact()

"""Disconnected landmark allocation must retain every non-trivial component."""

import networkx as nx
import pytest

from py3plex.algorithms.centrality import approx_closeness


@pytest.mark.parametrize('sizes,budget', [
    ([2, 2], 1),
    ([3, 3, 3], 1),
    ([2, 1, 1, 1, 1], 1),
    ([1, 2, 1, 1, 1], 1),
    ([2, 1, 2, 1, 1], 2),
    ([1, 1, 2, 2, 1, 1, 1], 2),
    ([3, 2, 1], 7),
    ([1, 1], 4),
    ([], 4),
])
def test_allocation_budget_and_component_coverage(sizes, budget):
    components = [set(range(size)) for size in sizes]
    allocation = approx_closeness._allocate_landmarks(components, budget)
    active_count = sum(size > 1 for size in sizes)
    assert len(allocation) == len(sizes)
    assert all(k >= 1 if size > 1 else k == 0 for size, k in zip(sizes, allocation))
    assert sum(allocation) == (max(budget, active_count) if active_count else 0)


@pytest.mark.parametrize('isolates_first', [False, True])
def test_isolates_do_not_remove_all_connected_landmarks(monkeypatch, isolates_first):
    graph = nx.Graph()
    if isolates_first:
        graph.add_nodes_from(range(10, 20))
    graph.add_edge('left', 'right')
    if not isolates_first:
        graph.add_nodes_from(range(10, 20))
    sampled = []
    original = approx_closeness._single_source_shortest_path_lengths

    def record_source(graph, source, **kwargs):
        sampled.append(source)
        return original(graph, source, **kwargs)

    monkeypatch.setattr(approx_closeness, '_single_source_shortest_path_lengths', record_source)
    values, errors = approx_closeness.approximate_closeness_landmarks(
        graph, n_landmarks=1, seed=0, diagnostics=True
    )
    assert len(sampled) == 1
    assert sampled[0] in {'left', 'right'}
    assert max(values['left'], values['right']) > 0
    assert all(values[node] == errors[node] == 0 for node in range(10, 20))


def test_each_nontrivial_component_is_actually_sampled(monkeypatch):
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (2, 3), (4, 5)])
    sampled = []
    original = approx_closeness._single_source_shortest_path_lengths

    def record_source(graph, source, **kwargs):
        sampled.append(source)
        return original(graph, source, **kwargs)

    monkeypatch.setattr(approx_closeness, '_single_source_shortest_path_lengths', record_source)
    approx_closeness.approximate_closeness_landmarks(graph, n_landmarks=1, seed=0)
    assert len(sampled) == 3
    assert {source // 2 for source in sampled} == {0, 1, 2}

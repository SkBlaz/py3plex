"""Scoped canonicalization preserves embedding configuration and execution."""

import numpy as np
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q
from py3plex.dsl.ast import canonicalize_ast_scoped
from py3plex.dsl.executor import execute_ast


@pytest.mark.parametrize('scope', ['relational', 'strict'])
def test_scoped_canonicalization_preserves_embedding_execution(scope):
    network = multi_layer_network(directed=False)
    network.add_edges([
        ['a', 'L', 'b', 'L', 1], ['b', 'L', 'c', 'L', 1],
        ['c', 'L', 'd', 'L', 1], ['d', 'L', 'a', 'L', 1],
    ], input_type='list')
    query = Q.nodes().embed(method='netmf', dim=2, seed=7, cache=False).to_ast()
    canonical, _ = canonicalize_ast_scoped(query, scope=scope)
    assert canonical.select.embedding_spec == query.select.embedding_spec
    expected = execute_ast(network, query)
    actual = execute_ast(network, canonical)
    assert actual.items == expected.items
    assert actual.attributes.keys() == expected.attributes.keys()
    assert actual.attributes
    for metric in expected.attributes:
        for item in expected.items:
            np.testing.assert_allclose(
                actual.attributes[metric][item], expected.attributes[metric][item]
            )
    repeated, _ = canonicalize_ast_scoped(canonical, scope=scope)
    assert repeated.select.embedding_spec == query.select.embedding_spec

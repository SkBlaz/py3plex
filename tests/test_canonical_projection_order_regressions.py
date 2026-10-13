"""Canonical queries must preserve the requested output column order."""

import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q
from py3plex.dsl.ast import (
    ast_from_json,
    ast_to_json,
    canonicalize_ast,
    canonicalize_ast_scoped,
)
from py3plex.dsl.provenance import ast_fingerprint


@pytest.mark.parametrize('canonicalizer', [
    canonicalize_ast,
    lambda query: canonicalize_ast_scoped(query)[0],
    lambda query: ast_from_json(ast_to_json(query)),
])
def test_canonical_replay_preserves_projection_order(canonicalizer):
    network = multi_layer_network(directed=False)
    network.add_edges([
        ['a', 'L', 'b', 'L', 1], ['b', 'L', 'c', 'L', 1],
    ], input_type='list')
    builder = Q.nodes().compute('degree', 'clustering').select('degree', 'clustering')
    original = builder.to_ast()
    restored = canonicalizer(original)
    assert restored.select.select_cols == ['degree', 'clustering']

    expected = builder.execute(network)
    actual = Q.from_ast(restored).execute(network)
    assert list(actual.attributes) == ['degree', 'clustering']
    assert actual.attributes == expected.attributes
    assert actual.to_pandas().columns.tolist() == expected.to_pandas().columns.tolist()
    assert original.select.select_cols == ['degree', 'clustering']


def test_different_projection_orders_have_different_fingerprints():
    first = Q.nodes().compute('degree', 'clustering').select('degree', 'clustering').to_ast()
    second = Q.nodes().compute('degree', 'clustering').select('clustering', 'degree').to_ast()
    assert ast_fingerprint(first) != ast_fingerprint(second)

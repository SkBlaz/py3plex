"""Canonical AST transformations must not alias execution settings."""

from copy import deepcopy

import pytest

from py3plex.dsl import Q
from py3plex.dsl.ast import (
    ApproximationSpec,
    EmbeddingSpec,
    canonicalize_ast,
    canonicalize_ast_scoped,
)
from py3plex.dsl.layers import LayerSet
from py3plex.dsl.provenance import ast_fingerprint


def configured_ast():
    query = Q.nodes().compute('degree').order_by('-degree').uq(
        method='perturbation', n_samples=4, seed=7
    ).to_ast()
    query.select.compute[0].approx = ApproximationSpec(params={'seed': 7})
    query.select.embedding_spec = EmbeddingSpec(metapaths=[['social', 'work']])
    query.select.uq_config.kwargs = {'bins': {'degree': 3}}
    query.select.layer_set = LayerSet('social') | LayerSet('work')
    return query


def mutate(query, field):
    if field == 'approximation':
        query.select.compute[0].approx.params['seed'] = 99
    elif field == 'embedding':
        query.select.embedding_spec.metapaths[0].append('later')
    elif field == 'uncertainty':
        query.select.uq_config.kwargs['bins']['degree'] = 9
    elif field == 'layers':
        query.select.layer_set.expr.left.value = 'later'
    elif field == 'ordering':
        query.select.order_by[0].desc = False


@pytest.mark.parametrize('canonicalizer,field', [
    (canonicalize_ast, field) for field in
    ('approximation', 'embedding', 'uncertainty', 'layers', 'ordering')
] + [
    (lambda query: canonicalize_ast_scoped(query)[0], field) for field in
    ('approximation', 'uncertainty', 'layers', 'ordering')
])
@pytest.mark.parametrize('mutate_original', [False, True])
def test_canonical_ast_is_independent(canonicalizer, field, mutate_original):
    original = configured_ast()
    canonical = canonicalizer(original)
    mutated, untouched = (original, canonical) if mutate_original else (canonical, original)
    expected_hash = ast_fingerprint(untouched)
    changed_hash = ast_fingerprint(mutated)
    mutate(mutated, field)
    assert ast_fingerprint(mutated) != changed_hash
    assert ast_fingerprint(untouched) == expected_hash


def test_transforming_canonical_order_does_not_change_original_execution():
    from py3plex.core.multinet import multi_layer_network

    network = multi_layer_network(directed=False)
    network.add_edges([
        ['a', 'L', 'b', 'L', 1], ['b', 'L', 'c', 'L', 1],
    ], input_type='list')
    original = Q.nodes().compute('degree').order_by('-degree').to_ast()
    snapshot = deepcopy(original)
    canonical = canonicalize_ast(original)
    canonical.select.order_by[0].desc = False
    expected = Q.from_ast(snapshot).execute(network)
    assert Q.from_ast(original).execute(network).items == expected.items
    assert Q.from_ast(canonical).execute(network).items != expected.items

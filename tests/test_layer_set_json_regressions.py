"""AST JSON preserves executable, late-bound layer set expressions."""

import pytest

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.dsl.ast import ast_from_json, ast_to_json
from py3plex.dsl.layers import LayerSet


@pytest.mark.parametrize('canonical', [False, True])
@pytest.mark.parametrize('target', ['nodes', 'edges'])
@pytest.mark.parametrize('layers', [
    LayerSet('social'),
    LayerSet('*'),
    LayerSet('social') | LayerSet('work'),
    (LayerSet('*') - LayerSet('work')) & ~LayerSet('coupling'),
    ~(LayerSet('social') | LayerSet('work')),
    LayerSet('literal | layer'),
])
def test_layer_set_json_execution_roundtrip(layers, target, canonical):
    network = multinet.multi_layer_network(directed=True)
    network.add_edges([
        ['a', layer, 'b', layer, 2] for layer in
        ('social', 'work', 'coupling', 'literal | layer')
    ], input_type='list')
    builder = getattr(Q, target)().from_layers(layers)
    original = builder.to_ast()
    restored = ast_from_json(ast_to_json(original, canonical=canonical))

    assert isinstance(restored.select.layer_set, LayerSet)
    assert restored.select.layer_set.expr == original.select.layer_set.expr
    assert restored.select.layer_set.resolve(network) == layers.resolve(network)
    assert Q.from_ast(restored).execute(network).items == builder.execute(network).items

    # Resolution must still happen against the current network, not the snapshot.
    network.add_edges([['new', 'later', 'node', 'later', 1]], input_type='list')
    assert restored.select.layer_set.resolve(network) == layers.resolve(network)
    assert Q.from_ast(restored).execute(network).items == builder.execute(network).items


def test_json_still_reads_legacy_layer_expression():
    from py3plex.dsl import L
    from py3plex.dsl.ast import LayerExpr

    original = Q.nodes().from_layers(L['social'] + L['work']).to_ast()
    restored = ast_from_json(ast_to_json(original))
    assert isinstance(restored.select.layer_expr, LayerExpr)
    assert restored.select.layer_expr == original.select.layer_expr

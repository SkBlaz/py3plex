import pytest
from py3plex.dsl import Q, L, LayerSet
from py3plex.core import multinet

@pytest.mark.parametrize("layers", [LayerSet("social"), LayerSet("social") | LayerSet("work"), LayerSet("*") - LayerSet("work"), ~LayerSet("work")])
def test_explain_layerset_without_network(layers):
    text = Q.nodes().from_layers(layers).compile().explain()
    assert "Layers: LayerSet:" in text
    assert "LayerFilter" in text

def test_explain_resolves_layers_when_network_supplied():
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([{"source":"a", "type":name} for name in ("social","work")])
    text = Q.nodes().from_layers(LayerSet("*") - LayerSet("work")).compile().explain(net)
    assert "Resolved layers: social" in text

def test_legacy_layer_expression_still_explains():
    assert "Layers: social, work" in Q.nodes().from_layers(L["social"] + L["work"]).compile().explain()

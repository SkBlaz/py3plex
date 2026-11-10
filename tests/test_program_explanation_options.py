import pytest
from py3plex.dsl import Q, L, LayerSet
from py3plex.dsl.program.explain import ExplainResult, explain_program

@pytest.mark.parametrize("cost", [True,False])
@pytest.mark.parametrize("types", [True,False])
@pytest.mark.parametrize("layers", [L["social"], LayerSet("social")])
def test_explanation_keeps_steps_with_optional_annotations(cost, types, layers):
    program = Q.nodes().from_layers(layers).where(degree__gt=1).compute("degree").order_by("-degree").limit(2).compile()
    result = explain_program(program, include_cost=cost, include_types=types)
    text = result.to_text()
    for step in ("SELECT nodes", "FROM layers:", "social", "WHERE", "COMPUTE degree", "ORDER BY degree DESC", "LIMIT 2"):
        assert step in text
    assert ("Type:" in text) == types
    assert ("Cost:" in text) == cost

def test_total_cost_renders():
    text = ExplainResult(["SELECT nodes"], [], [], [], total_cost="1s").to_text()
    assert "SELECT nodes" in text
    assert "Total Estimated Cost: 1s" in text

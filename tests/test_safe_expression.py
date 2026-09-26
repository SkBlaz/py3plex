"""Checks for the restricted expression and CLI builder parsers."""

import pytest

from py3plex._safe_expression import evaluate_expression
from py3plex.dsl.builder_parser import parse_builder_query
from py3plex.dynamics.config import _evaluate_expression


def test_filter_expression_keeps_boolean_and_arithmetic_semantics():
    context = {"degree": 3, "layer": "social"}
    assert evaluate_expression("degree * 2 > 5 and layer == 'social'", context)
    assert not evaluate_expression("degree < 2 or layer == 'work'", context)
    assert evaluate_expression("degree < 2 < missing", context) is False


@pytest.mark.parametrize("expression", [
    "__import__('os').system('true')",
    "degree.__class__",
    "[x for x in (1, 2)]",
    "degree[0]",
])
def test_filter_expression_rejects_python_execution(expression):
    with pytest.raises(ValueError):
        evaluate_expression(expression, {"degree": 3})


def test_dynamics_expression_resolves_names_without_text_substitution():
    assert _evaluate_expression("beta2 - beta", {}, {"beta": 0.1, "beta2": 0.3}) == pytest.approx(0.2)


def test_cli_builder_parser_accepts_query_and_layers():
    query = parse_builder_query(
        "Q.nodes().from_layers(L['social'] + L['work']).where(degree__gt=1).limit(3)"
    )
    assert query.to_ast().select.limit == 3
    assert query.to_ast().select.layer_expr.get_layer_names() == ["social", "work"]


@pytest.mark.parametrize("source", [
    "Q.nodes().execute(None)",
    "Q.nodes().__class__",
    "__import__('os').system('true')",
    "Q.nodes().compute(*['degree'])",
])
def test_cli_builder_parser_rejects_execution_and_dynamic_python(source):
    with pytest.raises(ValueError):
        parse_builder_query(source)

"""AST JSON must preserve typed targets and remain executable."""

import json

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q
from py3plex.dsl.ast import Target, ast_from_json, ast_to_json
from py3plex.dsl.executor import execute_ast
from py3plex.dsl.provenance import ast_fingerprint


@pytest.mark.parametrize("target", list(Target))
@pytest.mark.parametrize("canonical", [True, False])
def test_json_preserves_target_type_and_hash(target, canonical):
    ast = Q.nodes().to_ast()
    ast.select.target = target
    restored = ast_from_json(ast_to_json(ast, canonical=canonical))
    assert restored.select.target is target
    assert ast_fingerprint(restored) == ast_fingerprint(ast)


@pytest.mark.parametrize("legacy", [True, False])
@pytest.mark.parametrize("target", [Target.NODES, Target.EDGES])
def test_deserialized_ast_executes_with_tagged_or_legacy_target(target, legacy):
    network = multi_layer_network(directed=True)
    network.core_network = nx.DiGraph()
    network.core_network.add_edge(("a", "L"), ("b", "L"), weight=2)
    ast = (Q.nodes() if target is Target.NODES else Q.edges()).to_ast()
    data = json.loads(ast_to_json(ast))
    if legacy:
        data["select"]["target"] = target.value
    restored = ast_from_json(json.dumps(data))
    result = execute_ast(network, restored)
    expected = execute_ast(network, ast)
    assert restored.select.target is target
    assert result.target == expected.target
    assert result.items == expected.items
    assert result.attributes == expected.attributes

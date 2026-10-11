"""JSON readers must accept execution specs emitted by the AST writer."""

import pytest

from py3plex.dsl import Q
from py3plex.dsl.ast import ApproximationSpec, EmbeddingSpec, ast_from_json, ast_to_json


@pytest.mark.parametrize("seed", [0, 42])
@pytest.mark.parametrize("measure", ["betweenness_centrality", "closeness_centrality"])
def test_json_reconstructs_approximation_spec(measure, seed):
    params = {"n_samples": 2} if measure == "betweenness_centrality" else {"n_landmarks": 2}
    original = Q.nodes().compute(measure, approx=True, seed=seed, **params).to_ast()
    restored = ast_from_json(ast_to_json(original, canonical=False))
    actual = restored.select.compute[0].approx
    assert isinstance(actual, ApproximationSpec)
    assert actual == original.select.compute[0].approx
    assert actual.params["seed"] == seed


@pytest.mark.parametrize("seed", [0, 42])
@pytest.mark.parametrize("method", ["netmf", "metapath2vec"])
def test_json_reconstructs_embedding_spec(method, seed):
    original = Q.nodes().embed(
        method=method, dim=4, seed=seed, layers=["author", "paper"],
        metapaths=[["author", "paper", "author"]], cache=False,
    ).to_ast()
    restored = ast_from_json(ast_to_json(original, canonical=False))
    assert isinstance(restored.select.embedding_spec, EmbeddingSpec)
    assert restored.select.embedding_spec == original.select.embedding_spec


def test_json_still_rejects_unrecognized_ast_types():
    import json

    data = json.loads(ast_to_json(Q.nodes().to_ast(), canonical=False))
    data["select"]["embedding_spec"] = {"__type__": "UnrecognizedSpec"}
    with pytest.raises(ValueError, match="Unknown type: UnrecognizedSpec"):
        ast_from_json(json.dumps(data))

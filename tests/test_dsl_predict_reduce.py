"""Tests for predictive and reduction first-class DSL extensions."""

import pytest

from py3plex.core import multinet
from py3plex.dsl import Q, PredictStmt, ReduceStmt


@pytest.fixture
def multilayer_network_sample():
    net = multinet.multi_layer_network(directed=False)
    nodes = []
    for n in ["A", "B", "C", "D", "E"]:
        for layer in ["work", "leisure"]:
            nodes.append({"source": n, "type": layer})
    net.add_nodes(nodes)
    net.add_edges(
        [
            {"source": "A", "target": "B", "source_type": "work", "target_type": "work", "t": 1},
            {"source": "B", "target": "C", "source_type": "work", "target_type": "work", "t": 2},
            {"source": "C", "target": "D", "source_type": "work", "target_type": "work", "t": 3},
            {"source": "A", "target": "C", "source_type": "leisure", "target_type": "leisure", "t": 1},
            {"source": "C", "target": "E", "source_type": "leisure", "target_type": "leisure", "t": 4},
            {"source": "B", "target": "D", "source_type": "leisure", "target_type": "leisure", "t": 5},
        ]
    )
    return net


def test_predict_builder_to_ast_compiles():
    builder = (
        Q.predict.links()
        .random_holdout(0.2, seed=42)
        .model("common_neighbors")
        .eval(["roc_auc", "ap"])
    )
    ast = builder.to_ast()
    assert isinstance(ast, PredictStmt)
    assert ast.spec.model.name == "common_neighbors"
    assert ast.spec.split.strategy == "random_holdout"


def test_reduce_builder_to_ast_compiles():
    builder = Q.reduce.layers(method="hierarchical_js").target_k(2).distance("js_divergence")
    ast = builder.to_ast()
    assert isinstance(ast, ReduceStmt)
    assert ast.spec.method == "hierarchical_js"
    assert ast.spec.target_k == 2


def test_predict_links_heuristic_executes(multilayer_network_sample):
    res = (
        Q.predict.links()
        .scope(layers=["work", "leisure"])
        .random_holdout(0.34, seed=7)
        .model("common_neighbors")
        .negative_sampling(strategy="uniform", ratio=1.0, seed=7)
        .evaluate(metrics=["roc_auc", "average_precision", "precision@2"])
        .execute(multilayer_network_sample)
    )
    assert "roc_auc" in res.metrics
    assert "average_precision" in res.metrics
    assert isinstance(res.to_dict(), dict)
    assert res.is_replayable
    replay = res.replay()
    assert replay.metrics["roc_auc"] == pytest.approx(res.metrics["roc_auc"])


def test_predict_links_node2vec_temporal_holdout_executes(multilayer_network_sample):
    res = (
        Q.predict.links()
        .scope(layers=["work", "leisure"])
        .temporal_holdout(0.33)
        .model("node2vec", dim=16, walk_len=20, num_walks=5, seed=11)
        .edge_features("hadamard")
        .classifier("logreg", C=1.0)
        .negative_sampling(strategy="uniform", ratio=1.0, seed=11)
        .eval(["roc_auc", "ap"])
        .execute(multilayer_network_sample)
    )
    assert "roc_auc" in res.metrics
    assert "ap" in res.metrics
    assert res.provenance is not None
    assert res.provenance["split"]["strategy"] == "temporal_holdout"


def test_predict_links_by_layer_holdout_executes(multilayer_network_sample):
    res = (
        Q.predict.links()
        .scope(layers=["work", "leisure"])
        .by_layer_holdout(test_frac=0.5, seed=19)
        .model("jaccard")
        .negative_sampling(strategy="uniform", ratio=1.0, seed=19)
        .eval(["roc_auc"])
        .execute(multilayer_network_sample)
    )
    assert "roc_auc" in res.metrics
    assert res.provenance["split"]["strategy"] == "by_layer_holdout"


def test_predict_seed_determinism(multilayer_network_sample):
    q = (
        Q.predict.links()
        .scope(layers=["work", "leisure"])
        .random_holdout(0.34, seed=21)
        .model("common_neighbors")
        .negative_sampling(strategy="uniform", ratio=1.0, seed=21)
        .eval(["roc_auc", "average_precision"])
    )
    r1 = q.execute(multilayer_network_sample)
    r2 = q.execute(multilayer_network_sample)
    assert r1.metrics["roc_auc"] == pytest.approx(r2.metrics["roc_auc"])
    assert r1.metrics["average_precision"] == pytest.approx(r2.metrics["average_precision"])


def test_reduce_layers_hierarchical_executes(multilayer_network_sample):
    res = (
        Q.reduce.layers(method="hierarchical_js")
        .target_k(1)
        .distance("js_divergence")
        .aggregate("sum")
        .execute(multilayer_network_sample)
    )
    assert res.network is not None
    assert len(res.layer_mapping) == 2
    assert res.meta["original_layers"] == 2
    assert res.meta["reduced_layers"] == 1


def test_reduce_layers_other_methods(multilayer_network_sample):
    r1 = Q.reduce.layers(method="von_neumann_entropy").target_k(2).execute(multilayer_network_sample)
    r2 = Q.reduce.layers(method="strata_sbm").target_k(2).execute(multilayer_network_sample)
    assert r1.meta["method"] == "von_neumann_entropy"
    assert r2.meta["method"] == "strata_sbm"
    assert r1.provenance is not None
    assert r2.provenance is not None

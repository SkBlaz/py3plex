"""Example: first-class predictive and reduction DSL extensions."""

from py3plex.core import multinet
from py3plex.dsl import Q, L


def build_network():
    net = multinet.multi_layer_network(directed=False)
    nodes = []
    for n in ["A", "B", "C", "D", "E", "F"]:
        for layer in ["work", "leisure", "social"]:
            nodes.append({"source": n, "type": layer})
    net.add_nodes(nodes)
    net.add_edges(
        [
            {"source": "A", "target": "B", "source_type": "work", "target_type": "work", "t": 1},
            {"source": "B", "target": "C", "source_type": "work", "target_type": "work", "t": 2},
            {"source": "C", "target": "D", "source_type": "work", "target_type": "work", "t": 3},
            {"source": "A", "target": "C", "source_type": "leisure", "target_type": "leisure", "t": 1},
            {"source": "C", "target": "E", "source_type": "leisure", "target_type": "leisure", "t": 4},
            {"source": "B", "target": "D", "source_type": "social", "target_type": "social", "t": 2},
            {"source": "D", "target": "F", "source_type": "social", "target_type": "social", "t": 5},
        ]
    )
    return net


def main():
    net = build_network()

    lp = (
        Q.predict.links()
        .scope(layers=L["work"] + L["leisure"])
        .temporal_holdout(0.34)
        .model("node2vec", dim=32, walk_len=40, num_walks=8, seed=42)
        .edge_features("hadamard")
        .classifier("logreg", C=1.0)
        .negative_sampling(strategy="uniform", ratio=1.0, seed=42)
        .evaluate(metrics=["roc_auc", "average_precision", "precision@3"])
        .execute(net)
    )
    print(lp.report())
    print(lp.to_pandas().head())

    lp_compact = (
        Q.predict.links()
        .temporal_holdout(0.34)
        .model("jaccard")
        .eval(["roc_auc", "ap"])
        .execute(net)
    )
    print("Compact predictive form metrics:", lp_compact.metrics)

    reduction = (
        Q.reduce.layers(method="hierarchical_js")
        .target_k(2)
        .distance("js_divergence")
        .aggregate("sum")
        .execute(net)
    )
    print(reduction.report())
    print(reduction.to_pandas())

    reduction_alt = Q.reduce.layers().method("strata_sbm").target_k(2).execute(net)
    print("Alternative reduction method:", reduction_alt.meta["method"])


if __name__ == "__main__":
    main()

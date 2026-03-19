"""Canonical DSL query zoo implementations used by examples, tests, and documentation."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

import networkx as nx
import numpy as np
import pandas as pd


def _replicas(network) -> List[Tuple[str, str]]:
    return list(network.get_nodes())


def _layers(network) -> List[str]:
    return sorted({layer for _, layer in _replicas(network)})


def _replica_graph(network) -> nx.Graph:
    return network.core_network


def _layer_graph(network, layer: str) -> nx.Graph:
    graph = nx.Graph()
    for node, node_layer in _replicas(network):
        if node_layer == layer:
            graph.add_node(node)
    for source, target, data in _replica_graph(network).edges(data=True):
        if (
            isinstance(source, tuple)
            and isinstance(target, tuple)
            and len(source) >= 2
            and len(target) >= 2
            and source[1] == layer
            and target[1] == layer
        ):
            graph.add_edge(source[0], target[0], **data)
    return graph


def _aggregate_physical_graph(network, drop_layers: Iterable[str] | None = None) -> nx.Graph:
    drop = set(drop_layers or [])
    graph = nx.Graph()
    for source, target, data in _replica_graph(network).edges(data=True):
        if not (
            isinstance(source, tuple)
            and isinstance(target, tuple)
            and len(source) >= 2
            and len(target) >= 2
        ):
            continue
        if source[1] in drop or target[1] in drop:
            continue
        src = source[0]
        dst = target[0]
        graph.add_node(src)
        graph.add_node(dst)
        if src == dst:
            continue
        weight = float(data.get("weight", 1.0))
        if graph.has_edge(src, dst):
            graph[src][dst]["weight"] += weight
        else:
            graph.add_edge(src, dst, weight=weight)
    return graph


def _layer_counts(network) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for node, _layer in _replicas(network):
        counts[node] += 1
    return counts


def query_basic_exploration(network) -> pd.DataFrame:
    rows = []
    for layer in _layers(network):
        graph = _layer_graph(network, layer)
        n_nodes = graph.number_of_nodes()
        n_edges = graph.number_of_edges()
        avg_degree = (2 * n_edges / n_nodes) if n_nodes else 0.0
        rows.append(
            {
                "layer": layer,
                "n_nodes": n_nodes,
                "n_edges": n_edges,
                "avg_degree": avg_degree,
            }
        )
    return pd.DataFrame(rows, columns=["layer", "n_nodes", "n_edges", "avg_degree"])


def query_cross_layer_hubs(network, k: int = 5) -> pd.DataFrame:
    rows = []
    counts = _layer_counts(network)
    for layer in _layers(network):
        graph = _layer_graph(network, layer)
        degree = dict(graph.degree())
        betweenness = nx.betweenness_centrality(graph) if graph.number_of_nodes() else {}
        ordered = sorted(
            graph.nodes(),
            key=lambda node: (-degree.get(node, 0), -betweenness.get(node, 0.0), node),
        )[:k]
        for node in ordered:
            rows.append(
                {
                    "node": node,
                    "layer": layer,
                    "degree": degree.get(node, 0),
                    "betweenness_centrality": betweenness.get(node, 0.0),
                    "layer_count": counts.get(node, 1),
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "node",
            "layer",
            "degree",
            "betweenness_centrality",
            "layer_count",
        ],
    )


def query_layer_similarity(network) -> pd.DataFrame:
    layers = _layers(network)
    all_nodes = sorted({node for node, _ in _replicas(network)})
    layer_vectors = []
    for layer in layers:
        graph = _layer_graph(network, layer)
        layer_vectors.append([graph.degree(node) if node in graph else 0 for node in all_nodes])
    matrix = np.corrcoef(np.array(layer_vectors, dtype=float))
    matrix = np.nan_to_num(matrix, nan=0.0)
    np.fill_diagonal(matrix, 1.0)
    return pd.DataFrame(matrix, index=layers, columns=layers)


def query_community_structure(network) -> pd.DataFrame:
    rows = []
    community_id = 0
    for layer in _layers(network):
        graph = _layer_graph(network, layer)
        for component in nx.connected_components(graph):
            subgraph = graph.subgraph(component)
            size = subgraph.number_of_nodes()
            avg_degree = (
                sum(dict(subgraph.degree()).values()) / size if size else 0.0
            )
            rows.append(
                {
                    "community_id": community_id,
                    "layer": layer,
                    "size": size,
                    "avg_degree": avg_degree,
                    "dominant_layer": layer,
                }
            )
            community_id += 1
    return pd.DataFrame(
        rows,
        columns=["community_id", "layer", "size", "avg_degree", "dominant_layer"],
    )


def query_multiplex_pagerank(network) -> pd.DataFrame:
    graph = _aggregate_physical_graph(network)
    pagerank = nx.pagerank(graph, weight="weight")
    rows = [{"node": node, "multiplex_pagerank": pagerank[node]} for node in sorted(graph)]
    return pd.DataFrame(rows, columns=["node", "multiplex_pagerank"])


def query_robustness_analysis(network) -> pd.DataFrame:
    baseline_graph = _aggregate_physical_graph(network)
    baseline_cc = (
        len(max(nx.connected_components(baseline_graph), key=len))
        if baseline_graph.number_of_nodes()
        else 0
    )
    rows = []
    scenarios = [("baseline", None)] + [
        (f"without {layer}", [layer]) for layer in _layers(network)
    ]
    for scenario, removed in scenarios:
        graph = _aggregate_physical_graph(network, drop_layers=removed)
        n_nodes = graph.number_of_nodes()
        n_edges = graph.number_of_edges()
        avg_degree = (2 * n_edges / n_nodes) if n_nodes else 0.0
        largest_cc = (
            len(max(nx.connected_components(graph), key=len)) if n_nodes else 0
        )
        loss = 0.0 if not baseline_cc else max(0.0, 100.0 * (baseline_cc - largest_cc) / baseline_cc)
        rows.append(
            {
                "scenario": scenario,
                "n_nodes": n_nodes,
                "avg_degree": avg_degree,
                "total_edges": n_edges,
                "connectivity_loss": loss,
            }
        )
    return pd.DataFrame(
        rows,
        columns=["scenario", "n_nodes", "avg_degree", "total_edges", "connectivity_loss"],
    )


def query_advanced_centrality_comparison(network) -> pd.DataFrame:
    graph = _aggregate_physical_graph(network)
    degree = dict(graph.degree())
    betweenness = nx.betweenness_centrality(graph, weight="weight")
    closeness = nx.closeness_centrality(graph)
    pagerank = nx.pagerank(graph, weight="weight")
    metrics = [degree, betweenness, closeness, pagerank]
    thresholds = [np.quantile(list(metric.values()), 0.75) if metric else 0.0 for metric in metrics]

    rows = []
    for node in sorted(graph.nodes()):
        versatility = sum(metric.get(node, 0.0) >= threshold for metric, threshold in zip(metrics, thresholds))
        if versatility >= 3:
            hub_type = "versatile_hub"
        elif versatility >= 1:
            hub_type = "specialized_hub"
        else:
            hub_type = "peripheral"
        rows.append(
            {
                "node": node,
                "degree": degree.get(node, 0),
                "betweenness_centrality": betweenness.get(node, 0.0),
                "closeness_centrality": closeness.get(node, 0.0),
                "pagerank": pagerank.get(node, 0.0),
                "versatility": versatility,
                "hub_type": hub_type,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "node",
            "degree",
            "betweenness_centrality",
            "closeness_centrality",
            "pagerank",
            "versatility",
            "hub_type",
        ],
    )


def query_edge_grouping_and_coverage(network, k: int = 3) -> Dict[str, pd.DataFrame]:
    grouped: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
    for source, target, data in _replica_graph(network).edges(data=True):
        if not (
            isinstance(source, tuple)
            and isinstance(target, tuple)
            and len(source) >= 2
            and len(target) >= 2
        ):
            continue
        grouped[(source[1], target[1])].append(
            {
                "source": source[0],
                "target": target[0],
                "source_layer": source[1],
                "target_layer": target[1],
                "weight": float(data.get("weight", 1.0)),
            }
        )

    edge_rows: List[dict] = []
    summary_rows: List[dict] = []
    for (src_layer, dst_layer), items in sorted(grouped.items()):
        top_items = sorted(items, key=lambda item: -item["weight"])[:k]
        edge_rows.extend(top_items)
        summary_rows.append(
            {"src_layer": src_layer, "dst_layer": dst_layer, "n_items": len(top_items)}
        )

    return {
        "edges_by_pair": pd.DataFrame(edge_rows),
        "summary": pd.DataFrame(summary_rows, columns=["src_layer", "dst_layer", "n_items"]),
    }


def query_null_model_comparison(network) -> pd.DataFrame:
    rows = []
    for layer in _layers(network):
        graph = _layer_graph(network, layer)
        degrees = pd.Series(dict(graph.degree()), dtype=float)
        mean = float(degrees.mean()) if not degrees.empty else 0.0
        std = float(degrees.std(ddof=0)) if len(degrees) > 1 else 0.0
        for node, degree in degrees.items():
            z_score = 0.0 if std == 0 else (degree - mean) / std
            rows.append(
                {
                    "id": node,
                    "layer": layer,
                    "degree": degree,
                    "expected_degree": mean,
                    "z_score": z_score,
                    "is_significant": abs(z_score) >= 1.96,
                }
            )
    return pd.DataFrame(
        rows,
        columns=["id", "layer", "degree", "expected_degree", "z_score", "is_significant"],
    )


def query_bootstrap_confidence_intervals(network) -> pd.DataFrame:
    samples: Dict[str, List[float]] = defaultdict(list)
    for layer in _layers(network):
        graph = _layer_graph(network, layer)
        for node in graph.nodes():
            samples[node].append(float(graph.degree(node)))

    rows = []
    for node, values in sorted(samples.items()):
        arr = np.array(values, dtype=float)
        mean = float(arr.mean()) if len(arr) else 0.0
        std = float(arr.std(ddof=0)) if len(arr) > 1 else 0.0
        rel = 0.0 if mean == 0 else std / mean
        rows.append({"id": node, "mean": mean, "std": std, "relative_variability": rel})
    return pd.DataFrame(rows, columns=["id", "mean", "std", "relative_variability"])


def query_uncertainty_aware_ranking(network) -> pd.DataFrame:
    samples: Dict[str, List[float]] = defaultdict(list)
    for layer in _layers(network):
        graph = _layer_graph(network, layer)
        for node in graph.nodes():
            samples[node].append(float(graph.degree(node)))

    rows = []
    for node, values in sorted(samples.items()):
        arr = np.array(values, dtype=float)
        rows.append(
            {
                "node": node,
                "max_score": float(arr.max()),
                "mean_score": float(arr.mean()),
                "consistency_score": float(arr.mean() / (1.0 + arr.std(ddof=0))),
            }
        )

    df = pd.DataFrame(rows).sort_values("node").reset_index(drop=True)
    df["rank_by_max"] = df["max_score"].rank(method="dense", ascending=False).astype(int)
    df["rank_by_mean"] = df["mean_score"].rank(method="dense", ascending=False).astype(int)
    df["rank_by_consistency"] = (
        df["consistency_score"].rank(method="dense", ascending=False).astype(int)
    )
    return df[["node", "rank_by_max", "rank_by_mean", "rank_by_consistency"]]

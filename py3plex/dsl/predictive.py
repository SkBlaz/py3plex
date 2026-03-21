"""Predictive task DSL execution primitives.

This module implements first-class link prediction workflows for DSL v2.
"""

from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

from py3plex.core.multinet import multi_layer_network
from py3plex.ml.embedding.node2vec import Node2VecEmbedding

from .ast import (
    EvalSpec,
    LinkPredictionSpec,
    ModelSpec,
    NegativeSamplingSpec,
    PredictStmt,
    SplitSpec,
)
from .errors import (
    NegativeSamplingError,
    PredictionTaskError,
    SplitStrategyError,
)

logger = logging.getLogger(__name__)

EdgeKey = Tuple[Tuple[Any, Any], Tuple[Any, Any]]


def _canonical_edge(u: Tuple[Any, Any], v: Tuple[Any, Any], directed: bool) -> EdgeKey:
    if directed:
        return (u, v)
    return (u, v) if str(u) <= str(v) else (v, u)


def _extract_edge_tuple(edge: Tuple[Any, ...]) -> Tuple[Tuple[Any, Any], Tuple[Any, Any], Dict[str, Any]]:
    if len(edge) >= 4 and isinstance(edge[-1], dict):  # multiplex path with key
        return edge[0], edge[1], edge[-1]
    if len(edge) >= 3 and isinstance(edge[-1], dict):
        return edge[0], edge[1], edge[-1]
    if len(edge) >= 2:
        return edge[0], edge[1], {}
    raise PredictionTaskError(f"Malformed edge encountered: {edge!r}")


def _to_numpy_scalar(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _js_divergence(p: np.ndarray, q: np.ndarray, eps: float = 1e-12) -> float:
    p = p + eps
    q = q + eps
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    return float(0.5 * np.sum(p * np.log(p / m)) + 0.5 * np.sum(q * np.log(q / m)))


@dataclass
class _PredictRegistryEntry:
    name: str
    aliases: Tuple[str, ...]
    deterministic: bool
    impl: Any
    capabilities: Dict[str, Any] = field(default_factory=dict)


SPLIT_REGISTRY: Dict[str, _PredictRegistryEntry] = {}
NEGATIVE_SAMPLER_REGISTRY: Dict[str, _PredictRegistryEntry] = {}
MODEL_REGISTRY: Dict[str, _PredictRegistryEntry] = {}
EDGE_FEATURE_REGISTRY: Dict[str, _PredictRegistryEntry] = {}
CLASSIFIER_REGISTRY: Dict[str, _PredictRegistryEntry] = {}
EVALUATOR_REGISTRY: Dict[str, _PredictRegistryEntry] = {}


def _register(registry: Dict[str, _PredictRegistryEntry], entry: _PredictRegistryEntry) -> None:
    registry[entry.name] = entry
    for alias in entry.aliases:
        registry[alias] = entry


class PredictionResult:
    """Result object for link prediction workflows."""

    def __init__(
        self,
        metrics: Dict[str, float],
        predictions: List[Dict[str, Any]],
        meta: Optional[Dict[str, Any]] = None,
        replay_fn: Optional[Callable[[], "PredictionResult"]] = None,
    ):
        self.metrics = metrics
        self.predictions = predictions
        self.meta = meta or {}
        self._replay_fn = replay_fn

    @property
    def provenance(self) -> Optional[Dict[str, Any]]:
        return self.meta.get("provenance")

    @property
    def is_replayable(self) -> bool:
        return self._replay_fn is not None

    def replay(self) -> "PredictionResult":
        if not self._replay_fn:
            raise PredictionTaskError("Prediction result is not replayable.")
        return self._replay_fn()

    def to_pandas(self):
        import pandas as pd

        return pd.DataFrame(self.predictions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": dict(self.metrics),
            "predictions": list(self.predictions),
            "meta": dict(self.meta),
        }

    def report(self) -> str:
        lines = ["Link Prediction Report", "=" * 24]
        for k, v in sorted(self.metrics.items()):
            lines.append(f"{k}: {v:.6f}" if isinstance(v, (int, float)) else f"{k}: {v}")
        split_meta = self.meta.get("split", {})
        if split_meta:
            lines.append(
                f"train_pos={split_meta.get('train_pos')} test_pos={split_meta.get('test_pos')}"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"PredictionResult(metrics={list(self.metrics.keys())}, "
            f"n_predictions={len(self.predictions)}, replayable={self.is_replayable})"
        )


def _resolve_scope_layers(network: Any, layers_expr: Any) -> Optional[set]:
    if layers_expr is None:
        return None
    if hasattr(layers_expr, "resolve"):
        return set(layers_expr.resolve(network))
    if hasattr(layers_expr, "terms"):
        return {term.name for term in layers_expr.terms}
    if isinstance(layers_expr, (list, tuple, set)):
        return set(layers_expr)
    return {str(layers_expr)}


def _iter_scoped_edges(network: Any, allowed_layers: Optional[set]) -> List[Tuple[EdgeKey, Dict[str, Any]]]:
    out: List[Tuple[EdgeKey, Dict[str, Any]]] = []
    directed = bool(getattr(network, "directed", False))
    for raw in network.get_edges(data=True):
        u, v, data = _extract_edge_tuple(raw)
        if allowed_layers is not None and (u[1] not in allowed_layers or v[1] not in allowed_layers):
            continue
        out.append((_canonical_edge(u, v, directed), data))
    return out


def _extract_edge_time(data: Dict[str, Any]) -> Optional[float]:
    if "t_start" in data:
        return _to_numpy_scalar(data["t_start"])
    if "t" in data:
        return _to_numpy_scalar(data["t"])
    if "timestamp" in data:
        return _to_numpy_scalar(data["timestamp"])
    return None


def _split_random_holdout(
    positives: List[Tuple[EdgeKey, Dict[str, Any]]],
    test_frac: float,
    seed: Optional[int],
) -> Tuple[List[EdgeKey], List[EdgeKey], Dict[str, Any]]:
    if not positives:
        return [], [], {"strategy": "random_holdout", "test_frac": test_frac}
    rng = np.random.default_rng(seed)
    idx = np.arange(len(positives))
    rng.shuffle(idx)
    n_test = max(1, int(round(len(positives) * test_frac)))
    test_idx = set(idx[:n_test].tolist())
    train = [positives[i][0] for i in range(len(positives)) if i not in test_idx]
    test = [positives[i][0] for i in range(len(positives)) if i in test_idx]
    return train, test, {"strategy": "random_holdout", "test_frac": test_frac, "seed": seed}


def _split_temporal_holdout(
    positives: List[Tuple[EdgeKey, Dict[str, Any]]],
    test_frac: float,
) -> Tuple[List[EdgeKey], List[EdgeKey], Dict[str, Any]]:
    timed: List[Tuple[EdgeKey, float]] = []
    for edge, data in positives:
        t = _extract_edge_time(data)
        if t is None:
            raise SplitStrategyError(
                "temporal_holdout requires temporal edge attributes (t, t_start, or timestamp)."
            )
        timed.append((edge, t))
    timed.sort(key=lambda x: x[1])
    n_test = max(1, int(round(len(timed) * test_frac)))
    split_idx = max(1, len(timed) - n_test)
    train = [e for e, _ in timed[:split_idx]]
    test = [e for e, _ in timed[split_idx:]]
    return train, test, {
        "strategy": "temporal_holdout",
        "test_frac": test_frac,
        "cutoff_time": timed[split_idx][1] if split_idx < len(timed) else timed[-1][1],
    }


def _sample_negative_edges(
    graph: nx.Graph,
    candidate_nodes: Sequence[Tuple[Any, Any]],
    num_needed: int,
    directed: bool,
    same_layer_only: bool,
    rng: np.random.Generator,
    forbidden: Optional[set] = None,
) -> List[EdgeKey]:
    forbidden = forbidden or set()
    nodes = list(candidate_nodes)
    if len(nodes) < 2:
        return []
    sampled: List[EdgeKey] = []
    seen = set(forbidden)
    max_trials = max(1000, num_needed * 30)
    trials = 0
    while len(sampled) < num_needed and trials < max_trials:
        trials += 1
        u = nodes[int(rng.integers(0, len(nodes)))]
        v = nodes[int(rng.integers(0, len(nodes)))]
        if u == v:
            continue
        if same_layer_only and u[1] != v[1]:
            continue
        e = _canonical_edge(u, v, directed)
        if e in seen:
            continue
        if graph.has_edge(*e):
            continue
        seen.add(e)
        sampled.append(e)
    return sampled


def _heuristic_score_factory(name: str, train_graph: nx.Graph) -> Callable[[EdgeKey], float]:
    def _cn(edge: EdgeKey) -> float:
        u, v = edge
        return float(len(set(train_graph.neighbors(u)).intersection(set(train_graph.neighbors(v)))))

    def _jaccard(edge: EdgeKey) -> float:
        u, v = edge
        nu = set(train_graph.neighbors(u))
        nv = set(train_graph.neighbors(v))
        den = len(nu | nv)
        if den == 0:
            return 0.0
        return float(len(nu & nv) / den)

    def _aa(edge: EdgeKey) -> float:
        u, v = edge
        score = 0.0
        for w in set(train_graph.neighbors(u)).intersection(set(train_graph.neighbors(v))):
            deg = max(2, train_graph.degree(w))
            score += 1.0 / np.log(deg)
        return float(score)

    def _pa(edge: EdgeKey) -> float:
        u, v = edge
        return float(train_graph.degree(u) * train_graph.degree(v))

    mapping = {
        "common_neighbors": _cn,
        "jaccard": _jaccard,
        "adamic_adar": _aa,
        "preferential_attachment": _pa,
    }
    if name not in mapping:
        raise PredictionTaskError(f"Unknown heuristic model '{name}'.")
    return mapping[name]


def _edge_feature_composer(kind: str) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    kind = kind.lower()
    if kind == "hadamard":
        return lambda a, b: a * b
    if kind == "l1":
        return lambda a, b: np.abs(a - b)
    if kind == "l2":
        return lambda a, b: (a - b) ** 2
    if kind == "concat":
        return lambda a, b: np.concatenate([a, b])
    raise PredictionTaskError(
        f"Unknown edge feature operator '{kind}'. Use hadamard, l1, l2, or concat."
    )


def _compute_metric(metric: str, y_true: np.ndarray, y_score: np.ndarray, k: Optional[int] = None) -> float:
    m = metric.lower()
    if m in ("ap", "average_precision"):
        return float(average_precision_score(y_true, y_score))
    if m == "roc_auc":
        return float(roc_auc_score(y_true, y_score))
    if m in ("map", "mean_average_precision"):
        order = np.argsort(-y_score)
        y_sorted = y_true[order]
        precisions = []
        hits = 0
        for i, y in enumerate(y_sorted, start=1):
            if y == 1:
                hits += 1
                precisions.append(hits / i)
        return float(np.mean(precisions)) if precisions else 0.0
    if m.startswith("precision@"):
        k_val = int(m.split("@", 1)[1]) if "@" in m else int(k or 10)
        idx = np.argsort(-y_score)[:k_val]
        return float(np.mean(y_true[idx])) if len(idx) else 0.0
    if m.startswith("recall@"):
        k_val = int(m.split("@", 1)[1]) if "@" in m else int(k or 10)
        idx = np.argsort(-y_score)[:k_val]
        positives = max(1, int(np.sum(y_true)))
        return float(np.sum(y_true[idx]) / positives) if len(idx) else 0.0
    raise PredictionTaskError(f"Unknown evaluation metric '{metric}'.")


def _build_train_network(
    original_network: Any,
    train_edges: List[EdgeKey],
    scope_layers: Optional[set],
) -> multi_layer_network:
    directed = bool(getattr(original_network, "directed", False))
    train_net = multi_layer_network(network_type="multilayer", directed=directed)
    node_dicts = []
    for node, layer in original_network.get_nodes():
        if scope_layers is not None and layer not in scope_layers:
            continue
        node_dicts.append({"source": node, "type": layer})
    if node_dicts:
        train_net.add_nodes(node_dicts)

    edge_dicts = []
    for (u, v) in train_edges:
        edge_dicts.append(
            {
                "source": u[0],
                "target": v[0],
                "source_type": u[1],
                "target_type": v[1],
                "weight": 1.0,
            }
        )
    if edge_dicts:
        train_net.add_edges(edge_dicts)
    return train_net


def execute_predict_stmt(network: Any, stmt: PredictStmt) -> PredictionResult:
    if stmt.task != "links":
        raise PredictionTaskError(f"Unsupported predictive task '{stmt.task}'.")
    spec = stmt.spec
    if spec is None:
        raise PredictionTaskError("Missing LinkPredictionSpec in PredictStmt.")

    scope_layers = _resolve_scope_layers(network, spec.layers_expr)
    scoped_edges = _iter_scoped_edges(network, scope_layers)
    if not scoped_edges:
        raise PredictionTaskError("No edges available in selected scope.")

    split_entry = SPLIT_REGISTRY.get(spec.split.strategy)
    if split_entry is None:
        raise SplitStrategyError(f"Unknown split strategy '{spec.split.strategy}'.")

    if spec.split.strategy == "temporal_holdout":
        train_pos, test_pos, split_meta = _split_temporal_holdout(scoped_edges, spec.split.test_frac)
    else:
        train_pos, test_pos, split_meta = _split_random_holdout(
            scoped_edges, spec.split.test_frac, spec.split.seed
        )

    if not train_pos or not test_pos:
        raise SplitStrategyError("Split produced empty train or test set; adjust test_frac.")

    train_net = _build_train_network(network, train_pos, scope_layers)
    directed = bool(getattr(network, "directed", False))
    train_graph = nx.DiGraph() if directed else nx.Graph()
    for n in train_net.get_nodes():
        train_graph.add_node(n)
    for raw in train_net.get_edges(data=True):
        u, v, _ = _extract_edge_tuple(raw)
        train_graph.add_edge(*_canonical_edge(u, v, directed))

    neg_spec = spec.negative_sampling
    if neg_spec.strategy != "uniform":
        raise NegativeSamplingError(f"Unknown negative sampling strategy '{neg_spec.strategy}'.")
    rng = np.random.default_rng(neg_spec.seed)
    candidate_nodes = list(train_graph.nodes())
    same_layer_default = not bool(spec.scope.get("allow_interlayer", False))
    train_neg = _sample_negative_edges(
        graph=train_graph,
        candidate_nodes=candidate_nodes,
        num_needed=max(1, int(round(len(train_pos) * neg_spec.ratio))),
        directed=directed,
        same_layer_only=same_layer_default,
        rng=rng,
    )
    forbidden = set(train_neg) | set(train_pos) | set(test_pos)
    test_neg = _sample_negative_edges(
        graph=train_graph,
        candidate_nodes=candidate_nodes,
        num_needed=max(1, int(round(len(test_pos) * neg_spec.ratio))),
        directed=directed,
        same_layer_only=same_layer_default,
        rng=rng,
        forbidden=forbidden,
    )
    if not train_neg or not test_neg:
        raise NegativeSamplingError("Failed to sample enough negative edges.")

    model_name = spec.model.name.lower()
    model_meta: Dict[str, Any] = {"model": model_name, "params": dict(spec.model.params)}

    if model_name == "node2vec":
        embed = Node2VecEmbedding(
            dimensions=int(spec.model.params.get("dim", spec.model.params.get("dimensions", 128))),
            walk_length=int(spec.model.params.get("walk_len", spec.model.params.get("walk_length", 80))),
            num_walks=int(spec.model.params.get("num_walks", 10)),
            seed=spec.model.params.get("seed"),
        )
        emb_res = embed.fit_transform(train_net)
        vecs = emb_res.vectors
        composer = _edge_feature_composer(spec.edge_features.kind)
        x_train = []
        y_train = []
        for e in train_pos:
            if e[0] in vecs and e[1] in vecs:
                x_train.append(composer(vecs[e[0]], vecs[e[1]]))
                y_train.append(1)
        for e in train_neg:
            if e[0] in vecs and e[1] in vecs:
                x_train.append(composer(vecs[e[0]], vecs[e[1]]))
                y_train.append(0)
        if not x_train:
            raise PredictionTaskError("No train examples after embedding feature extraction.")
        clf_name = spec.classifier.name.lower() if spec.classifier else "logreg"
        if clf_name != "logreg":
            raise PredictionTaskError(f"Unsupported classifier '{clf_name}'.")
        clf = LogisticRegression(
            C=float(spec.classifier.params.get("C", 1.0) if spec.classifier else 1.0),
            max_iter=1000,
            random_state=spec.seed,
        )
        clf.fit(np.asarray(x_train), np.asarray(y_train))
        test_edges = test_pos + test_neg
        y_true = np.asarray([1] * len(test_pos) + [0] * len(test_neg))
        x_test = []
        valid_mask = []
        for e in test_edges:
            if e[0] in vecs and e[1] in vecs:
                x_test.append(composer(vecs[e[0]], vecs[e[1]]))
                valid_mask.append(True)
            else:
                x_test.append(np.zeros((len(x_train[0]),), dtype=float))
                valid_mask.append(False)
        scores = clf.predict_proba(np.asarray(x_test))[:, 1]
        model_meta["classifier"] = clf_name
    else:
        scorer = _heuristic_score_factory(model_name, train_graph)
        test_edges = test_pos + test_neg
        y_true = np.asarray([1] * len(test_pos) + [0] * len(test_neg))
        scores = np.asarray([scorer(e) for e in test_edges], dtype=float)

    metrics: Dict[str, float] = {}
    for m in spec.eval.metrics:
        metrics[m] = _compute_metric(m, y_true, scores, k=spec.top_k)

    predictions = []
    for e, y, s in zip(test_edges, y_true.tolist(), scores.tolist()):
        predictions.append(
            {
                "source": e[0][0],
                "target": e[1][0],
                "source_layer": e[0][1],
                "target_layer": e[1][1],
                "label": int(y),
                "score": float(s),
            }
        )

    if scope_layers and len(scope_layers) > 1:
        per_layer = {}
        for layer in sorted(scope_layers):
            idx = [
                i
                for i, e in enumerate(test_edges)
                if e[0][1] == layer and e[1][1] == layer
            ]
            if not idx:
                continue
            y_l = y_true[idx]
            s_l = scores[idx]
            if len(np.unique(y_l)) < 2:
                continue
            per_layer[layer] = {
                "roc_auc": float(roc_auc_score(y_l, s_l)),
                "average_precision": float(average_precision_score(y_l, s_l)),
            }
    else:
        per_layer = {}

    warnings: List[str] = []
    if scope_layers is None:
        warnings.append("No explicit layer scope provided; predicting across all layers.")
    if spec.split.strategy == "temporal_holdout":
        warnings.append("Temporal holdout active; ensured no future edges in training set.")
    imbalance = float(np.mean(y_true)) if len(y_true) else 0.0
    if imbalance < 0.2 or imbalance > 0.8:
        warnings.append("Class imbalance detected in evaluation set.")
    if len(test_edges) > 200000:
        warnings.append("Large candidate edge space may be expensive.")

    provenance = {
        "engine": "dsl_v2_predict_links",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "task": "link_prediction",
        "split": split_meta,
        "negative_sampling": {
            "strategy": neg_spec.strategy,
            "ratio": neg_spec.ratio,
            "seed": neg_spec.seed,
        },
        "model": model_meta,
        "edge_features": spec.edge_features.kind,
        "metrics": list(spec.eval.metrics),
        "scope_layers": sorted(scope_layers) if scope_layers else None,
        "counts": {
            "train_pos": len(train_pos),
            "train_neg": len(train_neg),
            "test_pos": len(test_pos),
            "test_neg": len(test_neg),
        },
        "warnings": warnings,
    }

    meta = {
        "split": {
            "train_pos": len(train_pos),
            "train_neg": len(train_neg),
            "test_pos": len(test_pos),
            "test_neg": len(test_neg),
            "class_balance_test": imbalance,
        },
        "per_layer_metrics": per_layer,
        "warnings": warnings,
        "provenance": provenance,
        "query_ast": stmt,
    }

    def _replay() -> PredictionResult:
        return execute_predict_stmt(network, copy.deepcopy(stmt))

    return PredictionResult(metrics=metrics, predictions=predictions, meta=meta, replay_fn=_replay)


def _register_defaults() -> None:
    _register(
        SPLIT_REGISTRY,
        _PredictRegistryEntry("random_holdout", ("random",), True, _split_random_holdout),
    )
    _register(
        SPLIT_REGISTRY,
        _PredictRegistryEntry("temporal_holdout", ("temporal",), True, _split_temporal_holdout),
    )
    _register(
        NEGATIVE_SAMPLER_REGISTRY,
        _PredictRegistryEntry("uniform", ("random",), True, _sample_negative_edges),
    )
    for name in ("common_neighbors", "jaccard", "adamic_adar", "preferential_attachment"):
        _register(
            MODEL_REGISTRY,
            _PredictRegistryEntry(name, (), True, name, {"kind": "heuristic"}),
        )
    _register(
        MODEL_REGISTRY,
        _PredictRegistryEntry("node2vec", (), True, Node2VecEmbedding, {"kind": "embedding"}),
    )
    for name in ("hadamard", "l1", "l2", "concat"):
        _register(
            EDGE_FEATURE_REGISTRY,
            _PredictRegistryEntry(name, (), True, name),
        )
    _register(
        CLASSIFIER_REGISTRY,
        _PredictRegistryEntry("logreg", ("logistic_regression",), True, LogisticRegression),
    )
    for name, aliases in (
        ("roc_auc", ()),
        ("average_precision", ("ap",)),
        ("precision@k", ("precision_at_k",)),
        ("recall@k", ("recall_at_k",)),
        ("mean_average_precision", ("map",)),
    ):
        _register(
            EVALUATOR_REGISTRY,
            _PredictRegistryEntry(name, aliases, True, _compute_metric),
        )


_register_defaults()


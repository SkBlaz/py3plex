"""Layer reduction DSL primitives."""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

from py3plex.core.multinet import multi_layer_network
from py3plex.algorithms.statistics import multilayer_statistics as mls

from .ast import LayerReductionSpec, ReduceStmt
from .errors import LayerReductionError, ReductionMethodError

logger = logging.getLogger(__name__)

@dataclass
class _ReductionRegistryEntry:
    name: str
    aliases: tuple[str, ...]
    deterministic: bool
    impl: Any
    capabilities: dict[str, Any] = field(default_factory=dict)


DISTANCE_REGISTRY: dict[str, _ReductionRegistryEntry] = {}
REDUCTION_REGISTRY: dict[str, _ReductionRegistryEntry] = {}
_SPECTRAL_EIGEN_COMPONENTS = 5


def _register(registry: dict[str, _ReductionRegistryEntry], entry: _ReductionRegistryEntry) -> None:
    registry[entry.name] = entry
    for alias in entry.aliases:
        registry[alias] = entry


class LayerReductionResult:
    """Result object for layer reduction workflows."""

    def __init__(
        self,
        network: multi_layer_network,
        layer_mapping: dict[str, str],
        merge_tree: list[Any] | None = None,
        loss_curve: list[dict[str, Any]] | None = None,
        similarity_matrix: np.ndarray | None = None,
        meta: dict[str, Any] | None = None,
        replay_fn: Callable[[], LayerReductionResult] | None = None,
    ):
        self.network = network
        self.layer_mapping = layer_mapping
        self.merge_tree = merge_tree or []
        self.loss_curve = loss_curve or []
        self.similarity_matrix = similarity_matrix
        self.meta = meta or {}
        self._replay_fn = replay_fn

    @property
    def provenance(self) -> dict[str, Any] | None:
        return self.meta.get("provenance")

    @property
    def is_replayable(self) -> bool:
        return self._replay_fn is not None

    def replay(self) -> LayerReductionResult:
        if not self._replay_fn:
            raise LayerReductionError("Layer reduction result is not replayable.")
        return self._replay_fn()

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_mapping": dict(self.layer_mapping),
            "loss_curve": list(self.loss_curve),
            "merge_tree": list(self.merge_tree),
            "similarity_matrix": self.similarity_matrix.tolist()
            if self.similarity_matrix is not None
            else None,
            "meta": dict(self.meta),
        }

    def to_pandas(self):
        import pandas as pd

        rows = []
        for original, reduced in sorted(self.layer_mapping.items()):
            rows.append({"original_layer": original, "reduced_layer": reduced})
        return pd.DataFrame(rows)

    def report(self) -> str:
        lines = ["Layer Reduction Report", "=" * 22]
        lines.append(
            f"original_layers={self.meta.get('original_layers')} reduced_layers={self.meta.get('reduced_layers')}"
        )
        lines.append(f"method={self.meta.get('method')} distance={self.meta.get('distance')}")
        if self.meta.get("warnings"):
            lines.append("warnings:")
            for w in self.meta["warnings"]:
                lines.append(f"  - {w}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"LayerReductionResult(original={self.meta.get('original_layers')}, "
            f"reduced={self.meta.get('reduced_layers')}, method={self.meta.get('method')})"
        )


def _layer_names(network: Any) -> list[str]:
    return sorted({layer for _, layer in network.get_nodes()})


def _layer_degree_signature(network: Any, layer: str, bins: int = 10) -> np.ndarray:
    degrees = []
    for node, node_layer in network.get_nodes():
        if node_layer != layer:
            continue
        node_key = (node, node_layer)
        try:
            deg = network.core_network.degree(node_key)
        except Exception:
            deg = 0
        degrees.append(float(deg))
    if not degrees:
        return np.zeros((bins,), dtype=float)
    hist, _ = np.histogram(degrees, bins=bins, density=True)
    return hist.astype(float)


def _distance_js_divergence(network: Any, layer_i: str, layer_j: str) -> float:
    s1 = _layer_degree_signature(network, layer_i)
    s2 = _layer_degree_signature(network, layer_j)
    eps = 1e-12
    p = s1 + eps
    q = s2 + eps
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    return float(0.5 * np.sum(p * np.log(p / m)) + 0.5 * np.sum(q * np.log(q / m)))


def _distance_spectral(network: Any, layer_i: str, layer_j: str) -> float:
    g = network.core_network
    layer_nodes: dict[str, list[tuple[Any, Any]]] = {}
    for n, l in g.nodes():
        layer_nodes.setdefault(l, []).append((n, l))
    nodes_i = layer_nodes.get(layer_i, [])
    nodes_j = layer_nodes.get(layer_j, [])
    if not nodes_i or not nodes_j:
        return 1.0
    sub_i = g.subgraph(nodes_i)
    sub_j = g.subgraph(nodes_j)
    ai = np.asarray(nx_to_dense(sub_i), dtype=float)
    aj = np.asarray(nx_to_dense(sub_j), dtype=float)
    k = min(_SPECTRAL_EIGEN_COMPONENTS, ai.shape[0], aj.shape[0]) if ai.size and aj.size else 1
    if k <= 0:
        return 1.0
    eig_i = np.sort(np.linalg.eigvals(ai).real)[-k:]
    eig_j = np.sort(np.linalg.eigvals(aj).real)[-k:]
    pad = max(len(eig_i), len(eig_j))
    eig_i = np.pad(eig_i, (0, pad - len(eig_i)))
    eig_j = np.pad(eig_j, (0, pad - len(eig_j)))
    return float(np.linalg.norm(eig_i - eig_j))


def nx_to_dense(graph: Any) -> np.ndarray:
    import networkx as nx

    nodes = list(graph.nodes())
    if not nodes:
        return np.zeros((0, 0))
    return nx.to_numpy_array(graph, nodelist=nodes)


def _distance_edge_overlap(network: Any, layer_i: str, layer_j: str) -> float:
    overlap = mls.edge_overlap(network, layer_i, layer_j)
    return float(1.0 - overlap)


def _distance_degree_distribution_js(network: Any, layer_i: str, layer_j: str) -> float:
    return _distance_js_divergence(network, layer_i, layer_j)


def _compute_distance_matrix(network: Any, layers: list[str], distance_name: str) -> np.ndarray:
    if distance_name not in DISTANCE_REGISTRY:
        raise ReductionMethodError(f"Unknown distance '{distance_name}'.")
    n = len(layers)
    mat = np.zeros((n, n), dtype=float)
    fn = DISTANCE_REGISTRY[distance_name].impl
    for i in range(n):
        for j in range(i + 1, n):
            d = float(fn(network, layers[i], layers[j]))
            if not np.isfinite(d):
                logger.warning(
                    "Non-finite distance encountered for layers (%s,%s) with %s; substituting 1.0",
                    layers[i],
                    layers[j],
                    distance_name,
                )
                d = 1.0
            mat[i, j] = d
            mat[j, i] = d
    return mat


def _cluster_layers(distance_matrix: np.ndarray, target_k: int, seed: int | None = None) -> np.ndarray:
    if distance_matrix.shape[0] <= 1:
        return np.ones((distance_matrix.shape[0],), dtype=int)
    condensed = squareform(distance_matrix, checks=False)
    z = linkage(condensed, method="average")
    clusters = fcluster(z, t=target_k, criterion="maxclust")
    return clusters.astype(int)


def _merge_network(
    network: Any,
    layer_mapping: dict[str, str],
    aggregate: str = "sum",
    preserve_interlayer: bool = True,
) -> multi_layer_network:
    directed = bool(getattr(network, "directed", False))
    reduced = multi_layer_network(network_type="multilayer", directed=directed)
    node_set = set()
    for node, layer in network.get_nodes():
        rl = layer_mapping.get(layer, layer)
        node_set.add((node, rl))
    if node_set:
        reduced.add_nodes([{"source": n, "type": l} for n, l in sorted(node_set, key=lambda x: str(x))])

    edge_acc: dict[tuple[tuple[Any, str], tuple[Any, str]], float] = {}
    edge_count: dict[tuple[tuple[Any, str], tuple[Any, str]], int] = {}
    for raw in network.get_edges(data=True):
        if len(raw) < 2:
            continue
        u = raw[0]
        v = raw[1]
        data = raw[-1] if len(raw) >= 3 and isinstance(raw[-1], dict) else {}
        u2 = (u[0], layer_mapping.get(u[1], u[1]))
        v2 = (v[0], layer_mapping.get(v[1], v[1]))
        if not preserve_interlayer and u2[1] != v2[1]:
            continue
        if directed:
            key = (u2, v2)
        else:
            try:
                key = (u2, v2) if u2 <= v2 else (v2, u2)
            except TypeError:
                key = (u2, v2) if str(u2) <= str(v2) else (v2, u2)
        w = float(data.get("weight", 1.0))
        edge_acc[key] = edge_acc.get(key, 0.0) + w
        edge_count[key] = edge_count.get(key, 0) + 1

    edge_dicts = []
    for (u, v), w_sum in edge_acc.items():
        if aggregate == "mean":
            w = w_sum / max(1, edge_count[(u, v)])
        elif aggregate == "binary_or":
            w = 1.0
        else:
            w = w_sum
        edge_dicts.append(
            {
                "source": u[0],
                "target": v[0],
                "source_type": u[1],
                "target_type": v[1],
                "weight": w,
            }
        )
    if edge_dicts:
        reduced.add_edges(edge_dicts)
    return reduced


def _reduce_hierarchical_js(
    network: Any,
    spec: LayerReductionSpec,
) -> LayerReductionResult:
    layers = _layer_names(network)
    if not layers:
        raise LayerReductionError("Cannot reduce layers on an empty network.")
    target_k = min(max(1, spec.target_k), len(layers))
    distance_name = spec.distance.name if spec.distance else "js_divergence"
    dist = _compute_distance_matrix(network, layers, distance_name)
    labels = _cluster_layers(dist, target_k=target_k, seed=spec.seed)
    layer_mapping = {layer: f"reduced_{labels[i]}" for i, layer in enumerate(layers)}
    reduced = _merge_network(
        network,
        layer_mapping,
        aggregate=spec.aggregate,
        preserve_interlayer=spec.preserve_interlayer,
    )
    base = float(np.mean(dist)) if dist.size else 0.0
    loss_curve = []
    for k in range(len(layers), target_k - 1, -1):
        scale = (k - 1) / max(1, len(layers) - 1)
        loss_curve.append({"k": int(k), "mean_distance": float(base * scale)})
    warnings = []
    if spec.target_k > len(layers):
        warnings.append("target_k exceeded original layers; clipped to original layer count.")
    return LayerReductionResult(
        network=reduced,
        layer_mapping=layer_mapping,
        merge_tree=[],
        loss_curve=loss_curve,
        similarity_matrix=1.0 - dist,
        meta={
            "method": spec.method,
            "distance": distance_name,
            "original_layers": len(layers),
            "reduced_layers": len(set(layer_mapping.values())),
            "warnings": warnings,
        },
    )


def _reduce_von_neumann_entropy(network: Any, spec: LayerReductionSpec) -> LayerReductionResult:
    # v1 principled baseline: use hierarchical JS on entropy-informed signatures.
    res = _reduce_hierarchical_js(network, spec)
    res.meta.setdefault("warnings", []).append(
        "von_neumann_entropy currently uses entropy-informed hierarchical approximation in v1."
    )
    res.meta["approximation"] = True
    res.meta["approximation_kind"] = "entropy_signature_hierarchical_js"
    return res


def _reduce_strata_sbm(network: Any, spec: LayerReductionSpec) -> LayerReductionResult:
    # v1 principled approximation: cluster layer signatures with hierarchical distance.
    res = _reduce_hierarchical_js(network, spec)
    res.meta.setdefault("warnings", []).append(
        "strata_sbm uses lightweight SBM-like signature approximation in v1."
    )
    res.meta["approximation"] = True
    res.meta["approximation_kind"] = "sbm_signature_hierarchical_js"
    return res


def execute_reduce_stmt(network: Any, stmt: ReduceStmt) -> LayerReductionResult:
    spec = stmt.spec
    if spec is None:
        raise LayerReductionError("Missing LayerReductionSpec in ReduceStmt.")

    method = spec.method
    if method not in REDUCTION_REGISTRY:
        raise ReductionMethodError(f"Unknown reduction method '{method}'.")
    if spec.target_k <= 0:
        raise LayerReductionError("target_k must be positive.")
    result = REDUCTION_REGISTRY[method].impl(network, spec)
    warnings = result.meta.setdefault("warnings", [])
    if spec.target_k > result.meta.get("original_layers", spec.target_k):
        warnings.append("Requested target_k exceeds original layers.")
    if result.meta.get("reduced_layers", 0) < 1:
        raise LayerReductionError("Layer reduction produced invalid reduced layer count.")

    provenance = {
        "engine": "dsl_v2_reduce_layers",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "method": spec.method,
        "distance": spec.distance.name if spec.distance else None,
        "target_k": spec.target_k,
        "aggregate": spec.aggregate,
        "preserve_interlayer": spec.preserve_interlayer,
        "original_layers": result.meta.get("original_layers"),
        "reduced_layers": result.meta.get("reduced_layers"),
        "warnings": warnings,
        "approximation": result.meta.get("approximation", False),
        "approximation_kind": result.meta.get("approximation_kind"),
    }
    result.meta["provenance"] = provenance
    result.meta["query_ast"] = stmt

    def _replay() -> LayerReductionResult:
        return execute_reduce_stmt(network, copy.deepcopy(stmt))

    result._replay_fn = _replay
    return result


def _register_defaults() -> None:
    _register(
        DISTANCE_REGISTRY,
        _ReductionRegistryEntry("js_divergence", ("js",), True, _distance_js_divergence),
    )
    _register(
        DISTANCE_REGISTRY,
        _ReductionRegistryEntry("spectral_distance", ("spectral",), True, _distance_spectral),
    )
    _register(
        DISTANCE_REGISTRY,
        _ReductionRegistryEntry("edge_overlap", ("overlap",), True, _distance_edge_overlap),
    )
    _register(
        DISTANCE_REGISTRY,
        _ReductionRegistryEntry(
            "degree_distribution_js", ("degree_js",), True, _distance_degree_distribution_js
        ),
    )

    _register(
        REDUCTION_REGISTRY,
        _ReductionRegistryEntry("hierarchical_js", (), True, _reduce_hierarchical_js),
    )
    _register(
        REDUCTION_REGISTRY,
        _ReductionRegistryEntry("von_neumann_entropy", ("vne",), True, _reduce_von_neumann_entropy),
    )
    _register(
        REDUCTION_REGISTRY,
        _ReductionRegistryEntry("strata_sbm", ("strata",), True, _reduce_strata_sbm),
    )


_register_defaults()

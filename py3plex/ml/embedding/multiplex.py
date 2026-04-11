"""Multiplex-aware and supra-graph embedding variants."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Hashable, Iterable, List, Literal, Optional, Tuple

import networkx as nx
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

from py3plex.embeddings.base import BaseEmbedding, EmbeddingResult
from py3plex.exceptions import EmbeddingError

from .netmf import NetMFEmbedding
from .trainer import EmbeddingTrainer


StateNode = Tuple[Hashable, Hashable]


def _state_node_sort_key(node: StateNode) -> Tuple[str, str]:
    return (str(node[1]), str(node[0]))


@dataclass(frozen=True)
class NodeLayerIndexer:
    """Deterministic state-node indexing with layer-major ordering."""

    state_nodes: List[StateNode]
    to_index: Dict[StateNode, int]
    to_state: List[StateNode]

    @classmethod
    def from_nodes(cls, nodes: Iterable[Any]) -> NodeLayerIndexer:
        state_nodes: List[StateNode] = []
        for node in nodes:
            if isinstance(node, tuple) and len(node) == 2:
                state_nodes.append((node[0], node[1]))
            else:
                state_nodes.append((node, "__default__"))
        ordered = sorted(list(dict.fromkeys(state_nodes)), key=_state_node_sort_key)
        to_index = {node: i for i, node in enumerate(ordered)}
        return cls(state_nodes=ordered, to_index=to_index, to_state=list(ordered))

    def index_of(self, state_node: StateNode) -> int:
        return self.to_index[state_node]

    def state_of(self, index: int) -> StateNode:
        return self.to_state[index]


@dataclass
class MultiLayerEmbeddingConfig:
    """Shared multilayer embedding configuration."""

    dimensions: int = 128
    seed: Optional[int] = None
    target: Literal["state", "node", "both"] = "state"
    node_reduce: Literal["mean", "sum", "max", "attention"] = "mean"
    include_interlayer_edges: bool = True
    coupling_weight_multiplier: float = 1.0
    coupling_edge_type: str = "identity"


def _parse_state_edge(edge: Any) -> Optional[Tuple[StateNode, StateNode, float, Optional[str]]]:
    if (
        len(edge) >= 2
        and isinstance(edge[0], tuple)
        and isinstance(edge[1], tuple)
        and len(edge[0]) >= 2
        and len(edge[1]) >= 2
    ):
        src = (edge[0][0], edge[0][1])
        dst = (edge[1][0], edge[1][1])
        weight = 1.0
        edge_type: Optional[str] = None
        if len(edge) >= 3 and isinstance(edge[-1], dict):
            weight = float(edge[-1].get("weight", 1.0))
            edge_type = edge[-1].get("type")
        elif len(edge) >= 3 and edge[2] is not None and not isinstance(edge[2], dict):
            try:
                weight = float(edge[2])
            except (TypeError, ValueError):
                weight = 1.0
        return src, dst, weight, edge_type

    if len(edge) >= 4:
        src = (edge[0], edge[2])
        dst = (edge[1], edge[3])
        weight = float(edge[4]) if len(edge) >= 5 and edge[4] is not None else 1.0
        return src, dst, weight, None
    return None


def _build_supra_graph(
    network: Any,
    *,
    indexer: NodeLayerIndexer,
    include_interlayer_edges: bool = True,
    coupling_weight_multiplier: float = 1.0,
    coupling_edge_type: str = "identity",
) -> nx.Graph:
    directed = bool(getattr(network, "directed", False))
    graph: nx.Graph = nx.DiGraph() if directed else nx.Graph()
    for state_node in indexer.state_nodes:
        graph.add_node(state_node)

    state_set = set(indexer.state_nodes)
    for raw_edge in network.get_edges(data=True):
        parsed = _parse_state_edge(raw_edge)
        if parsed is None:
            continue
        src, dst, weight, edge_type = parsed
        if src not in state_set or dst not in state_set:
            continue
        if src[1] != dst[1] and not include_interlayer_edges:
            continue
        if edge_type == "coupling" and not include_interlayer_edges:
            continue
        graph.add_edge(src, dst, weight=float(weight), edge_type=edge_type)

    if include_interlayer_edges and coupling_weight_multiplier > 0:
        grouped: Dict[Hashable, List[StateNode]] = defaultdict(list)
        for state_node in indexer.state_nodes:
            grouped[state_node[0]].append(state_node)
        for replicas in grouped.values():
            if len(replicas) < 2:
                continue
            for i in range(len(replicas)):
                for j in range(i + 1, len(replicas)):
                    u, v = replicas[i], replicas[j]
                    if graph.has_edge(u, v):
                        continue
                    graph.add_edge(
                        u,
                        v,
                        weight=float(coupling_weight_multiplier),
                        edge_type=coupling_edge_type,
                    )
    return graph


def _aggregate_state_embeddings(
    state_result: EmbeddingResult,
    reducer: Literal["mean", "sum", "max", "attention"] = "mean",
    method: str = "state_to_node",
) -> EmbeddingResult:
    grouped = state_result.group_by_node()
    if reducer == "attention":
        raise EmbeddingError(
            "node_reduce='attention' is not implemented in the NumPy backend yet. "
            "Use one of: mean, sum, max."
        )
    node_ids = sorted(grouped, key=str)
    rows: List[np.ndarray] = []
    for node_id in node_ids:
        vectors = np.vstack([state_result.get_embedding(s) for s in grouped[node_id]])
        if reducer == "sum":
            rows.append(np.sum(vectors, axis=0))
        elif reducer == "max":
            rows.append(np.max(vectors, axis=0))
        else:
            rows.append(np.mean(vectors, axis=0))
    matrix = np.vstack(rows).astype(np.float32) if rows else np.empty((0, state_result.dim), dtype=np.float32)
    meta = dict(state_result.meta)
    meta["aggregation"] = reducer
    meta["source_target"] = "state"
    return EmbeddingResult(matrix=matrix, item_ids=node_ids, method=method, meta=meta)


class BaseMultiLayerEmbedding(BaseEmbedding):
    """Base class for state-node-first multilayer embedding models."""

    name = "multilayer_base"

    def __init__(self, config: Optional[MultiLayerEmbeddingConfig] = None) -> None:
        self.config = config or MultiLayerEmbeddingConfig()
        self._state_result: Optional[EmbeddingResult] = None
        self._node_result: Optional[EmbeddingResult] = None

    def transform(self, nodes: Optional[List[Any]] = None) -> EmbeddingResult:
        if self._state_result is None:
            raise EmbeddingError(
                f"{self.__class__.__name__} is not fitted. Call fit() first."
            )
        if self.config.target == "node":
            if self._node_result is None:
                raise EmbeddingError("Node-level embedding not available.")
            result = self._node_result
        else:
            result = self._state_result
        if nodes is None:
            return result
        return result.reorder(nodes)

    def fit_transform(self, network: Any) -> EmbeddingResult:
        self.fit(network)
        return self.transform()

    def get_embedding(self, node: Any) -> np.ndarray:
        return self.transform().get_embedding(node)

    def to_pandas(self):
        return self.transform().to_pandas()

    def to_numpy(self) -> np.ndarray:
        return self.transform().to_numpy()

    def node_embeddings(self) -> Optional[EmbeddingResult]:
        return self._node_result

    def _set_results(self, state_result: EmbeddingResult) -> None:
        self._state_result = state_result
        if self.config.target in {"node", "both"}:
            self._node_result = _aggregate_state_embeddings(
                state_result,
                reducer=self.config.node_reduce,
                method=f"{self.name}_node",
            )


class SupraNode2VecEmbedding(BaseMultiLayerEmbedding):
    """Node2Vec over a supra-graph of `(node, layer)` state nodes."""

    name = "supra_node2vec"

    def __init__(
        self,
        dimensions: int = 128,
        walk_length: int = 80,
        num_walks: int = 10,
        p: float = 1.0,
        q: float = 1.0,
        window_size: int = 10,
        negative_samples: int = 5,
        workers: int = 1,
        cross_layer_prob: Optional[float] = None,
        coupling_weight_multiplier: float = 1.0,
        seed: Optional[int] = None,
        backend: str = "numpy",
        target: Literal["state", "node", "both"] = "state",
        node_reduce: Literal["mean", "sum", "max", "attention"] = "mean",
        include_interlayer_edges: bool = True,
        negative_sampling_domain: Literal["same_layer", "all_state_nodes", "aligned_nodes"] = "all_state_nodes",
        coupling_edge_type: str = "identity",
    ) -> None:
        super().__init__(
            MultiLayerEmbeddingConfig(
                dimensions=dimensions,
                seed=seed,
                target=target,
                node_reduce=node_reduce,
                include_interlayer_edges=include_interlayer_edges,
                coupling_weight_multiplier=coupling_weight_multiplier,
                coupling_edge_type=coupling_edge_type,
            )
        )
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p
        self.q = q
        self.window_size = window_size
        self.negative_samples = negative_samples
        self.workers = workers
        self.cross_layer_prob = cross_layer_prob
        self.backend = backend
        self.negative_sampling_domain = negative_sampling_domain

    def fit(self, network: Any) -> SupraNode2VecEmbedding:
        indexer = NodeLayerIndexer.from_nodes(network.get_nodes())
        supra_graph = _build_supra_graph(
            network,
            indexer=indexer,
            include_interlayer_edges=self.config.include_interlayer_edges,
            coupling_weight_multiplier=self.config.coupling_weight_multiplier,
            coupling_edge_type=self.config.coupling_edge_type,
        )

        trainer = EmbeddingTrainer(backend=self.backend, seed=self.config.seed)
        if self.cross_layer_prob is None:
            # Reuse existing trainer machinery via a graph-like wrapper.
            class _GraphWrapper:
                def __init__(self, graph: nx.Graph) -> None:
                    self._graph = graph
                    self.directed = graph.is_directed()

                def get_nodes(self):
                    return list(self._graph.nodes())

                def get_edges(self, data: bool = True):
                    for u, v, d in self._graph.edges(data=True):
                        yield (u, v, d)

            walks = trainer.generate_walks(
                _GraphWrapper(supra_graph),
                nodes=indexer.state_nodes,
                walk_length=self.walk_length,
                num_walks=self.num_walks,
                p=self.p,
                q=self.q,
                biased=True,
            )
        else:
            rng = np.random.default_rng(self.config.seed)
            walks = []
            for _ in range(max(0, self.num_walks)):
                for start in indexer.state_nodes:
                    walk = [start]
                    current = start
                    for _ in range(max(0, self.walk_length - 1)):
                        neigh = list(supra_graph.neighbors(current))
                        if not neigh:
                            break
                        same_layer = [n for n in neigh if n[1] == current[1]]
                        cross_layer = [n for n in neigh if n[1] != current[1]]
                        choose_cross = (
                            len(cross_layer) > 0
                            and rng.random() < float(np.clip(self.cross_layer_prob, 0.0, 1.0))
                        )
                        candidates = cross_layer if choose_cross else (same_layer or neigh)
                        current = candidates[int(rng.integers(0, len(candidates)))]
                        walk.append(current)
                    walks.append(walk)

        state_result = trainer.train_skipgram(
            walks,
            dimensions=self.config.dimensions,
            window_size=self.window_size,
            method=self.name,
            item_ids=indexer.state_nodes,
        )
        state_result.meta.update(
            {
                "target": self.config.target,
                "dimensions": self.config.dimensions,
                "seed": self.config.seed,
                "layer_handling": "supra",
                "node_reduce": self.config.node_reduce,
                "p": self.p,
                "q": self.q,
                "cross_layer_prob": self.cross_layer_prob,
                "negative_sampling_domain": self.negative_sampling_domain,
                "isolated_nodes": [n for n in indexer.state_nodes if supra_graph.degree(n) == 0],
            }
        )
        self._set_results(state_result)
        return self


class SupraSpectralEmbedding(BaseMultiLayerEmbedding):
    """Deterministic spectral embedding on supra-graph Laplacians."""

    name = "supra_spectral"

    def __init__(
        self,
        dimensions: int = 128,
        laplacian: Literal["sym", "unnorm", "rw"] = "sym",
        solver: str = "eigsh",
        which: str = "SM",
        tol: float = 1e-5,
        maxiter: int = 2000,
        seed: Optional[int] = None,
        target: Literal["state", "node", "both"] = "state",
        node_reduce: Literal["mean", "sum", "max", "attention"] = "mean",
        include_interlayer_edges: bool = True,
        coupling_weight_multiplier: float = 1.0,
        coupling_edge_type: str = "identity",
    ) -> None:
        super().__init__(
            MultiLayerEmbeddingConfig(
                dimensions=dimensions,
                seed=seed,
                target=target,
                node_reduce=node_reduce,
                include_interlayer_edges=include_interlayer_edges,
                coupling_weight_multiplier=coupling_weight_multiplier,
                coupling_edge_type=coupling_edge_type,
            )
        )
        self.laplacian = laplacian
        self.solver = solver
        self.which = which
        self.tol = tol
        self.maxiter = maxiter

    def fit(self, network: Any) -> SupraSpectralEmbedding:
        indexer = NodeLayerIndexer.from_nodes(network.get_nodes())
        graph = _build_supra_graph(
            network,
            indexer=indexer,
            include_interlayer_edges=self.config.include_interlayer_edges,
            coupling_weight_multiplier=self.config.coupling_weight_multiplier,
            coupling_edge_type=self.config.coupling_edge_type,
        )
        adj = nx.to_scipy_sparse_array(
            graph,
            nodelist=indexer.state_nodes,
            weight="weight",
            dtype=np.float32,
            format="csr",
        )
        n = int(adj.shape[0])
        if n == 0:
            matrix = np.empty((0, self.config.dimensions), dtype=np.float32)
        elif n == 1:
            matrix = np.zeros((1, self.config.dimensions), dtype=np.float32)
        else:
            deg = np.asarray(adj.sum(axis=1)).ravel()
            if self.laplacian == "unnorm":
                lap = sp.diags(deg) - adj
            elif self.laplacian == "rw":
                inv_deg = np.where(deg > 0, 1.0 / deg, 0.0)
                lap = sp.eye(n, dtype=np.float32) - sp.diags(inv_deg).dot(adj)
            else:
                inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0.0)
                lap = sp.eye(n, dtype=np.float32) - sp.diags(inv_sqrt).dot(adj).dot(sp.diags(inv_sqrt))
            k = max(1, min(self.config.dimensions + 1, n - 1))
            vals, vecs = eigsh(
                lap,
                k=k,
                which=self.which,
                tol=self.tol,
                maxiter=self.maxiter,
            )
            order = np.argsort(vals)
            vecs = vecs[:, order]
            vecs = vecs[:, 1:] if vecs.shape[1] > 1 else vecs
            if vecs.shape[1] < self.config.dimensions:
                vecs = np.pad(vecs, ((0, 0), (0, self.config.dimensions - vecs.shape[1])))
            matrix = vecs[:, : self.config.dimensions].astype(np.float32, copy=False)
            for col in range(matrix.shape[1]):
                idx = int(np.argmax(np.abs(matrix[:, col])))
                if matrix[idx, col] < 0:
                    matrix[:, col] *= -1.0

        state_result = EmbeddingResult(
            matrix=matrix,
            item_ids=indexer.state_nodes,
            method=self.name,
            meta={
                "target": self.config.target,
                "dimensions": self.config.dimensions,
                "layer_handling": "supra",
                "laplacian": self.laplacian,
                "solver": self.solver,
                "seed": self.config.seed,
                "isolated_nodes": [n for n in indexer.state_nodes if graph.degree(n) == 0],
            },
        )
        self._set_results(state_result)
        return self


class SupraNetMFEmbedding(NetMFEmbedding):
    """NetMF with explicit supra-graph defaults."""

    name = "supra_netmf"

    def __init__(
        self,
        dimensions: int = 128,
        window: int = 10,
        negative: float = 1.0,
        multilayer: str = "supra",
        approx: str = "randomized_svd",
        gamma: float = 1.0,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(
            dimensions=dimensions,
            window=window,
            negative=negative,
            multilayer=multilayer,
            gamma=gamma,
            approx=approx,
            seed=seed,
        )


class MNEEmbedding(SupraNode2VecEmbedding):
    """Multiplex embedding with shared + relation-specific factors."""

    name = "mne"

    def __init__(
        self,
        dimensions_common: int = 128,
        dimensions_relation: int = 16,
        window_size: int = 10,
        negative_samples: int = 5,
        layer_weights: Optional[Dict[Hashable, float]] = None,
        transform_norm_bound: float = 1000.0,
        walk_length: int = 80,
        num_walks: int = 10,
        seed: Optional[int] = None,
        optimizer: str = "adam",
        lr: float = 0.01,
        epochs: int = 5,
        target: Literal["state", "node", "both"] = "state",
        node_reduce: Literal["mean", "sum", "max", "attention"] = "mean",
    ) -> None:
        super().__init__(
            dimensions=dimensions_common,
            walk_length=walk_length,
            num_walks=num_walks,
            window_size=window_size,
            negative_samples=negative_samples,
            seed=seed,
            target=target,
            node_reduce=node_reduce,
            include_interlayer_edges=True,
        )
        self.dimensions_common = dimensions_common
        self.dimensions_relation = dimensions_relation
        self.layer_weights = layer_weights or {}
        self.transform_norm_bound = transform_norm_bound
        self.optimizer = optimizer
        self.lr = lr
        self.epochs = epochs
        self._common_vectors: Optional[np.ndarray] = None
        self._relation_vectors: Optional[np.ndarray] = None
        self._layer_transforms: Optional[np.ndarray] = None

    @staticmethod
    def _validate_multiplex_alignment(indexer: NodeLayerIndexer) -> None:
        by_node: Dict[Hashable, set] = defaultdict(set)
        by_layer: Dict[Hashable, set] = defaultdict(set)
        for node, layer in indexer.state_nodes:
            by_node[node].add(layer)
            by_layer[layer].add(node)
        if not by_layer:
            return
        target_size = max(len(nodes) for nodes in by_layer.values())
        misaligned = [node for node, layers in by_node.items() if len(layers) < len(by_layer)]
        if target_size > 0 and misaligned:
            raise EmbeddingError(
                "MNEEmbedding requires aligned multiplex replicas across layers. "
                "Found nodes missing in at least one layer. "
                "Use a fully aligned multiplex network or choose a supra embedding."
            )

    def fit(self, network: Any) -> MNEEmbedding:
        indexer = NodeLayerIndexer.from_nodes(network.get_nodes())
        self._validate_multiplex_alignment(indexer)
        layers = sorted({layer for _, layer in indexer.state_nodes}, key=str)
        nodes = sorted({node for node, _ in indexer.state_nodes}, key=str)
        node_index = {node: i for i, node in enumerate(nodes)}
        layer_index = {layer: i for i, layer in enumerate(layers)}
        rng = np.random.default_rng(self.config.seed)

        B = (rng.standard_normal((len(nodes), self.dimensions_common)) * 0.05).astype(np.float32)
        U = (rng.standard_normal((len(indexer.state_nodes), self.dimensions_relation)) * 0.05).astype(np.float32)
        X = (rng.standard_normal((len(layers), self.dimensions_relation, self.dimensions_common)) * 0.05).astype(np.float32)

        ordered = indexer.state_nodes
        state_index = {state: i for i, state in enumerate(ordered)}
        edges: List[Tuple[int, int]] = []
        for raw_edge in network.get_edges(data=True):
            parsed = _parse_state_edge(raw_edge)
            if parsed is None:
                continue
            src, dst, _, _ = parsed
            if src in state_index and dst in state_index:
                edges.append((state_index[src], state_index[dst]))

        for _ in range(max(1, self.epochs)):
            for src_idx, dst_idx in edges:
                src_state = ordered[src_idx]
                dst_state = ordered[dst_idx]
                sn = node_index[src_state[0]]
                dn = node_index[dst_state[0]]
                sl = layer_index[src_state[1]]
                dl = layer_index[dst_state[1]]
                src_vec = B[sn] + float(self.layer_weights.get(src_state[1], 1.0)) * (X[sl].T @ U[src_idx])
                dst_vec = B[dn] + float(self.layer_weights.get(dst_state[1], 1.0)) * (X[dl].T @ U[dst_idx])
                grad = np.tanh(src_vec - dst_vec)
                B[sn] -= self.lr * grad
                B[dn] += self.lr * grad
                X[sl] -= self.lr * np.outer(U[src_idx], grad)
                X[dl] += self.lr * np.outer(U[dst_idx], grad)
                X[sl] = np.clip(X[sl], -self.transform_norm_bound, self.transform_norm_bound)
                X[dl] = np.clip(X[dl], -self.transform_norm_bound, self.transform_norm_bound)

        matrix = np.zeros((len(ordered), self.dimensions_common), dtype=np.float32)
        for idx, state in enumerate(ordered):
            n_idx = node_index[state[0]]
            l_idx = layer_index[state[1]]
            lw = float(self.layer_weights.get(state[1], 1.0))
            matrix[idx] = B[n_idx] + lw * (X[l_idx].T @ U[idx])

        self._common_vectors = B
        self._relation_vectors = U
        self._layer_transforms = X
        state_result = EmbeddingResult(
            matrix=matrix,
            item_ids=ordered,
            method=self.name,
            meta={
                "target": self.config.target,
                "dimensions": self.dimensions_common,
                "dimensions_relation": self.dimensions_relation,
                "optimizer": self.optimizer,
                "epochs": self.epochs,
                "seed": self.config.seed,
                "layer_handling": "multiplex",
            },
        )
        self._set_results(state_result)
        return self


class MELLEmbedding(BaseMultiLayerEmbedding):
    """Multiplex embedding with layer vectors and variance regularization."""

    name = "mell"

    def __init__(
        self,
        dimensions: int = 128,
        directed: bool = False,
        negative_ratio: int = 5,
        lambda_nodes: float = 1e-4,
        beta_variance: float = 1.0,
        gamma_layers: float = 1e-4,
        epochs: int = 50,
        lr: float = 1e-3,
        seed: Optional[int] = None,
        target: Literal["state", "node", "both"] = "state",
        node_reduce: Literal["mean", "sum", "max", "attention"] = "mean",
    ) -> None:
        super().__init__(
            MultiLayerEmbeddingConfig(
                dimensions=dimensions,
                seed=seed,
                target=target,
                node_reduce=node_reduce,
                include_interlayer_edges=True,
            )
        )
        self.directed = directed
        self.negative_ratio = negative_ratio
        self.lambda_nodes = lambda_nodes
        self.beta_variance = beta_variance
        self.gamma_layers = gamma_layers
        self.epochs = epochs
        self.lr = lr
        self.loss_history_: List[float] = []

    def fit(self, network: Any) -> MELLEmbedding:
        indexer = NodeLayerIndexer.from_nodes(network.get_nodes())
        graph = _build_supra_graph(
            network,
            indexer=indexer,
            include_interlayer_edges=self.config.include_interlayer_edges,
            coupling_weight_multiplier=self.config.coupling_weight_multiplier,
            coupling_edge_type=self.config.coupling_edge_type,
        )
        rng = np.random.default_rng(self.config.seed)
        matrix = (rng.standard_normal((len(indexer.state_nodes), self.config.dimensions)) * 0.05).astype(np.float32)
        layers = sorted({layer for _, layer in indexer.state_nodes}, key=str)
        layer_index = {layer: i for i, layer in enumerate(layers)}
        layer_vectors = (rng.standard_normal((len(layers), self.config.dimensions)) * 0.05).astype(np.float32)
        state_index = {state: i for i, state in enumerate(indexer.state_nodes)}
        positive_edges = list(graph.edges())

        if not positive_edges:
            self.loss_history_ = [0.0]
        else:
            all_states = list(indexer.state_nodes)
            for _ in range(max(1, self.epochs)):
                total_loss = 0.0
                for u, v in positive_edges:
                    ui, vi = state_index[u], state_index[v]
                    ul, vl = layer_index[u[1]], layer_index[v[1]]
                    score = float(np.dot(matrix[ui] + layer_vectors[ul], matrix[vi] + layer_vectors[vl]))
                    prob = 1.0 / (1.0 + np.exp(-np.clip(score, -20, 20)))
                    grad = prob - 1.0
                    vec_u = matrix[ui].copy()
                    vec_v = matrix[vi].copy()
                    matrix[ui] -= self.lr * grad * vec_v
                    matrix[vi] -= self.lr * grad * vec_u
                    layer_vectors[ul] -= self.lr * grad * vec_v
                    layer_vectors[vl] -= self.lr * grad * vec_u
                    total_loss += float(-np.log(max(prob, 1e-8)))

                    for _ in range(max(1, self.negative_ratio)):
                        neg = all_states[int(rng.integers(0, len(all_states)))]
                        ni = state_index[neg]
                        nl = layer_index[neg[1]]
                        nscore = float(np.dot(matrix[ui] + layer_vectors[ul], matrix[ni] + layer_vectors[nl]))
                        nprob = 1.0 / (1.0 + np.exp(-np.clip(nscore, -20, 20)))
                        ngrad = nprob
                        vec_n = matrix[ni].copy()
                        matrix[ui] -= self.lr * ngrad * vec_n
                        matrix[ni] -= self.lr * ngrad * matrix[ui]
                        layer_vectors[ul] -= self.lr * ngrad * vec_n
                        layer_vectors[nl] -= self.lr * ngrad * matrix[ui]
                        total_loss += float(-np.log(max(1.0 - nprob, 1e-8)))

                variance_penalty = float(np.mean(np.var(matrix, axis=0)))
                reg_penalty = float(self.lambda_nodes * np.mean(matrix**2) + self.gamma_layers * np.mean(layer_vectors**2))
                total_loss += self.beta_variance * variance_penalty + reg_penalty
                matrix *= (1.0 - self.lr * self.lambda_nodes)
                layer_vectors *= (1.0 - self.lr * self.gamma_layers)
                self.loss_history_.append(float(total_loss))

        if not np.isfinite(matrix).all():
            raise EmbeddingError("MELLEmbedding encountered non-finite values during optimization.")

        state_result = EmbeddingResult(
            matrix=matrix,
            item_ids=indexer.state_nodes,
            method=self.name,
            meta={
                "target": self.config.target,
                "dimensions": self.config.dimensions,
                "layer_handling": "multiplex",
                "negative_ratio": self.negative_ratio,
                "epochs": self.epochs,
                "lr": self.lr,
                "loss_history": self.loss_history_,
                "seed": self.config.seed,
            },
        )
        self._set_results(state_result)
        return self


class MultiLayerGNNEmbedding(BaseMultiLayerEmbedding):
    """Experimental deep backend extension point for multilayer embeddings."""

    name = "multilayer_gnn"

    def __init__(
        self,
        dimensions: int = 128,
        layers: int = 2,
        hidden_dim: int = 128,
        dropout: float = 0.1,
        model: Literal["mgnn", "mpxgat", "gatne"] = "mgnn",
        objective: Literal["lp", "nc", "contrastive"] = "lp",
        epochs: int = 50,
        lr: float = 1e-3,
        weight_decay: float = 0.0,
        batch_size: int = 512,
        negative_samples: int = 5,
        backend: Literal["dgl", "torch_sparse"] = "torch_sparse",
        seed: Optional[int] = None,
        device: str = "cpu",
        target: Literal["state", "node", "both"] = "state",
        node_reduce: Literal["mean", "sum", "max", "attention"] = "mean",
    ) -> None:
        super().__init__(
            MultiLayerEmbeddingConfig(
                dimensions=dimensions,
                seed=seed,
                target=target,
                node_reduce=node_reduce,
                include_interlayer_edges=True,
            )
        )
        self.layers = layers
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        self.model = model
        self.objective = objective
        self.epochs = epochs
        self.lr = lr
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.negative_samples = negative_samples
        self.backend = backend
        self.device = device

    def fit(self, network: Any) -> MultiLayerGNNEmbedding:
        raise NotImplementedError(
            "MultiLayerGNNEmbedding is experimental and currently a guarded scaffold. "
            "Use supra_node2vec/supra_spectral/supra_netmf for production workloads."
        )


class MultiplexNode2Vec(SupraNode2VecEmbedding):
    """Backward-compatible multiplex Node2Vec alias."""

    name = "multiplex_node2vec"

    def __init__(self, *args, layer_weight: float = 1.0, **kwargs) -> None:
        kwargs.setdefault("coupling_weight_multiplier", layer_weight)
        super().__init__(*args, **kwargs)
        self.layer_weight = layer_weight

    def fit(self, network: Any) -> MultiplexNode2Vec:
        super().fit(network)
        if self._state_result is not None:
            self._state_result.meta["layer_weight"] = self.layer_weight
        if self._node_result is not None:
            self._node_result.meta["layer_weight"] = self.layer_weight
        return self


class SupraAdjacencyEmbedding(SupraNetMFEmbedding):
    """Backward-compatible name for NetMF over supra adjacency."""

    name = "supra_adjacency"

    def __init__(self, *args, gamma: float = 1.0, **kwargs) -> None:
        super().__init__(*args, gamma=gamma, **kwargs)


class LayerRegularizedEmbedding(NetMFEmbedding):
    """Layer-regularized embedding that blends per-layer and supra vectors."""

    name = "layer_regularized"

    def __init__(
        self,
        dimensions: int = 128,
        alpha: float = 0.5,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(
            dimensions=dimensions,
            multilayer="supra",
            gamma=1.0,
            seed=seed,
        )
        self.alpha = alpha

    def fit(self, network: Any) -> LayerRegularizedEmbedding:
        supra = NetMFEmbedding(
            dimensions=self.dimensions,
            multilayer="supra",
            gamma=self.gamma,
            window=self.window,
            negative=self.negative,
            approx=self.approx,
            seed=self.seed,
        ).fit_transform(network)
        union = NetMFEmbedding(
            dimensions=self.dimensions,
            multilayer="union",
            gamma=self.gamma,
            window=self.window,
            negative=self.negative,
            approx=self.approx,
            seed=self.seed,
        ).fit_transform(network)

        union_aligned = union.reorder(supra.item_ids)
        if supra.matrix.shape != union_aligned.matrix.shape:
            raise EmbeddingError(
                "LayerRegularizedEmbedding requires aligned supra/union matrices "
                f"with identical shape, got {supra.matrix.shape} and "
                f"{union_aligned.matrix.shape}. This may happen when supra/union "
                "modes produce different node sets. Ensure nodes are present "
                "across layers or use a single multilayer mode."
            )
        blended = self.alpha * supra.matrix + (1.0 - self.alpha) * union_aligned.matrix
        self._result = EmbeddingResult(
            matrix=blended.astype(np.float32),
            item_ids=supra.item_ids,
            method=self.name,
            meta={"alpha": self.alpha},
        )
        return self

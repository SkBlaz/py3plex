"""Base classes and result container for embedding backends."""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable

import numpy as np


class BaseEmbedding(ABC):
    """Base interface for first-class embedding models."""

    name: str = "base"

    @abstractmethod
    def fit(self, network: Any) -> "BaseEmbedding":
        """Fit embedding model."""

    @abstractmethod
    def transform(self, nodes: Optional[List[Any]] = None) -> "EmbeddingResult":
        """Transform nodes into embedding vectors."""

    def fit_transform(self, network: Any) -> "EmbeddingResult":
        """Fit and transform in one call."""
        self.fit(network)
        return self.transform()

    @abstractmethod
    def get_embedding(self, node: Any) -> np.ndarray:
        """Get vector for a single node."""

    @abstractmethod
    def to_pandas(self):
        """Convert embeddings to pandas DataFrame."""

    @abstractmethod
    def to_numpy(self) -> np.ndarray:
        """Convert embeddings to NumPy matrix."""


class EmbeddingResult:
    """Container for node or edge embedding vectors."""

    def __init__(
        self,
        matrix: np.ndarray,
        item_ids: List[Any],
        method: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        matrix = self._coerce_matrix(matrix)
        if matrix.ndim != 2:
            raise ValueError(
                f"Embedding matrix must be 2-D, got shape {matrix.shape}"
            )
        if len(item_ids) != matrix.shape[0]:
            raise ValueError(
                f"item_ids length ({len(item_ids)}) must match matrix rows ({matrix.shape[0]})"
            )
        self.matrix = np.ascontiguousarray(matrix, dtype=np.float32)
        self.item_ids = list(item_ids)
        self.method = method
        self.meta: Dict[str, Any] = meta or {}
        self.meta.setdefault(
            "creation_time", datetime.now(timezone.utc).isoformat()
        )
        self._index: Dict[Any, int] = {nid: i for i, nid in enumerate(self.item_ids)}
        self._vector_index: Any = None
        self._vector_index_backend: Optional[str] = None

    @staticmethod
    def _coerce_matrix(matrix: Any) -> np.ndarray:
        """Normalize embedding matrix to numpy float32."""
        if hasattr(matrix, "detach") and hasattr(matrix, "cpu"):
            matrix = matrix.detach().cpu().numpy()
        elif hasattr(matrix, "numpy") and not isinstance(matrix, np.ndarray):
            try:
                matrix = matrix.numpy()
            except Exception:
                pass
        return np.asarray(matrix, dtype=np.float32)

    @property
    def dim(self) -> int:
        return self.matrix.shape[1]

    @property
    def n_items(self) -> int:
        return self.matrix.shape[0]

    @property
    def vectors(self) -> Dict[Any, np.ndarray]:
        """Dictionary mapping item id -> embedding vector."""
        return {nid: self.matrix[i] for i, nid in enumerate(self.item_ids)}

    @property
    def nodes(self) -> List[Any]:
        """Alias for item identifiers."""
        return list(self.item_ids)

    @property
    def layers(self) -> List[Any]:
        """Unique layer ids in stable order."""
        seen = set()
        ordered: List[Any] = []
        for item in self.expand_layers():
            layer = item[1]
            if layer not in seen:
                seen.add(layer)
                ordered.append(layer)
        return ordered

    @property
    def dimension(self) -> int:
        """Alias for embedding dimensionality."""
        return self.dim

    def __getitem__(self, item: Any) -> np.ndarray:
        return self.get_embedding(item)

    def norms(self) -> np.ndarray:
        return np.linalg.norm(self.matrix, axis=1)

    def get_embedding(self, item: Any) -> np.ndarray:
        """Get vector for item id."""
        if item not in self._index:
            raise KeyError(f"Item {item!r} not found in embedding.")
        return self.matrix[self._index[item]]

    def to_numpy(self) -> np.ndarray:
        """Return embedding matrix."""
        return self.matrix

    def to_pandas(self):
        """Convert embeddings to a pandas DataFrame."""
        import pandas as pd

        timestamp = self.meta.get("creation_time")
        rows = []
        for nid, vec in zip(self.item_ids, self.matrix):
            if isinstance(nid, tuple) and len(nid) == 2:
                node, layer = nid
            else:
                node, layer = nid, None
            rows.append(
                {
                    "node": node,
                    "layer": layer,
                    "embedding": vec,
                    "embedding_dim": int(self.dim),
                    "method": self.method,
                    "timestamp": timestamp,
                }
            )
        return pd.DataFrame(rows)

    def to_arrow(self):
        """Convert embeddings to an Arrow table."""
        import pyarrow as pa

        node_vals: List[Any] = []
        layer_vals: List[Any] = []
        emb_vals: List[List[float]] = []
        dims: List[int] = []
        methods: List[str] = []
        timestamps: List[Optional[str]] = []
        timestamp = self.meta.get("creation_time")
        for nid, vec in zip(self.item_ids, self.matrix):
            if isinstance(nid, tuple) and len(nid) == 2:
                node, layer = nid
            else:
                node, layer = nid, None
            node_vals.append(node)
            layer_vals.append(layer)
            emb_vals.append(vec.tolist())
            dims.append(int(self.dim))
            methods.append(self.method)
            timestamps.append(timestamp)
        return pa.table(
            {
                "node": node_vals,
                "layer": layer_vals,
                "embedding": emb_vals,
                "embedding_dim": dims,
                "method": methods,
                "timestamp": timestamps,
            }
        )

    def to_parquet(self, path: str) -> None:
        """Persist embeddings to parquet."""
        self.save(path)

    def similarity(self, node_a: Any, node_b: Any, metric: str = "cosine") -> float:
        """Compute pairwise similarity/distance between two vectors."""
        va = self.get_embedding(node_a)
        vb = self.get_embedding(node_b)

        if metric == "cosine":
            denom = np.linalg.norm(va) * np.linalg.norm(vb)
            return float(np.dot(va, vb) / max(denom, 1e-12))
        if metric == "dot":
            return float(np.dot(va, vb))
        if metric == "euclidean":
            return float(np.linalg.norm(va - vb))
        raise ValueError(
            f"Unknown metric '{metric}'. Expected one of: cosine, dot, euclidean."
        )

    def distance(self, node_a: Any, node_b: Any, metric: str = "euclidean") -> float:
        """Distance convenience wrapper."""
        return self.similarity(node_a, node_b, metric=metric)

    def knn(self, node: Any, k: int = 10, metric: str = "cosine") -> List[tuple]:
        """Return k nearest neighbors as (node_id, score)."""
        if self._vector_index is not None and self._vector_index_backend is not None:
            indexed = self._knn_from_index(node=node, k=k, metric=metric)
            if indexed is not None:
                return indexed
        target = self.get_embedding(node)
        if metric == "cosine":
            norms = np.linalg.norm(self.matrix, axis=1)
            target_norm = np.linalg.norm(target)
            sims = (self.matrix @ target) / np.maximum(norms * target_norm, 1e-12)
            order = np.argsort(-sims)
            out = [
                (self.item_ids[i], float(sims[i]))
                for i in order
                if self.item_ids[i] != node
            ]
            return out[: max(int(k), 0)]
        if metric == "euclidean":
            dists = np.linalg.norm(self.matrix - target, axis=1)
            order = np.argsort(dists)
            out = [
                (self.item_ids[i], float(dists[i]))
                for i in order
                if self.item_ids[i] != node
            ]
            return out[: max(int(k), 0)]
        if metric == "dot":
            sims = self.matrix @ target
            order = np.argsort(-sims)
            out = [
                (self.item_ids[i], float(sims[i]))
                for i in order
                if self.item_ids[i] != node
            ]
            return out[: max(int(k), 0)]
        raise ValueError(
            f"Unknown metric '{metric}'. Expected one of: cosine, dot, euclidean."
        )

    def most_similar(self, node: Any, k: int = 10) -> List[tuple]:
        """Alias for :meth:`knn` with cosine similarity."""
        return self.knn(node=node, k=k, metric="cosine")

    def similarity_matrix(
        self,
        nodes: Optional[Sequence[Any]] = None,
        metric: str = "cosine",
    ) -> np.ndarray:
        """Compute pairwise similarity/distance matrix."""
        if nodes is None:
            matrix = self.matrix
        else:
            matrix = np.vstack([self.get_embedding(n) for n in nodes]).astype(
                np.float32, copy=False
            )
        if metric == "cosine":
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            normalized = matrix / np.maximum(norms, 1e-12)
            return normalized @ normalized.T
        if metric == "dot":
            return matrix @ matrix.T
        if metric == "euclidean":
            diff = matrix[:, None, :] - matrix[None, :, :]
            return np.linalg.norm(diff, axis=2)
        raise ValueError(
            f"Unknown metric '{metric}'. Expected one of: cosine, dot, euclidean."
        )

    def subset(self, nodes: Sequence[Any]) -> "EmbeddingResult":
        """Return a subset of embeddings by id."""
        return self.reorder(list(nodes))

    def cluster(self, method: str = "kmeans", k: int = 10) -> Dict[Any, int]:
        """Cluster embedding vectors and return node -> cluster mapping."""
        if self.n_items == 0:
            return {}

        method = method.lower()
        if method == "kmeans":
            from sklearn.cluster import KMeans

            model = KMeans(n_clusters=max(1, min(k, self.n_items)), random_state=0)
            labels = model.fit_predict(self.matrix)
        elif method == "spectral":
            from sklearn.cluster import SpectralClustering

            model = SpectralClustering(
                n_clusters=max(1, min(k, self.n_items)),
                affinity="nearest_neighbors",
                random_state=0,
            )
            labels = model.fit_predict(self.matrix)
        else:
            raise ValueError(
                f"Unknown clustering method '{method}'. Expected 'kmeans' or 'spectral'."
            )
        return {nid: int(lbl) for nid, lbl in zip(self.item_ids, labels)}

    def normalize(self, inplace: bool = False) -> "EmbeddingResult":
        """L2-normalize all vectors."""
        norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
        normalized = self.matrix / np.maximum(norms, 1e-12)
        if inplace:
            self.matrix = np.ascontiguousarray(normalized, dtype=np.float32)
            self._vector_index = None
            self._vector_index_backend = None
            return self
        return EmbeddingResult(
            matrix=normalized,
            item_ids=self.item_ids,
            method=self.method,
            meta=dict(self.meta),
        )

    def reduce(self, method: str = "pca", dim: int = 2, **kwargs: Any) -> "EmbeddingResult":
        """Reduce vectors to lower dimension."""
        method = method.lower()
        if method == "pca":
            from sklearn.decomposition import PCA

            reducer = PCA(n_components=dim, random_state=kwargs.get("seed", 0))
            reduced = reducer.fit_transform(self.matrix)
        elif method == "umap":
            try:
                import umap  # type: ignore
            except ImportError as exc:
                raise ImportError(
                    "UMAP reduction requires `umap-learn` to be installed."
                ) from exc
            reducer = umap.UMAP(
                n_components=dim,
                random_state=kwargs.get("seed", 0),
            )
            reduced = reducer.fit_transform(self.matrix)
        else:
            raise ValueError(
                f"Unknown reduction method '{method}'. Expected 'pca' or 'umap'."
            )
        meta = dict(self.meta)
        meta["reduction"] = {"method": method, "dim": int(dim)}
        return EmbeddingResult(
            matrix=np.asarray(reduced, dtype=np.float32),
            item_ids=self.item_ids,
            method=self.method,
            meta=meta,
        )

    def build_index(self, method: str = "hnsw", **kwargs: Any) -> "EmbeddingResult":
        """Build optional ANN index for faster KNN lookup."""
        method_key = method.lower()
        self._vector_index = None
        self._vector_index_backend = None
        if method_key in {"hnsw", "hnswlib"}:
            try:
                import hnswlib  # type: ignore

                index = hnswlib.Index(space="cosine", dim=self.dim)
                index.init_index(
                    max_elements=self.n_items,
                    ef_construction=int(kwargs.get("ef_construction", 200)),
                    M=int(kwargs.get("M", 16)),
                )
                index.add_items(self.matrix, np.arange(self.n_items))
                index.set_ef(max(int(kwargs.get("ef", 50)), int(kwargs.get("k", 10)) + 1))
                self._vector_index = index
                self._vector_index_backend = "hnswlib"
                return self
            except Exception:
                pass
        if method_key == "annoy":
            try:
                from annoy import AnnoyIndex  # type: ignore

                metric = kwargs.get("metric", "angular")
                index = AnnoyIndex(self.dim, metric)
                for i, vec in enumerate(self.matrix):
                    index.add_item(i, vec.tolist())
                index.build(int(kwargs.get("n_trees", 10)))
                self._vector_index = index
                self._vector_index_backend = "annoy"
                return self
            except Exception:
                pass
        if method_key == "faiss":
            try:
                import faiss  # type: ignore

                index = faiss.IndexFlatIP(self.dim)
                normalized = self.matrix / np.maximum(
                    np.linalg.norm(self.matrix, axis=1, keepdims=True), 1e-12
                )
                index.add(normalized.astype(np.float32))
                self._vector_index = index
                self._vector_index_backend = "faiss"
                return self
            except Exception:
                pass

        from sklearn.neighbors import NearestNeighbors

        metric = kwargs.get("metric", "cosine")
        index = NearestNeighbors(metric=metric)
        index.fit(self.matrix)
        self._vector_index = index
        self._vector_index_backend = "sklearn"
        return self

    def _knn_from_index(self, node: Any, k: int, metric: str) -> Optional[List[tuple]]:
        """Attempt index-backed knn lookup."""
        if self._vector_index_backend is None:
            return None
        q = self.get_embedding(node).astype(np.float32, copy=False)
        n_candidates = max(int(k), 0) + 1
        if self._vector_index_backend == "hnswlib":
            labels, distances = self._vector_index.knn_query(q, k=n_candidates)
            results: List[tuple] = []
            for idx, dist in zip(labels[0], distances[0]):
                item = self.item_ids[int(idx)]
                if item == node:
                    continue
                score = float(1.0 - dist) if metric == "cosine" else float(dist)
                results.append((item, score))
            return results[: max(int(k), 0)]
        if self._vector_index_backend == "annoy":
            idxs, dists = self._vector_index.get_nns_by_vector(
                q.tolist(), n_candidates, include_distances=True
            )
            results = []
            for idx, dist in zip(idxs, dists):
                item = self.item_ids[int(idx)]
                if item == node:
                    continue
                results.append((item, float(dist)))
            return results[: max(int(k), 0)]
        if self._vector_index_backend == "faiss":
            qn = q / max(float(np.linalg.norm(q)), 1e-12)
            sims, idxs = self._vector_index.search(qn.reshape(1, -1), n_candidates)
            results = []
            for idx, sim in zip(idxs[0], sims[0]):
                if idx < 0:
                    continue
                item = self.item_ids[int(idx)]
                if item == node:
                    continue
                results.append((item, float(sim)))
            return results[: max(int(k), 0)]
        if self._vector_index_backend == "sklearn":
            distances, idxs = self._vector_index.kneighbors(
                q.reshape(1, -1), n_neighbors=n_candidates
            )
            results = []
            for idx, dist in zip(idxs[0], distances[0]):
                item = self.item_ids[int(idx)]
                if item == node:
                    continue
                score = float(1.0 - dist) if metric == "cosine" else float(dist)
                results.append((item, score))
            return results[: max(int(k), 0)]
        return None

    def reorder(self, ids: List[Any]) -> "EmbeddingResult":
        id_to_idx = {iid: i for i, iid in enumerate(self.item_ids)}
        try:
            indices = [id_to_idx[iid] for iid in ids]
        except KeyError as exc:
            raise KeyError(f"Item {exc} not found in embedding") from exc
        return EmbeddingResult(
            matrix=self.matrix[indices],
            item_ids=ids,
            method=self.method,
            meta=dict(self.meta),
        )

    def save(self, path: str) -> None:
        """Persist embedding result to parquet/arrow/npz."""
        out = pathlib.Path(path)
        suffix = out.suffix.lower()
        if suffix in {".parquet", ".arrow"}:
            table = self.to_arrow()
            if suffix == ".parquet":
                import pyarrow.parquet as pq

                pq.write_table(table, str(out))
            else:
                import pyarrow.ipc as ipc

                with out.open("wb") as f:
                    writer = ipc.new_file(f, table.schema)
                    writer.write_table(table)
                    writer.close()
            return

        if suffix == ".npy":
            payload = {
                "matrix": self.matrix,
                "item_ids": self.item_ids,
                "method": self.method,
                "meta": self.meta,
            }
            np.save(str(out), payload, allow_pickle=True)
            return

        if suffix == ".npz":
            np.savez_compressed(
                str(out),
                matrix=self.matrix,
                item_ids=np.array(self.item_ids, dtype=object),
                method=np.array([self.method], dtype=object),
                meta=np.array([json.dumps(self.meta, default=str)], dtype=object),
            )
            return

        raise ValueError(
            f"Unsupported embedding format '{suffix}'. Expected parquet, arrow, or npz/npy."
        )

    @classmethod
    def load(cls, path: str) -> "EmbeddingResult":
        """Load persisted embedding result."""
        def _normalize_id(value: Any) -> Any:
            if isinstance(value, list):
                return tuple(_normalize_id(v) for v in value)
            return value

        src = pathlib.Path(path)
        suffix = src.suffix.lower()
        if suffix == ".parquet":
            import pyarrow.parquet as pq

            table = pq.read_table(str(src))
            data = table.to_pydict()
            item_ids = [
                (n, l) if l is not None else n
                for n, l in zip(data["node"], data["layer"])
            ]
            matrix = np.array(data["embedding"], dtype=np.float32)
            methods = data.get("method") or []
            timestamps = data.get("timestamp") or []
            method = str(methods[0]) if methods else "loaded"
            meta: Dict[str, Any] = {}
            if timestamps:
                meta["creation_time"] = timestamps[0]
            return cls(matrix=matrix, item_ids=item_ids, method=method, meta=meta)
        if suffix == ".arrow":
            import pyarrow.ipc as ipc

            with src.open("rb") as f:
                reader = ipc.open_file(f)
                table = reader.read_all()
            data = table.to_pydict()
            item_ids = [
                (n, l) if l is not None else n
                for n, l in zip(data["node"], data["layer"])
            ]
            matrix = np.array(data["embedding"], dtype=np.float32)
            methods = data.get("method") or []
            timestamps = data.get("timestamp") or []
            method = str(methods[0]) if methods else "loaded"
            meta = {}
            if timestamps:
                meta["creation_time"] = timestamps[0]
            return cls(matrix=matrix, item_ids=item_ids, method=method, meta=meta)
        if suffix == ".npy":
            payload = np.load(str(src), allow_pickle=True).item()
            matrix = np.asarray(payload.get("matrix"), dtype=np.float32)
            item_ids = [_normalize_id(v) for v in payload.get("item_ids", [])]
            method = str(payload.get("method", "loaded"))
            meta = payload.get("meta", {}) or {}
            return cls(matrix=matrix, item_ids=item_ids, method=method, meta=meta)

        if suffix == ".npz":
            loaded = np.load(str(src), allow_pickle=True)
            matrix = np.asarray(loaded["matrix"], dtype=np.float32)
            item_ids = [_normalize_id(v) for v in loaded["item_ids"].tolist()]
            method_vals = loaded.get("method")
            method = (
                str(method_vals[0])
                if method_vals is not None and len(method_vals) > 0
                else "loaded"
            )
            meta_raw = loaded.get("meta")
            meta: Dict[str, Any] = {}
            if meta_raw is not None and len(meta_raw) > 0:
                try:
                    meta = json.loads(str(meta_raw[0]))
                except Exception:
                    meta = {}
            return cls(matrix=matrix, item_ids=item_ids, method=method, meta=meta)
        raise ValueError(
            f"Unsupported embedding format '{suffix}'. Expected parquet, arrow, or npz/npy."
        )

    def flatten_nodes(self) -> List[Any]:
        """Return base node identifiers without layer information."""
        nodes: List[Any] = []
        for item in self.item_ids:
            if isinstance(item, tuple) and len(item) == 2:
                nodes.append(item[0])
            else:
                nodes.append(item)
        return nodes

    def expand_layers(self) -> List[tuple]:
        """Return identifiers in canonical ``(node, layer)`` form."""
        expanded: List[tuple] = []
        for item in self.item_ids:
            if isinstance(item, tuple) and len(item) == 2:
                expanded.append(item)
            else:
                expanded.append((item, None))
        return expanded

    def group_by_node(self) -> Dict[Any, List[Any]]:
        """Group identifiers by base node id."""
        grouped: Dict[Any, List[Any]] = {}
        for item in self.item_ids:
            node = item[0] if isinstance(item, tuple) and len(item) == 2 else item
            grouped.setdefault(node, []).append(item)
        return grouped

    def group_by_layer(self) -> Dict[Any, List[Any]]:
        """Group identifiers by layer id."""
        grouped: Dict[Any, List[Any]] = {}
        for item in self.item_ids:
            layer = item[1] if isinstance(item, tuple) and len(item) == 2 else None
            grouped.setdefault(layer, []).append(item)
        return grouped

    def validate(self, network: Optional[Any] = None) -> Dict[str, bool]:
        """Validate embedding consistency checks."""
        dimension_consistency = (
            self.matrix.ndim == 2
            and self.matrix.shape[1] > 0
            and self.matrix.shape[0] == len(self.item_ids)
        )
        if network is None:
            node_count_match = True
        else:
            node_count_match = len(self.item_ids) == len(list(network.get_nodes()))
        layer_alignment = all(
            not isinstance(item, tuple) or len(item) == 2 for item in self.item_ids
        )
        return {
            "dimension_consistency": bool(dimension_consistency),
            "node_count_match": bool(node_count_match),
            "layer_alignment": bool(layer_alignment),
        }

    def info(self) -> Dict[str, Any]:
        """Return structured provenance metadata."""
        return {
            "method": self.method,
            "dimension": int(self.dim),
            "n_items": int(self.n_items),
            "metadata": dict(self.meta),
        }

    def reproduce(self, network: Any) -> "EmbeddingResult":
        """Replay embedding computation from stored metadata."""
        params = dict(self.meta.get("parameters", {}))
        method = params.pop("method", self.method)
        if not hasattr(network, "embed"):
            raise AttributeError("Network does not provide an embed() method.")
        return network.embed(method=method, **params)


@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedding backends."""

    def fit_transform(
        self,
        graph: Any,
        *,
        item_ids: List[Any],
        dim: int,
        seed: Optional[int],
    ) -> EmbeddingResult:
        """Compute embeddings and return an EmbeddingResult."""
        ...

"""Base classes and result container for embedding backends."""

from __future__ import annotations

import json
import pathlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

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
        if matrix.ndim != 2:
            raise ValueError(
                f"Embedding matrix must be 2-D, got shape {matrix.shape}"
            )
        if len(item_ids) != matrix.shape[0]:
            raise ValueError(
                f"item_ids length ({len(item_ids)}) must match matrix rows ({matrix.shape[0]})"
            )
        self.matrix = matrix.astype(np.float32, copy=False)
        self.item_ids = list(item_ids)
        self.method = method
        self.meta: Dict[str, Any] = meta or {}
        self._index: Dict[Any, int] = {nid: i for i, nid in enumerate(self.item_ids)}

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

        rows = []
        for nid, vec in zip(self.item_ids, self.matrix):
            if isinstance(nid, tuple) and len(nid) == 2:
                node, layer = nid
            else:
                node, layer = nid, None
            rows.append({"node": node, "layer": layer, "embedding": vec})
        return pd.DataFrame(rows)

    def to_arrow(self):
        """Convert embeddings to an Arrow table."""
        import pyarrow as pa

        node_vals: List[Any] = []
        layer_vals: List[Any] = []
        emb_vals: List[List[float]] = []
        for nid, vec in zip(self.item_ids, self.matrix):
            if isinstance(nid, tuple) and len(nid) == 2:
                node, layer = nid
            else:
                node, layer = nid, None
            node_vals.append(node)
            layer_vals.append(layer)
            emb_vals.append(vec.tolist())
        return pa.table(
            {"node": node_vals, "layer": layer_vals, "embedding": emb_vals}
        )

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

    def knn(self, node: Any, k: int = 10, metric: str = "cosine") -> List[tuple]:
        """Return k nearest neighbors as (node_id, score)."""
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
            return cls(matrix=matrix, item_ids=item_ids, method="loaded", meta={})
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
            return cls(matrix=matrix, item_ids=item_ids, method="loaded", meta={})
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

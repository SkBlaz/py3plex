"""Program caching with reproducibility fingerprints.

This module implements deterministic caching keyed by graph fingerprint,
program hash, and execution context.
"""

from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from typing import Any, Dict, Optional, Tuple
import hashlib
import json
import platform
import sys
import math

import py3plex


@dataclass
class CacheKey:
    """Key for cache lookups with reproducibility guarantees.
    
    Attributes:
        graph_fingerprint: Stable hash of network structure
        program_hash: Hash of program AST
        execution_context: Hash of execution parameters (seed, etc.)
        environment_signature: Library/Python/OS version info
    """
    graph_fingerprint: str
    program_hash: str
    execution_context: str
    environment_signature: str
    
    def to_string(self) -> str:
        """Convert to cache key string."""
        return f"{self.graph_fingerprint}:{self.program_hash}:{self.execution_context}:{self.environment_signature}"
    
    def __hash__(self) -> int:
        return hash(self.to_string())
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, CacheKey):
            return False
        return self.to_string() == other.to_string()


def graph_fingerprint(network: Any) -> str:
    """Hash graph data in traversal order, including identities and attributes.

    Raise TypeError or ValueError for inputs that cannot safely be cached.
    Order matters for queries with tied scores or positional limits.
    """
    import networkx as nx
    from py3plex.core.multinet import multi_layer_network

    graph_types = (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)
    if type(network) is multi_layer_network:
        graph = network.core_network
    elif type(network) in graph_types:
        graph = network
    else:
        raise TypeError("Unsupported network for cache fingerprint")
    if type(graph) not in graph_types:
        raise TypeError("Unsupported graph for cache fingerprint")

    edges = graph.edges(keys=True, data=True) if graph.is_multigraph() else graph.edges(data=True)
    digest = hashlib.sha256()

    def emit(value):
        try:
            digest.update(json.dumps(_cache_value(value), allow_nan=False).encode())
        except RecursionError as exc:
            raise ValueError("Nested value cannot be safely hashed") from exc

    def emit_list(records, emit_record):
        digest.update(b'["list", [')
        for index, record in enumerate(records):
            if index:
                digest.update(b", ")
            emit_record(record)
        digest.update(b"]]")

    def partitions():
        if hasattr(network, "list_partitions"):
            for name in network.list_partitions():
                partition = network.get_partition_by_name(name)
                if partition is not None:
                    yield name, partition

    def emit_partition(record):
        name, partition = record
        digest.update(b'["tuple", [')
        emit(name)
        digest.update(b", ")
        emit_list(partition.items(), emit)
        digest.update(b"]]")

    # Match _fingerprint_value's tagged tuple/list encoding byte for byte.
    digest.update(b'["tuple", [')
    for value in (
        type(graph).__name__,
        getattr(network, "directed", graph.is_directed()),
        getattr(network, "network_type", None),
        getattr(network, "network_version", None),
        getattr(network, "coupling_weight", None),
        getattr(network, "layers", None),
        getattr(network, "temporal_edges", None),
        graph.graph,
    ):
        emit(value)
        digest.update(b", ")
    emit_list(graph.nodes(data=True), emit)
    digest.update(b", ")
    emit_list(edges, emit)
    digest.update(b", ")
    emit_list(partitions(), emit_partition)
    digest.update(b"]]")
    return digest.hexdigest()


def _fingerprint_value(value: Any) -> str:
    """Hash supported values with their types preserved."""
    try:
        payload = json.dumps(_cache_value(value), allow_nan=False)
    except RecursionError as exc:
        raise ValueError("Nested value cannot be safely hashed") from exc
    return hashlib.sha256(payload.encode()).hexdigest()


def program_fingerprint(program_hash: str, optimization_level: int = 0) -> str:
    """Compute fingerprint for program including optimization level.
    
    Args:
        program_hash: Hash from GraphProgram.hash()
        optimization_level: Optimization level (0=none, 1=basic, 2=aggressive)
        
    Returns:
        Combined fingerprint
    """
    combined = f"{program_hash}:opt{optimization_level}"
    return hashlib.sha256(combined.encode()).hexdigest()


def execution_fingerprint(
    seed: Optional[int] = None,
    n_jobs: int = 1,
    uq_params: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    planner_config: Optional[Dict[str, Any]] = None,
    explain_plan: bool = False,
    optimize: Optional[bool] = None,
) -> str:
    """Compute fingerprint of execution context.
    
    Args:
        seed: Random seed
        n_jobs: Number of parallel jobs
        uq_params: UQ parameters (method, n_samples, etc.)
        params: Query parameter bindings
        planner_config: Planner configuration that affects output
        explain_plan: Whether the result includes an execution plan
        
    Returns:
        Hash of execution context
    """
    context = {
        "seed": seed,
        "n_jobs": n_jobs,
        "uq_params": _cache_value(uq_params or {}),
        "params": _cache_value(params or {}),
        "planner_config": _cache_value(planner_config or {}),
        "explain_plan": explain_plan,
        "optimize": optimize,
    }
    json_str = json.dumps(context, sort_keys=True, allow_nan=False)
    return hashlib.sha256(json_str.encode()).hexdigest()


def _cache_value(value: Any) -> Any:
    """Canonicalize supported cache inputs with their types preserved."""
    if value is None or isinstance(value, (bool, int, str)):
        return [type(value).__name__, value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite values cannot be used in cache keys")
        return ["float", value]
    if isinstance(value, (list, tuple)):
        return [type(value).__name__, [_cache_value(item) for item in value]]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("Cache key dictionaries require string keys")
        return ["dict", [[key, _cache_value(value[key])] for key in sorted(value)]]
    raise TypeError(f"Cannot cache execution parameter of type {type(value).__name__}")


def environment_signature() -> str:
    """Get environment signature for reproducibility.
    
    Returns:
        String with library/Python/OS versions
    """
    return (
        f"py3plex:{py3plex.__version__}:"
        f"python:{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}:"
        f"platform:{platform.system()}:{platform.machine()}"
    )


class ProgramCache:
    """In-memory cache for program execution results.
    
    Cache is keyed by (graph_fingerprint, program_hash, execution_context).
    Cache entries include full provenance for reproducibility verification.
    
    Example:
        >>> import networkx as nx
        >>> from py3plex.dsl import Q
        >>> from py3plex.core.multinet import multi_layer_network
        >>> net = multi_layer_network.from_networkx(nx.Graph([(("a", "L"), ("b", "L"))]))
        >>> program = Q.nodes().to_program()
        >>> result = program.execute(net, seed=42, cache_policy="disabled", progress=False)
        >>> cache = ProgramCache()
        >>> key = CacheKey(
        ...     graph_fingerprint=graph_fingerprint(net),
        ...     program_hash=program.hash(),
        ...     execution_context=execution_fingerprint(seed=42),
        ...     environment_signature=environment_signature()
        ... )
        >>> cache.put(key, result)
        >>> cache.get(key).items == result.items
        True
    """
    
    def __init__(self, max_entries: Optional[int] = 128):
        """Retain the most recently used entries; None opts into unlimited storage."""
        self._lock = RLock()
        self._cache = OrderedDict()
        self._evictions = self._hits = self._misses = 0
        self.max_entries = max_entries

    @property
    def max_entries(self) -> Optional[int]:
        """Capacity of this cache, including the one returned by get_global_cache()."""
        return self._max_entries

    @max_entries.setter
    def max_entries(self, limit: Optional[int]) -> None:
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("max_entries must be a nonnegative integer or None")
        with self._lock:
            self._max_entries = limit
            while limit is not None and len(self._cache) > limit:
                self._cache.popitem(last=False)
                self._evictions += 1

    def __getstate__(self):
        with self._lock:
            return {key: (value.copy() if key == "_cache" else value)
                    for key, value in vars(self).items() if key != "_lock"}

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = RLock()
        self._cache = OrderedDict(self._cache)
        self._evictions = state.get("_evictions", 0)
        self.max_entries = state.get("_max_entries", None)

    def get(self, key: CacheKey) -> Optional[Any]:
        """Get cached result.
        
        Args:
            key: Cache key
            
        Returns:
            Cached result or None if not found
        """
        key_str = key.to_string()
        with self._lock:
            if key_str in self._cache:
                self._hits += 1
                self._cache.move_to_end(key_str)
                return self._cache[key_str][1]
            self._misses += 1
            return None

    def put(self, key: CacheKey, result: Any) -> None:
        """Store result in cache.
        
        Args:
            key: Cache key
            result: Result to cache
        """
        key_str = key.to_string()
        with self._lock:
            self._cache[key_str] = (key, result)
            self._cache.move_to_end(key_str)
            if self._max_entries is not None and len(self._cache) > self._max_entries:
                self._cache.popitem(last=False)
                self._evictions += 1
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = self._misses = self._evictions = 0
    
    def size(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)
    
    def statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "evictions": self._evictions,
                "max_entries": self._max_entries,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }


# Global cache instance
_global_cache = ProgramCache()


def get_global_cache() -> ProgramCache:
    """Get global cache instance."""
    return _global_cache


def clear_global_cache() -> None:
    """Clear global cache."""
    _global_cache.clear()

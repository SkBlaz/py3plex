"""Program caching with reproducibility fingerprints.

This module implements deterministic caching keyed by graph fingerprint,
program hash, and execution context.
"""

from dataclasses import dataclass
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
    """Hash the complete graph state read by DSL queries.

    Raise TypeError for values that cannot be represented faithfully. Callers
    must then execute without caching, rather than reusing a false match.
    """
    graph = getattr(network, "core_network", None)
    if graph is None:
        raise TypeError("Graph cache requires a core_network")

    def encode(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, str)):
            return [type(value).__name__, value]
        if isinstance(value, float):
            if not math.isfinite(value):
                raise TypeError("Non-finite graph values cannot be fingerprinted")
            return ["float", value]
        if isinstance(value, (list, tuple)):
            return [type(value).__name__, [encode(item) for item in value]]
        if isinstance(value, dict):
            pairs = [[encode(key), encode(item)] for key, item in value.items()]
            pairs.sort(key=lambda pair: json.dumps(pair[0], sort_keys=True))
            return ["dict", pairs]
        raise TypeError(f"Cannot fingerprint graph value of type {type(value).__name__}")

    def packed(value: Any) -> str:
        return json.dumps(encode(value), sort_keys=True, separators=(",", ":"), allow_nan=False)

    nodes = sorted(packed((node, attrs)) for node, attrs in graph.nodes(data=True))
    if graph.is_multigraph():
        edges = sorted(packed((source, target, key, attrs))
                       for source, target, key, attrs in graph.edges(keys=True, data=True))
    else:
        edges = sorted(packed((source, target, attrs))
                       for source, target, attrs in graph.edges(data=True))

    state = {
        "directed": graph.is_directed(),
        "multigraph": graph.is_multigraph(),
        "network_type": getattr(network, "network_type", None),
        "graph_attributes": packed(graph.graph),
        "nodes": nodes,
        "edges": edges,
        "partitions": packed(getattr(network, "_partitions", {})),
    }
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"))
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
) -> str:
    """Compute fingerprint of execution context.
    
    Args:
        seed: Random seed
        n_jobs: Number of parallel jobs
        uq_params: UQ parameters (method, n_samples, etc.)
        params: Query parameter bindings
        planner_config: Planner configuration that affects result metadata
        explain_plan: Whether to attach the execution plan
        
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
    }
    json_str = json.dumps(context, sort_keys=True, allow_nan=False)
    return hashlib.sha256(json_str.encode()).hexdigest()


def _cache_value(value: Any) -> Any:
    """Encode supported values without conflating distinct Python types.

    Unknown objects must not be represented by ``repr``: it can change between
    runs or omit state that affects a query. Callers can skip caching instead.
    """
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
        >>> cache = ProgramCache()
        >>> key = CacheKey(
        ...     graph_fingerprint=graph_fingerprint(net),
        ...     program_hash=program.hash(),
        ...     execution_context=execution_fingerprint(seed=42),
        ...     environment_signature=environment_signature()
        ... )
        >>> cache.put(key, result)
        >>> cached = cache.get(key)
    """
    
    def __init__(self):
        self._cache: Dict[str, Tuple[CacheKey, Any]] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: CacheKey) -> Optional[Any]:
        """Get cached result.
        
        Args:
            key: Cache key
            
        Returns:
            Cached result or None if not found
        """
        key_str = key.to_string()
        if key_str in self._cache:
            self._hits += 1
            return self._cache[key_str][1]
        else:
            self._misses += 1
            return None
    
    def put(self, key: CacheKey, result: Any) -> None:
        """Store result in cache.
        
        Args:
            key: Cache key
            result: Result to cache
        """
        key_str = key.to_string()
        self._cache[key_str] = (key, result)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def size(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)
    
    def statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
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

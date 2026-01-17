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
from pathlib import Path

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
    """Compute stable fingerprint of network structure.
    
    Args:
        network: py3plex multi_layer_network object
        
    Returns:
        64-character hex hash of network structure
    """
    # Extract network properties in deterministic order
    layers_list = []
    try:
        if hasattr(network, "get_layers"):
            layers = network.get_layers()
            # Extract stable layer identifiers, handling MultiGraph objects
            for layer in layers:
                if hasattr(layer, "name"):
                    # NetworkX graph with a name attribute
                    layers_list.append(str(layer.name) if layer.name is not None else repr(type(layer)))
                elif hasattr(layer, "__class__"):
                    # Use the class name as identifier for graph objects
                    # This avoids memory addresses in the repr
                    layers_list.append(f"{layer.__class__.__name__}")
                else:
                    layers_list.append(str(layer))
    except Exception:
        pass
    
    data = {
        "directed": getattr(network, "directed", False),
        "layers": sorted(layers_list),
    }
    
    # Get nodes and edges in sorted order
    try:
        nodes = []
        edges = []
        
        if hasattr(network, "get_nodes"):
            # Convert all nodes to strings before sorting to handle mixed types
            nodes = sorted([str(n) for n in network.get_nodes()])
        
        if hasattr(network, "get_edges"):
            edge_list = network.get_edges()
            # Sort edges deterministically
            edges = sorted([(str(e[0]), str(e[1]), str(e[2]), str(e[3])) for e in edge_list])
        
        data["num_nodes"] = len(nodes)
        data["num_edges"] = len(edges)
        
        # Sample first 100 edges for large networks
        if len(edges) > 100:
            data["edge_sample"] = edges[:100]
        else:
            data["edges"] = edges
            
    except Exception:
        # Fallback: just use basic structure
        data["num_nodes"] = getattr(network, "N", 0)
        data["num_edges"] = getattr(network, "E", 0)
    
    # Serialize deterministically
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


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
    uq_params: Optional[Dict[str, Any]] = None
) -> str:
    """Compute fingerprint of execution context.
    
    Args:
        seed: Random seed
        n_jobs: Number of parallel jobs
        uq_params: UQ parameters (method, n_samples, etc.)
        
    Returns:
        Hash of execution context
    """
    context = {
        "seed": seed,
        "n_jobs": n_jobs,
        "uq_params": uq_params or {},
    }
    json_str = json.dumps(context, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


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

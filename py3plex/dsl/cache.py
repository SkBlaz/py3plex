"""Cache backend for DSL v2 query planner.

This module provides caching infrastructure for expensive computations
(primarily centrality measures) with deterministic cache keys.
"""

import hashlib
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class CacheStatistics:
    """Statistics for cache operations.
    
    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        stores: Number of cache stores
        evictions: Number of cache evictions
        size_bytes: Estimated cache size in bytes
    """
    hits: int = 0
    misses: int = 0
    stores: int = 0
    evictions: int = 0
    size_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "stores": self.stores,
            "evictions": self.evictions,
            "size_bytes": self.size_bytes,
            "hit_rate": self.hit_rate,
        }


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any) -> None:
        """Put value into cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached entries."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> CacheStatistics:
        """Get cache statistics.
        
        Returns:
            CacheStatistics object
        """
        pass


# Size estimation constants for cache entries
_SIZE_ESTIMATE_DICT_ENTRY = 100  # bytes per dict entry
_SIZE_ESTIMATE_LIST_ITEM = 50    # bytes per list item
_SIZE_ESTIMATE_DEFAULT = 1000    # bytes for unknown types


class InMemoryCacheBackend(CacheBackend):
    """In-memory cache backend with LRU eviction.
    
    This is the default cache backend. It uses an OrderedDict for LRU
    eviction and tracks cache statistics.
    
    Args:
        max_entries: Maximum number of entries (default: 100)
        max_bytes: Maximum cache size in bytes (default: 100MB)
    """
    
    def __init__(self, max_entries: int = 100, max_bytes: int = 100 * 1024 * 1024):
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self._cache: OrderedDict[str, Tuple[Any, int, float]] = OrderedDict()
        self._stats = CacheStatistics()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            # Move to end (most recently used)
            value, size, timestamp = self._cache.pop(key)
            self._cache[key] = (value, size, timestamp)
            self._stats.hits += 1
            return value
        else:
            self._stats.misses += 1
            return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value into cache."""
        # Estimate size
        size = self._estimate_size(value)
        
        # Remove old entry if exists
        if key in self._cache:
            old_value, old_size, old_timestamp = self._cache.pop(key)
            self._stats.size_bytes -= old_size
        
        # Add new entry
        timestamp = time.time()
        self._cache[key] = (value, size, timestamp)
        self._stats.size_bytes += size
        self._stats.stores += 1
        
        # Evict if needed
        self._evict_if_needed()
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._stats = CacheStatistics()
    
    def get_statistics(self) -> CacheStatistics:
        """Get cache statistics."""
        return self._stats
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes.
        
        This is a rough estimate based on type.
        """
        if isinstance(value, dict):
            return len(value) * _SIZE_ESTIMATE_DICT_ENTRY
        elif isinstance(value, (list, tuple)):
            return len(value) * _SIZE_ESTIMATE_LIST_ITEM
        elif isinstance(value, str):
            return len(value)
        elif isinstance(value, (int, float)):
            return 8
        else:
            return _SIZE_ESTIMATE_DEFAULT
    
    def _evict_if_needed(self) -> None:
        """Evict entries if limits are exceeded."""
        # Evict by count
        while len(self._cache) > self.max_entries:
            key, (value, size, timestamp) = self._cache.popitem(last=False)
            self._stats.size_bytes -= size
            self._stats.evictions += 1
        
        # Evict by size
        while self._stats.size_bytes > self.max_bytes and len(self._cache) > 0:
            key, (value, size, timestamp) = self._cache.popitem(last=False)
            self._stats.size_bytes -= size
            self._stats.evictions += 1


# Global cache instance
_global_cache: Optional[CacheBackend] = None


def get_global_cache() -> CacheBackend:
    """Get or create the global cache instance.
    
    Returns:
        Global CacheBackend instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = InMemoryCacheBackend()
    return _global_cache


def set_global_cache(cache: Optional[CacheBackend]) -> None:
    """Set the global cache instance.
    
    Args:
        cache: CacheBackend instance or None to disable
    """
    global _global_cache
    _global_cache = cache


def clear_cache() -> None:
    """Clear the global cache."""
    cache = get_global_cache()
    if cache:
        cache.clear()


def get_cache_statistics() -> Dict[str, Any]:
    """Get global cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    cache = get_global_cache()
    if cache:
        return cache.get_statistics().to_dict()
    return CacheStatistics().to_dict()


def create_cache_key(
    network_fingerprint: Dict[str, Any],
    ast_hash: str,
    measure_name: str,
    params: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    uq_method: Optional[str] = None,
    n_samples: Optional[int] = None
) -> str:
    """Create a deterministic cache key.
    
    Args:
        network_fingerprint: Network fingerprint dict
        ast_hash: AST hash
        measure_name: Measure name
        params: Query parameters
        seed: Random seed if applicable
        uq_method: Uncertainty quantification method if applicable
        n_samples: Number of samples for UQ if applicable
        
    Returns:
        Cache key (hex string)
    """
    parts = [
        str(network_fingerprint.get("node_count", 0)),
        str(network_fingerprint.get("edge_count", 0)),
        str(network_fingerprint.get("layer_count", 0)),
        ",".join(sorted(network_fingerprint.get("layers", []))),
        ast_hash,
        measure_name,
        str(params) if params else "",
        str(seed) if seed is not None else "",
        uq_method or "",
        str(n_samples) if n_samples else "",
    ]
    
    canonical = "|".join(parts)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]

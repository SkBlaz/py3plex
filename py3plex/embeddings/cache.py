"""In-memory LRU cache for embedding results.

Cache keys are tuples of (network_fingerprint_hash, ast_hash, embed_config_hash)
so that mutations to the network or changes to query/embedding params always
produce a cache miss.

The cache is module-level (global), so it persists across DSL calls within
a single Python process.  Use :func:`clear_cache` to reset it.
"""

from __future__ import annotations

import hashlib
import json
import logging
from threading import Lock
from typing import Any, Dict, Optional

from .base import EmbeddingResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache storage
# ---------------------------------------------------------------------------

_LOCK = Lock()
_MAX_ENTRIES: int = 128


class _LRUCache:
    """Thread-safe LRU cache backed by an OrderedDict."""

    def __init__(self, maxsize: int = 128) -> None:
        from collections import OrderedDict

        self._store: "OrderedDict[str, EmbeddingResult]" = OrderedDict()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[EmbeddingResult]:
        with _LOCK:
            if key in self._store:
                self._store.move_to_end(key)
                self._hits += 1
                return self._store[key]
            self._misses += 1
            return None

    def put(self, key: str, value: EmbeddingResult) -> None:
        with _LOCK:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = value
            if len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with _LOCK:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses


_DEFAULT_CACHE = _LRUCache(maxsize=_MAX_ENTRIES)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def make_embed_config_hash(config: Dict[str, Any]) -> str:
    """Return a short deterministic hash string for an embedding config dict.

    Args:
        config: Serialisable dict of embedding parameters.

    Returns:
        8-character hex digest.
    """
    serialised = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(serialised.encode()).hexdigest()[:16]


def make_cache_key(
    network_fingerprint: str,
    ast_hash: str,
    embed_config_hash: str,
    network_version: Optional[int] = None,
) -> str:
    """Compose a cache key from its components.

    Args:
        network_fingerprint: Hash or string describing network structure.
        ast_hash: Hash of the query AST.
        embed_config_hash: Hash of embedding parameters.
        network_version: Optional monotonic version counter from the network
            object; if provided it is incorporated so mutations always miss.

    Returns:
        Cache key string.
    """
    parts = [network_fingerprint, ast_hash, embed_config_hash]
    if network_version is not None:
        parts.append(str(network_version))
    return ":".join(parts)


def cache_get(key: str) -> Optional[EmbeddingResult]:
    """Retrieve an EmbeddingResult from the default cache.

    Returns ``None`` on a cache miss.
    """
    result = _DEFAULT_CACHE.get(key)
    if result is not None:
        logger.debug("Embedding cache HIT for key %.32s…", key)
    else:
        logger.debug("Embedding cache MISS for key %.32s…", key)
    return result


def cache_put(key: str, result: EmbeddingResult) -> None:
    """Store an EmbeddingResult in the default cache."""
    _DEFAULT_CACHE.put(key, result)


def clear_cache() -> None:
    """Clear all cached embeddings."""
    _DEFAULT_CACHE.clear()
    logger.debug("Embedding cache cleared.")


def cache_stats() -> Dict[str, int]:
    """Return cache hit/miss statistics."""
    return {"hits": _DEFAULT_CACHE.hits, "misses": _DEFAULT_CACHE.misses}

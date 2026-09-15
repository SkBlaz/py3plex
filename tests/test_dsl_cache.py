"""Focused tests for the DSL query cache backend and cache key contract."""

import pytest

import py3plex.dsl.cache as cache_module
from py3plex.dsl.cache import (
    CacheBackend,
    CacheStatistics,
    InMemoryCacheBackend,
    clear_cache,
    create_cache_key,
    get_cache_statistics,
    get_global_cache,
    set_global_cache,
)


def test_cache_statistics_report_zero_and_nonzero_hit_rates():
    stats = CacheStatistics()
    assert stats.hit_rate == 0.0

    stats.hits = 3
    stats.misses = 1
    assert stats.hit_rate == pytest.approx(0.75)
    assert stats.to_dict() == {
        "hits": 3,
        "misses": 1,
        "stores": 0,
        "evictions": 0,
        "size_bytes": 0,
        "hit_rate": 0.75,
    }


def test_in_memory_cache_tracks_hits_misses_and_value_sizes():
    cache = InMemoryCacheBackend(max_entries=10)

    assert cache.get("missing") is None
    cache.put("mapping", {"a": 1, "b": 2})
    cache.put("sequence", [1, 2, 3])
    cache.put("text", "abcd")
    cache.put("number", 1)
    cache.put("object", object())

    assert cache.get("mapping") == {"a": 1, "b": 2}
    stats = cache.get_statistics()
    assert stats.misses == 1
    assert stats.hits == 1
    assert stats.stores == 5
    assert stats.size_bytes == 2 * 100 + 3 * 50 + 4 + 8 + 1000


def test_put_replaces_existing_entry_without_leaking_size():
    cache = InMemoryCacheBackend()
    cache.put("key", "long value")
    cache.put("key", "x")

    assert cache.get("key") == "x"
    assert cache.get_statistics().stores == 2
    assert cache.get_statistics().size_bytes == 1


def test_count_limit_evicts_least_recently_used_entry():
    cache = InMemoryCacheBackend(max_entries=2)
    cache.put("first", "a")
    cache.put("second", "b")
    assert cache.get("first") == "a"  # Make first the most recently used.
    cache.put("third", "c")

    assert cache.get("second") is None
    assert cache.get("first") == "a"
    assert cache.get("third") == "c"
    assert cache.get_statistics().evictions == 1


def test_byte_limit_evicts_until_cache_fits():
    cache = InMemoryCacheBackend(max_entries=10, max_bytes=5)
    cache.put("first", "1234")
    cache.put("second", "5678")

    assert cache.get("first") is None
    assert cache.get("second") == "5678"
    assert cache.get_statistics().size_bytes == 4
    assert cache.get_statistics().evictions == 1


def test_clear_resets_entries_and_statistics():
    cache = InMemoryCacheBackend()
    cache.put("key", "value")
    cache.get("key")

    cache.clear()

    assert cache.get("key") is None
    assert cache.get_statistics() == CacheStatistics(misses=1)


def test_global_cache_can_be_replaced_and_cleared():
    replacement = InMemoryCacheBackend()
    set_global_cache(replacement)
    try:
        assert get_global_cache() is replacement
        replacement.put("key", "value")
        assert get_cache_statistics()["stores"] == 1

        clear_cache()
        assert get_cache_statistics() == CacheStatistics().to_dict()
    finally:
        set_global_cache(None)

    assert isinstance(get_global_cache(), InMemoryCacheBackend)


def test_cache_key_is_stable_and_sensitive_to_inputs():
    fingerprint = {
        "node_count": 3,
        "edge_count": 2,
        "layer_count": 2,
        "layers": ["work", "social"],
    }

    key = create_cache_key(
        fingerprint,
        ast_hash="abc123",
        measure_name="degree",
        params={"weighted": True},
        seed=42,
        uq_method="bootstrap",
        n_samples=10,
    )

    assert key == create_cache_key(
        {**fingerprint, "layers": ["social", "work"]},
        ast_hash="abc123",
        measure_name="degree",
        params={"weighted": True},
        seed=42,
        uq_method="bootstrap",
        n_samples=10,
    )
    assert len(key) == 16
    assert key != create_cache_key(fingerprint, "abc123", "pagerank")
    assert key != create_cache_key(fingerprint, "abc123", "degree", seed=43)


def test_global_cache_module_state_can_be_disabled_temporarily():
    original = cache_module._global_cache
    try:
        set_global_cache(None)
        assert get_cache_statistics() == CacheStatistics().to_dict()
    finally:
        cache_module._global_cache = original


def test_statistics_fall_back_for_a_falsey_backend():
    class FalseyBackend(CacheBackend):
        def __bool__(self):
            return False

        def get(self, key):
            return None

        def put(self, key, value):
            pass

        def clear(self):
            pass

        def get_statistics(self):
            return CacheStatistics(hits=99)

    original = cache_module._global_cache
    try:
        set_global_cache(FalseyBackend())
        assert get_cache_statistics() == CacheStatistics().to_dict()
        clear_cache()
    finally:
        cache_module._global_cache = original

def test_lru_cache_evicts_after_hit_and_releases_results():
    import weakref
    from py3plex.dsl.program.cache import CacheKey, ProgramCache

    class Result:
        pass

    cache = ProgramCache(max_entries=2)
    keys = [CacheKey(str(i), "program", "context", "env") for i in range(3)]
    result = Result()
    ref = weakref.ref(result)
    cache.put(keys[0], 0)
    cache.put(keys[1], result)
    del result
    assert cache.get(keys[0]) == 0
    cache.put(keys[2], 2)
    assert cache.get(keys[1]) is None and ref() is None
    assert cache.statistics()["evictions"] == 1
    cache.clear()
    assert cache.size() == cache.statistics()["evictions"] == 0


def test_resize_and_restore_cache():
    import pickle
    from py3plex.dsl.program.cache import CacheKey, ProgramCache

    cache = ProgramCache()
    keys = [CacheKey(str(i), "p", "c", "e") for i in range(3)]
    for i, key in enumerate(keys):
        cache.put(key, i)
    cache = pickle.loads(pickle.dumps(cache))
    cache.max_entries = 1
    assert cache.get(keys[-1]) == 2
    assert cache.statistics()["evictions"] == 2

    restored = ProgramCache.__new__(ProgramCache)
    restored.__setstate__({"_cache": {keys[0].to_string(): (keys[0], 123)}, "_hits": 0, "_misses": 0})
    assert restored.max_entries is None
    assert restored.get(keys[0]) == 123

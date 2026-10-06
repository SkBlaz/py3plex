"""Regression tests for cached results leaking between receivers or methods."""

import pytest

from py3plex.core.lazy_evaluation import CacheManager


@pytest.mark.parametrize("max_size", [1, 4])
def test_cached_method_keeps_results_specific_to_receiver(max_size):
    cache = CacheManager(max_size=max_size)

    class Network:
        def __init__(self, degree):
            self.degree = degree
            self.calls = 0

        @cache.cached_method("degree")
        def compute(self, scale=1):
            self.calls += 1
            return self.degree * scale

    first, second = Network(3), Network(8)
    assert first.compute(scale=2) == 6
    assert second.compute(scale=2) == 16
    assert second.compute(scale=2) == 16
    assert second.calls == 1
    assert first.compute(scale=2) == 6
    assert first.calls == (2 if max_size == 1 else 1)
    assert cache.cache_info("degree")["degree"] <= max_size


def test_equal_unhashable_receivers_keep_separate_cached_results():
    cache = CacheManager()

    class Network:
        __hash__ = None

        def __init__(self, degree):
            self.degree = degree

        def __eq__(self, other):
            return isinstance(other, Network)

        @cache.cached_method("degree")
        def compute(self):
            return self.degree

    first, second = Network(3), Network(8)
    assert first == second
    assert first.compute() == 3
    assert second.compute() == 8
    assert first.compute() == 3


def test_distinct_methods_with_same_name_do_not_share_results():
    cache = CacheManager()

    def make_method(offset):
        @cache.cached_method("degree")
        def compute(self, value):
            return offset + value

        return compute

    class Network:
        first = make_method(3)
        second = make_method(8)

    network = Network()
    assert network.first(2) == 5
    assert network.second(2) == 10
    assert network.first(2) == 5


def test_clearing_cache_recomputes_for_each_receiver():
    cache = CacheManager()

    class Network:
        def __init__(self, degree):
            self.degree = degree

        @cache.cached_method("degree")
        def compute(self):
            return self.degree

    first, second = Network(3), Network(8)
    assert first.compute() == 3
    assert second.compute() == 8
    first.degree, second.degree = 5, 10
    cache.clear_cache("degree")
    assert first.compute() == 5
    assert second.compute() == 10


@pytest.mark.parametrize("release", ["clear", "evict"])
def test_cached_receiver_lifetime_ends_with_its_cache_entry(release):
    import gc
    import weakref

    cache = CacheManager(max_size=1)

    class Network:
        @cache.cached_method("degree")
        def compute(self):
            return 3

    network = Network()
    reference = weakref.ref(network)
    assert network.compute() == 3
    del network
    gc.collect()
    # The live entry must retain the receiver to prevent reuse of its ID.
    assert reference() is not None
    if release == "clear":
        cache.clear_cache("degree")
    else:
        assert Network().compute() == 3
    gc.collect()
    assert reference() is None

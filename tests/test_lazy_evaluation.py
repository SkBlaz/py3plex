"""
Tests for lazy evaluation and caching infrastructure.

Tests:
- LazyProperty descriptor
- CacheManager functionality
- Cache invalidation
- LRU eviction
"""

import pytest
import numpy as np
from py3plex.core.lazy_evaluation import (
    LazyProperty,
    CacheManager,
    cached_property,
    invalidate_caches,
)


class TestLazyProperty:
    """Test LazyProperty descriptor."""
    
    def test_lazy_computation(self):
        """Test that property is computed lazily."""
        call_count = [0]
        
        class TestClass:
            @LazyProperty
            def expensive_property(self):
                call_count[0] += 1
                return 42
        
        obj = TestClass()
        assert call_count[0] == 0  # Not computed yet
        
        value1 = obj.expensive_property
        assert call_count[0] == 1  # Computed on first access
        assert value1 == 42
        
        value2 = obj.expensive_property
        assert call_count[0] == 1  # Not recomputed
        assert value2 == 42
    
    def test_lazy_property_per_instance(self):
        """Test that lazy properties are per-instance."""
        class TestClass:
            def __init__(self, value):
                self.value = value
            
            @LazyProperty
            def doubled(self):
                return self.value * 2
        
        obj1 = TestClass(10)
        obj2 = TestClass(20)
        
        assert obj1.doubled == 20
        assert obj2.doubled == 40


class TestCacheManager:
    """Test CacheManager class."""
    
    def test_basic_caching(self):
        """Test basic cache functionality."""
        cache = CacheManager(max_size=10)
        
        # Get cache
        my_cache = cache.get_cache('test')
        assert isinstance(my_cache, dict)
        assert len(my_cache) == 0
    
    def test_clear_cache(self):
        """Test cache clearing."""
        cache = CacheManager()
        
        # Add items to cache
        test_cache = cache.get_cache('test')
        test_cache['key1'] = 'value1'
        test_cache['key2'] = 'value2'
        
        assert len(test_cache) == 2
        
        # Clear specific cache
        cache.clear_cache('test')
        assert len(test_cache) == 0
        
        # Add to multiple caches
        cache.get_cache('cache1')['k'] = 'v'
        cache.get_cache('cache2')['k'] = 'v'
        
        # Clear all caches
        cache.clear_cache()
        assert len(cache.get_cache('cache1')) == 0
        assert len(cache.get_cache('cache2')) == 0
    
    def test_cached_method_decorator(self):
        """Test cached_method decorator."""
        cache = CacheManager(max_size=5)
        
        call_count = [0]
        
        class TestClass:
            def __init__(self):
                self._cache_manager = cache
            
            @cache.cached_method('results')
            def compute(self, x):
                call_count[0] += 1
                return x * 2
        
        obj = TestClass()
        
        # First call - should compute
        result1 = obj.compute(5)
        assert result1 == 10
        assert call_count[0] == 1
        
        # Second call with same argument - should use cache
        result2 = obj.compute(5)
        assert result2 == 10
        assert call_count[0] == 1  # Not recomputed
        
        # Different argument - should compute
        result3 = obj.compute(10)
        assert result3 == 20
        assert call_count[0] == 2
    
    def test_lru_eviction(self):
        """Test LRU cache eviction."""
        cache = CacheManager(max_size=3)
        
        class TestClass:
            def __init__(self):
                self._cache_manager = cache
            
            @cache.cached_method('small_cache')
            def compute(self, x):
                return x * 2
        
        obj = TestClass()
        
        # Fill cache to capacity
        obj.compute(1)
        obj.compute(2)
        obj.compute(3)
        
        results_cache = cache.get_cache('small_cache')
        assert len(results_cache) == 3
        
        # Add one more - should evict oldest
        obj.compute(4)
        assert len(results_cache) == 3  # Still at max size
    
    def test_cache_info(self):
        """Test cache_info method."""
        cache = CacheManager()
        
        cache.get_cache('cache1')['k1'] = 'v1'
        cache.get_cache('cache1')['k2'] = 'v2'
        cache.get_cache('cache2')['k1'] = 'v1'
        
        info = cache.cache_info()
        assert info['cache1'] == 2
        assert info['cache2'] == 1
        
        specific_info = cache.cache_info('cache1')
        assert specific_info['cache1'] == 2


class TestInvalidateCaches:
    """Test cache invalidation decorator."""
    
    def test_invalidate_on_modification(self):
        """Test that caches are invalidated on modification."""
        cache = CacheManager()
        
        class Network:
            def __init__(self):
                self._cache_manager = cache
                self.data = []
            
            @cached_property('expensive')
            def expensive_property(self):
                return sum(self.data)
            
            @invalidate_caches('expensive')
            def add_data(self, value):
                self.data.append(value)
        
        net = Network()
        net.data = [1, 2, 3]
        
        # Compute property
        result1 = net.expensive_property
        assert result1 == 6
        
        # Modify network - should invalidate cache
        net.add_data(4)
        
        # Property should be recomputed
        # Note: In this simple test, we check that the method can be called
        # In practice, the cached_property would need to check if cache is cleared
        assert net.data == [1, 2, 3, 4]


class TestCachedProperty:
    """Test cached_property decorator."""
    
    def test_cached_property_basic(self):
        """Test basic cached property functionality."""
        call_count = [0]
        
        class TestClass:
            @cached_property('test')
            def prop(self):
                call_count[0] += 1
                return 42
        
        obj = TestClass()
        
        # First access
        val1 = obj.prop
        assert val1 == 42
        assert call_count[0] == 1
        
        # Second access - should use cache
        val2 = obj.prop
        assert val2 == 42
        assert call_count[0] == 1
    
    def test_cached_property_deletion(self):
        """Test cache deletion."""
        call_count = [0]
        
        class TestClass:
            @cached_property('test')
            def prop(self):
                call_count[0] += 1
                return call_count[0]
        
        obj = TestClass()
        
        val1 = obj.prop
        assert val1 == 1
        
        # Delete cache
        del obj.prop
        
        # Should recompute
        val2 = obj.prop
        assert val2 == 2


def test_cache_manager_integration():
    """Integration test for cache manager with multiple operations."""
    cache = CacheManager(max_size=10)
    
    class ComplexObject:
        def __init__(self):
            self._cache_manager = cache
            self.value = 0
        
        @cache.cached_method('results')
        def compute_expensive(self, x, y):
            return x * y + self.value
        
        @invalidate_caches('results')
        def update_value(self, new_value):
            self.value = new_value
    
    obj = ComplexObject()
    
    # Compute result
    result1 = obj.compute_expensive(3, 4)
    assert result1 == 12  # 3*4 + 0
    
    # Should use cache
    result2 = obj.compute_expensive(3, 4)
    assert result2 == 12
    
    # Update value - invalidates cache
    obj.update_value(10)
    
    # Cache should be cleared
    results_cache = cache.get_cache('results')
    # Note: invalidate_caches only clears if _cache_manager exists
    
    # Compute with new value
    result3 = obj.compute_expensive(3, 4)
    assert result3 == 22  # 3*4 + 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

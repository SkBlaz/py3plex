"""
Tests for py3plex.core.lazy_evaluation module.

This module tests lazy evaluation and caching functionality.
"""

import pytest
from py3plex.core.lazy_evaluation import (
    LazyProperty,
    CacheManager,
)


class TestLazyProperty:
    """Test the LazyProperty descriptor."""

    def test_lazy_property_computed_once(self):
        """Test that lazy property is computed only once."""
        call_count = [0]
        
        class TestClass:
            @LazyProperty
            def expensive_property(self):
                call_count[0] += 1
                return "computed_value"
        
        obj = TestClass()
        
        # First access should compute
        result1 = obj.expensive_property
        assert result1 == "computed_value"
        assert call_count[0] == 1
        
        # Second access should return cached value
        result2 = obj.expensive_property
        assert result2 == "computed_value"
        assert call_count[0] == 1  # Not incremented

    def test_lazy_property_different_instances(self):
        """Test that lazy properties are instance-specific."""
        call_count = [0]
        
        class TestClass:
            def __init__(self, value):
                self.value = value
            
            @LazyProperty
            def computed_value(self):
                call_count[0] += 1
                return f"computed_{self.value}"
        
        obj1 = TestClass("A")
        obj2 = TestClass("B")
        
        # Each instance computes independently
        assert obj1.computed_value == "computed_A"
        assert obj2.computed_value == "computed_B"
        assert call_count[0] == 2

    def test_lazy_property_manual_set(self):
        """Test that lazy property can be manually set."""
        class TestClass:
            @LazyProperty
            def property_name(self):
                return "original_value"
        
        obj = TestClass()
        
        # Manually set the value
        obj.property_name = "overridden_value"
        
        # Should return the overridden value
        assert obj.property_name == "overridden_value"

    def test_lazy_property_descriptor_access(self):
        """Test accessing LazyProperty descriptor on class."""
        class TestClass:
            @LazyProperty
            def some_property(self):
                return "value"
        
        # Accessing on class returns the descriptor
        descriptor = TestClass.some_property
        assert isinstance(descriptor, LazyProperty)

    def test_lazy_property_with_none_return(self):
        """Test lazy property that returns None."""
        class TestClass:
            @LazyProperty
            def none_property(self):
                return None
        
        obj = TestClass()
        # None is a valid cached value
        assert obj.none_property is None
        # Should still be cached
        assert hasattr(obj, "_lazy_none_property")

    def test_lazy_property_with_exception(self):
        """Test lazy property that raises an exception."""
        class TestClass:
            @LazyProperty
            def error_property(self):
                raise ValueError("Test error")
        
        obj = TestClass()
        
        # Should raise on access
        with pytest.raises(ValueError, match="Test error"):
            _ = obj.error_property
        
        # Should not cache the exception, raise again
        with pytest.raises(ValueError, match="Test error"):
            _ = obj.error_property


class TestCacheManager:
    """Test the CacheManager class."""

    def test_cache_manager_initialization(self):
        """Test CacheManager can be initialized."""
        cache = CacheManager(max_size=100)
        assert cache.max_size == 100
        assert len(cache._caches) == 0

    def test_get_cache_creates_new_cache(self):
        """Test get_cache creates a new cache if it doesn't exist."""
        cache_manager = CacheManager()
        
        # Get a new cache
        cache = cache_manager.get_cache("test_cache")
        
        # Should be an empty dictionary
        assert isinstance(cache, dict)
        assert len(cache) == 0
        
        # Should be stored in the manager
        assert "test_cache" in cache_manager._caches

    def test_get_cache_returns_existing_cache(self):
        """Test get_cache returns the same cache on multiple calls."""
        cache_manager = CacheManager()
        
        # Get cache and add data
        cache1 = cache_manager.get_cache("test_cache")
        cache1["key"] = "value"
        
        # Get the same cache again
        cache2 = cache_manager.get_cache("test_cache")
        
        # Should be the same cache
        assert cache2 is cache1
        assert cache2["key"] == "value"

    def test_multiple_named_caches(self):
        """Test manager can handle multiple named caches."""
        cache_manager = CacheManager()
        
        cache_a = cache_manager.get_cache("cache_a")
        cache_b = cache_manager.get_cache("cache_b")
        
        cache_a["data"] = "A"
        cache_b["data"] = "B"
        
        # Caches should be independent
        assert cache_a["data"] == "A"
        assert cache_b["data"] == "B"
        assert cache_a is not cache_b

    def test_cache_manager_default_size(self):
        """Test CacheManager has a default max_size."""
        cache = CacheManager()
        assert cache.max_size == 128  # Default from implementation

    def test_cache_manager_weak_references(self):
        """Test CacheManager uses weak references for networks."""
        cache_manager = CacheManager()
        
        # Should have WeakKeyDictionary for network refs
        assert hasattr(cache_manager, '_network_refs')
        # WeakKeyDictionary doesn't break even if empty
        assert len(cache_manager._network_refs) == 0


class TestLazyPropertyEdgeCases:
    """Test edge cases for LazyProperty."""

    def test_lazy_property_with_args_fails(self):
        """Test that LazyProperty doesn't work with methods requiring arguments."""
        class TestClass:
            @LazyProperty
            def method_with_args(self, arg):
                return arg
        
        obj = TestClass()
        
        # This will fail because LazyProperty calls the method without args
        with pytest.raises(TypeError):
            _ = obj.method_with_args

    def test_lazy_property_name_attribute(self):
        """Test that LazyProperty stores the function name."""
        class TestClass:
            @LazyProperty
            def my_property(self):
                return "value"
        
        descriptor = TestClass.my_property
        assert descriptor.name == "my_property"
        assert descriptor.func.__name__ == "my_property"

    def test_lazy_property_cache_attribute_naming(self):
        """Test the internal cache attribute naming."""
        class TestClass:
            @LazyProperty
            def test_prop(self):
                return "cached"
        
        obj = TestClass()
        _ = obj.test_prop
        
        # Should create _lazy_test_prop attribute
        assert hasattr(obj, "_lazy_test_prop")
        assert getattr(obj, "_lazy_test_prop") == "cached"

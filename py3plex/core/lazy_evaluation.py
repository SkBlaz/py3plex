"""
Lazy evaluation and caching infrastructure for py3plex.

This module provides decorators and utilities for lazy computation and caching
of expensive operations in multilayer network analysis.

Features:
- Lazy property evaluation (compute only when accessed)
- LRU caching for repeated computations
- Cache invalidation on network modifications
- Memory-efficient storage for large matrices

Authors: py3plex contributors
Date: 2025
"""

import functools
import hashlib
import pickle
import weakref
from typing import Any, Callable, Dict, Optional, Tuple


class LazyProperty:
    """Descriptor for lazy property evaluation.
    
    A lazy property is computed once on first access and cached thereafter.
    The cached value is invalidated if the associated cache is cleared.
    
    Example:
        >>> class Network:
        ...     @LazyProperty
        ...     def expensive_matrix(self):
        ...         return compute_expensive_matrix()
    """
    
    def __init__(self, func: Callable) -> None:
        self.func = func
        self.name = func.__name__
        
    def __get__(self, obj: Any, objtype: Optional[type] = None) -> Any:
        if obj is None:
            return self
        
        # Check if value is already cached
        cache_attr = f"_lazy_{self.name}"
        if hasattr(obj, cache_attr):
            return getattr(obj, cache_attr)
        
        # Compute and cache the value
        value = self.func(obj)
        setattr(obj, cache_attr, value)
        return value
    
    def __set__(self, obj: Any, value: Any) -> None:
        # Allow manual setting of the cached value
        cache_attr = f"_lazy_{self.name}"
        setattr(obj, cache_attr, value)


class CacheManager:
    """Manages caching for expensive network computations.
    
    Provides LRU caching with automatic invalidation and memory management.
    Supports caching of:
    - Supra-adjacency matrices
    - Layout computations
    - Community detection results
    - Centrality calculations
    
    Example:
        >>> cache = CacheManager(max_size=100)
        >>> @cache.cached_method
        ... def expensive_operation(network, param):
        ...     return compute_result(network, param)
    """
    
    def __init__(self, max_size: int = 128) -> None:
        """Initialize cache manager.
        
        Args:
            max_size: Maximum number of cached items (LRU eviction)
        """
        self.max_size = max_size
        self._caches: Dict[str, Dict] = {}
        self._network_refs: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
        
    def get_cache(self, cache_name: str) -> Dict:
        """Get or create a named cache.
        
        Args:
            cache_name: Name of the cache (e.g., 'supra_matrix', 'layouts')
            
        Returns:
            Dictionary cache for the named category
        """
        if cache_name not in self._caches:
            self._caches[cache_name] = {}
        return self._caches[cache_name]
    
    def clear_cache(self, cache_name: Optional[str] = None) -> None:
        """Clear cache(s).
        
        Args:
            cache_name: Specific cache to clear, or None to clear all caches
        """
        if cache_name is None:
            self._caches.clear()
        elif cache_name in self._caches:
            self._caches[cache_name].clear()
    
    def cached_method(self, cache_name: str = "default") -> Callable:
        """Decorator for caching method results.
        
        Args:
            cache_name: Name of the cache to use
            
        Returns:
            Decorated function with caching
            
        Example:
            >>> @cache.cached_method('centrality')
            ... def compute_centrality(self, method='degree'):
            ...     return expensive_computation()
        """
        cache_manager = self  # Capture the cache manager instance
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(obj_self, *args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key = cache_manager._generate_cache_key(func.__name__, args, kwargs)
                cache = cache_manager.get_cache(cache_name)
                
                # Check if result is cached
                if cache_key in cache:
                    return cache[cache_key]
                
                # Compute and cache result
                result = func(obj_self, *args, **kwargs)
                
                # Implement LRU eviction if cache is full
                if len(cache) >= cache_manager.max_size:
                    # Remove oldest item (first key in dict)
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]
                
                cache[cache_key] = result
                return result
            
            return wrapper
        return decorator
    
    def _generate_cache_key(self, func_name: str, args: Tuple, kwargs: Dict) -> str:
        """Generate a unique cache key from function name and arguments.
        
        Args:
            func_name: Name of the function
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Hash string as cache key
        
        Note:
            Uses SHA-256 for better collision resistance than MD5.
        """
        # Create a deterministic representation of arguments
        key_data = (func_name, args, tuple(sorted(kwargs.items())))
        key_str = str(key_data)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def cache_info(self, cache_name: Optional[str] = None) -> Dict[str, int]:
        """Get information about cache usage.
        
        Args:
            cache_name: Specific cache to inspect, or None for all caches
            
        Returns:
            Dictionary with cache sizes
        """
        if cache_name is not None:
            if cache_name in self._caches:
                return {cache_name: len(self._caches[cache_name])}
            return {cache_name: 0}
        
        return {name: len(cache) for name, cache in self._caches.items()}


def cached_property(cache_name: str = "default"):
    """Decorator for caching property-like methods.
    
    Similar to @property but with caching that persists until explicitly cleared.
    
    Args:
        cache_name: Name of the cache category
        
    Returns:
        Decorator function
        
    Example:
        >>> class Network:
        ...     @cached_property('layouts')
        ...     def spring_layout(self):
        ...         return compute_spring_layout(self)
    """
    def decorator(func: Callable) -> property:
        cache_attr = f"_cache_{func.__name__}"
        
        @functools.wraps(func)
        def getter(self):
            if not hasattr(self, cache_attr):
                value = func(self)
                setattr(self, cache_attr, value)
            return getattr(self, cache_attr)
        
        def deleter(self):
            if hasattr(self, cache_attr):
                delattr(self, cache_attr)
        
        return property(getter, None, deleter)
    
    return decorator


def invalidate_caches(*cache_names: str):
    """Decorator to invalidate caches when a method modifies the network.
    
    Use this decorator on methods that modify the network structure
    (e.g., add_node, add_edge, remove_node) to ensure cached values
    are invalidated.
    
    Args:
        *cache_names: Names of caches to invalidate
        
    Returns:
        Decorator function
        
    Example:
        >>> class Network:
        ...     @invalidate_caches('supra_matrix', 'layouts')
        ...     def add_edge(self, u, v):
        ...         self.graph.add_edge(u, v)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Execute the original function
            result = func(self, *args, **kwargs)
            
            # Invalidate specified caches
            if hasattr(self, '_cache_manager'):
                for cache_name in cache_names:
                    self._cache_manager.clear_cache(cache_name)
            
            # Also clear lazy property caches
            for cache_name in cache_names:
                cache_attr = f"_lazy_{cache_name}"
                if hasattr(self, cache_attr):
                    delattr(self, cache_attr)
            
            return result
        
        return wrapper
    return decorator

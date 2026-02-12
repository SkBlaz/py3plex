"""
Tests for py3plex.algebra.registry module.

Tests registration and lookup of algebra operation implementations.
"""

import pytest
from py3plex.algebra.registry import (
    AlgebraRegistry,
    get_registry,
    register_operation,
    get_operation,
    list_operations,
    clear_registry
)
from py3plex.algebra.backend import AlgebraBackend


class TestAlgebraRegistry:
    """Test the AlgebraRegistry class."""

    def test_registry_creation(self):
        """Test creating a new registry."""
        registry = AlgebraRegistry()
        assert registry is not None

    def test_register_operation(self):
        """Test registering an operation."""
        registry = AlgebraRegistry()
        
        def dummy_op(graph, *args):
            return "result"
        
        registry.register("test_op", AlgebraBackend.NETWORKX, dummy_op)
        
        retrieved = registry.get("test_op", AlgebraBackend.NETWORKX)
        assert retrieved == dummy_op

    def test_get_nonexistent_operation(self):
        """Test getting an operation that doesn't exist."""
        registry = AlgebraRegistry()
        
        with pytest.raises(KeyError):
            registry.get("nonexistent_op", AlgebraBackend.NETWORKX)

    def test_register_multiple_backends(self):
        """Test registering same operation for different backends."""
        registry = AlgebraRegistry()
        
        def nx_impl(graph, *args):
            return "networkx"
        
        def sparse_impl(graph, *args):
            return "sparse"
        
        registry.register("operation", AlgebraBackend.NETWORKX, nx_impl)
        registry.register("operation", AlgebraBackend.SPARSE, sparse_impl)
        
        assert registry.get("operation", AlgebraBackend.NETWORKX) == nx_impl
        assert registry.get("operation", AlgebraBackend.SPARSE) == sparse_impl

    def test_list_operations_empty(self):
        """Test listing operations when registry is empty."""
        registry = AlgebraRegistry()
        ops = registry.list_operations()
        assert ops == []

    def test_list_operations_with_entries(self):
        """Test listing operations after registration."""
        registry = AlgebraRegistry()
        
        def op1(g):
            pass
        def op2(g):
            pass
        
        registry.register("op1", AlgebraBackend.NETWORKX, op1)
        registry.register("op2", AlgebraBackend.NETWORKX, op2)
        
        ops = registry.list_operations()
        assert len(ops) >= 2
        assert "op1" in ops
        assert "op2" in ops

    def test_clear_registry(self):
        """Test clearing all registered operations."""
        registry = AlgebraRegistry()
        
        def dummy_op(g):
            pass
        
        registry.register("test_op", AlgebraBackend.NETWORKX, dummy_op)
        assert len(registry.list_operations()) > 0
        
        registry.clear()
        assert len(registry.list_operations()) == 0

    def test_overwrite_existing_operation(self):
        """Test that registering same op+backend overwrites."""
        registry = AlgebraRegistry()
        
        def impl1(g):
            return "first"
        def impl2(g):
            return "second"
        
        registry.register("op", AlgebraBackend.NETWORKX, impl1)
        retrieved1 = registry.get("op", AlgebraBackend.NETWORKX)
        assert retrieved1 == impl1
        
        # Overwrite
        registry.register("op", AlgebraBackend.NETWORKX, impl2)
        retrieved2 = registry.get("op", AlgebraBackend.NETWORKX)
        assert retrieved2 == impl2
        assert retrieved2 != impl1


class TestGlobalRegistryFunctions:
    """Test the global registry access functions."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def teardown_method(self):
        """Clear registry after each test."""
        clear_registry()

    def test_get_global_registry(self):
        """Test getting the global registry."""
        registry = get_registry()
        assert registry is not None

    def test_register_operation_globally(self):
        """Test registering operation via global function."""
        def test_func(graph):
            return "test"
        
        register_operation("global_op", AlgebraBackend.NETWORKX, test_func)
        
        retrieved = get_operation("global_op", AlgebraBackend.NETWORKX)
        assert retrieved == test_func

    def test_get_operation_not_found(self):
        """Test getting nonexistent operation globally."""
        with pytest.raises(KeyError):
            get_operation("nonexistent", AlgebraBackend.NETWORKX)

    def test_list_operations_global(self):
        """Test listing operations globally."""
        def op1(g):
            pass
        def op2(g):
            pass
        
        register_operation("op1", AlgebraBackend.NETWORKX, op1)
        register_operation("op2", AlgebraBackend.SPARSE, op2)
        
        ops = list_operations()
        assert "op1" in ops
        assert "op2" in ops

    def test_clear_global_registry(self):
        """Test clearing the global registry."""
        def dummy(g):
            pass
        
        register_operation("test", AlgebraBackend.NETWORKX, dummy)
        assert len(list_operations()) > 0
        
        clear_registry()
        assert len(list_operations()) == 0

    def test_multiple_backend_registration(self):
        """Test registering multiple backends for same operation."""
        def nx_func(g):
            return "nx"
        def sparse_func(g):
            return "sparse"
        def igraph_func(g):
            return "igraph"
        
        register_operation("multi", AlgebraBackend.NETWORKX, nx_func)
        register_operation("multi", AlgebraBackend.SPARSE, sparse_func)
        register_operation("multi", AlgebraBackend.IGRAPH, igraph_func)
        
        assert get_operation("multi", AlgebraBackend.NETWORKX) == nx_func
        assert get_operation("multi", AlgebraBackend.SPARSE) == sparse_func
        assert get_operation("multi", AlgebraBackend.IGRAPH) == igraph_func

    def test_registry_singleton_behavior(self):
        """Test that get_registry returns same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_operation_with_different_signatures(self):
        """Test registering operations with different signatures."""
        def op_no_args(graph):
            return 1
        
        def op_with_args(graph, param1, param2):
            return param1 + param2
        
        register_operation("no_args", AlgebraBackend.NETWORKX, op_no_args)
        register_operation("with_args", AlgebraBackend.NETWORKX, op_with_args)
        
        # Both should be registered
        assert get_operation("no_args", AlgebraBackend.NETWORKX) == op_no_args
        assert get_operation("with_args", AlgebraBackend.NETWORKX) == op_with_args

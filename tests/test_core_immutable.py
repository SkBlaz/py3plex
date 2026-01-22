"""
Tests for py3plex.core.immutable module.

This module tests immutable network views and copy-on-write semantics.
"""

import pytest
from py3plex.core.immutable import (
    ImmutableNetworkError,
    ImmutableNetworkView,
)


class MockNetwork:
    """Mock network for testing."""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def add_node(self, node):
        self.nodes.append(node)
    
    def add_edge(self, source, target):
        self.edges.append((source, target))
    
    def get_nodes(self):
        return self.nodes.copy()
    
    def get_edges(self):
        return self.edges.copy()
    
    def number_of_nodes(self):
        return len(self.nodes)
    
    def number_of_edges(self):
        return len(self.edges)
    
    def __repr__(self):
        return f"MockNetwork(nodes={len(self.nodes)}, edges={len(self.edges)})"


class TestImmutableNetworkError:
    """Test the ImmutableNetworkError exception."""

    def test_immutable_network_error_creation(self):
        """Test that ImmutableNetworkError can be raised."""
        with pytest.raises(ImmutableNetworkError):
            raise ImmutableNetworkError("Cannot modify immutable network")

    def test_immutable_network_error_inheritance(self):
        """Test that ImmutableNetworkError extends Exception."""
        assert issubclass(ImmutableNetworkError, Exception)


class TestImmutableNetworkView:
    """Test the ImmutableNetworkView class."""

    def test_immutable_view_creation_with_deep_copy(self):
        """Test creating immutable view with deep copy."""
        network = MockNetwork()
        network.add_node("A")
        network.add_edge("A", "B")
        
        immutable = ImmutableNetworkView(network, deep_copy=True)
        
        # View should be created
        assert immutable is not None
        assert immutable._is_frozen is True
        
        # Original network changes should not affect immutable view
        network.add_node("C")
        assert len(immutable.get_nodes()) == 1  # Still has only A

    def test_immutable_view_creation_without_deep_copy(self):
        """Test creating immutable view without deep copy (reference)."""
        network = MockNetwork()
        network.add_node("A")
        
        immutable = ImmutableNetworkView(network, deep_copy=False)
        
        # View uses reference to original
        assert immutable._network is network

    def test_immutable_view_read_only_methods(self):
        """Test that read-only methods work."""
        network = MockNetwork()
        network.add_node("A")
        network.add_node("B")
        network.add_edge("A", "B")
        
        immutable = ImmutableNetworkView(network)
        
        # Read-only operations should work
        assert len(immutable.get_nodes()) == 2
        assert len(immutable.get_edges()) == 1
        assert immutable.number_of_nodes() == 2
        assert immutable.number_of_edges() == 1

    def test_immutable_view_repr(self):
        """Test string representation of immutable view."""
        network = MockNetwork()
        immutable = ImmutableNetworkView(network, copy_on_write=False)
        
        repr_str = repr(immutable)
        assert "ImmutableNetworkView" in repr_str
        assert "frozen" in repr_str
        
        immutable_cow = ImmutableNetworkView(network, copy_on_write=True)
        repr_str_cow = repr(immutable_cow)
        assert "copy-on-write" in repr_str_cow

    def test_copy_on_write_mode(self):
        """Test copy_on_write flag is stored correctly."""
        network = MockNetwork()
        
        immutable_frozen = ImmutableNetworkView(network, copy_on_write=False)
        assert immutable_frozen._copy_on_write is False
        
        immutable_cow = ImmutableNetworkView(network, copy_on_write=True)
        assert immutable_cow._copy_on_write is True

    def test_immutable_view_has_frozen_flag(self):
        """Test that immutable view has frozen flag set."""
        network = MockNetwork()
        immutable = ImmutableNetworkView(network)
        
        assert hasattr(immutable, '_is_frozen')
        assert immutable._is_frozen is True

    def test_number_of_nodes_with_core_network(self):
        """Test number_of_nodes when network has core_network attribute."""
        class NetworkWithCore:
            def __init__(self):
                self.core_network = MockNetwork()
                self.core_network.add_node("A")
        
        network = NetworkWithCore()
        immutable = ImmutableNetworkView(network)
        
        # Should delegate to core_network
        assert immutable.number_of_nodes() == 1

    def test_number_of_edges_with_core_network(self):
        """Test number_of_edges when network has core_network attribute."""
        class NetworkWithCore:
            def __init__(self):
                self.core_network = MockNetwork()
                self.core_network.add_edge("A", "B")
        
        network = NetworkWithCore()
        immutable = ImmutableNetworkView(network)
        
        # Should delegate to core_network
        assert immutable.number_of_edges() == 1

    def test_number_of_nodes_fallback(self):
        """Test number_of_nodes returns 0 for network without method."""
        class MinimalNetwork:
            pass
        
        network = MinimalNetwork()
        immutable = ImmutableNetworkView(network)
        
        # Should return 0 as fallback
        assert immutable.number_of_nodes() == 0

    def test_number_of_edges_fallback(self):
        """Test number_of_edges returns 0 for network without method."""
        class MinimalNetwork:
            pass
        
        network = MinimalNetwork()
        immutable = ImmutableNetworkView(network)
        
        # Should return 0 as fallback
        assert immutable.number_of_edges() == 0


class TestImmutableNetworkViewEdgeCases:
    """Test edge cases for ImmutableNetworkView."""

    def test_empty_network(self):
        """Test immutable view of empty network."""
        network = MockNetwork()
        immutable = ImmutableNetworkView(network)
        
        assert immutable.number_of_nodes() == 0
        assert immutable.number_of_edges() == 0
        assert len(immutable.get_nodes()) == 0
        assert len(immutable.get_edges()) == 0

    def test_deep_copy_isolation(self):
        """Test that deep copy provides proper isolation."""
        network = MockNetwork()
        network.add_node("original")
        
        immutable = ImmutableNetworkView(network, deep_copy=True)
        
        # Modify original network
        network.add_node("modified")
        
        # Immutable view should not see the change
        nodes = immutable.get_nodes()
        assert len(nodes) == 1
        assert "original" in nodes
        assert "modified" not in nodes

    def test_reference_mode_sees_changes(self):
        """Test that reference mode (deep_copy=False) sees changes."""
        network = MockNetwork()
        network.add_node("original")
        
        immutable = ImmutableNetworkView(network, deep_copy=False)
        
        # Get initial nodes
        initial_nodes = immutable.get_nodes()
        assert len(initial_nodes) == 1
        
        # Modify original network
        network.add_node("new")
        
        # With reference mode, changes ARE visible
        # (This tests that deep_copy=False actually uses reference)
        updated_nodes = immutable.get_nodes()
        assert len(updated_nodes) == 2

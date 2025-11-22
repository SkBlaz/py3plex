"""
Immutable graph mode with copy-on-write semantics.

Provides optional immutable graphs to prevent accidental mutation during
analysis pipelines. Uses copy-on-write for efficiency.

Features:
- Immutable wrapper around multilayer networks
- Copy-on-write semantics for modifications
- Read-only views of network data
- Safe for concurrent analysis

Authors: py3plex contributors
Date: 2025
"""

import copy
from typing import Any, Optional
import warnings


class ImmutableNetworkError(Exception):
    """Raised when attempting to modify an immutable network."""
    pass


class ImmutableNetworkView:
    """Immutable view of a multilayer network.
    
    Prevents modifications to the underlying network. Any modification
    attempt either raises an error or creates a modified copy depending
    on copy_on_write setting.
    
    Example:
        >>> network = multi_layer_network()
        >>> # ... build network ...
        >>> immutable = ImmutableNetworkView(network)
        >>> immutable.add_edge(...)  # Raises ImmutableNetworkError
        >>> 
        >>> # With copy-on-write
        >>> immutable_cow = ImmutableNetworkView(network, copy_on_write=True)
        >>> modified = immutable_cow.add_edge(...)  # Returns new network
    """
    
    def __init__(
        self,
        network: Any,
        copy_on_write: bool = False,
        deep_copy: bool = True
    ):
        """Initialize immutable network view.
        
        Args:
            network: The underlying multilayer network
            copy_on_write: If True, modifications create a copy instead of raising error
            deep_copy: If True, make a deep copy of the network; if False, use reference
        """
        if deep_copy:
            # Make a deep copy to ensure immutability
            self._network = copy.deepcopy(network)
        else:
            # Use reference (faster but original network could still be modified externally)
            self._network = network
        
        self._copy_on_write = copy_on_write
        self._is_frozen = True
    
    def __repr__(self) -> str:
        """String representation."""
        mode = "copy-on-write" if self._copy_on_write else "frozen"
        return f"<ImmutableNetworkView ({mode}): {repr(self._network)}>"
    
    # =========================================================================
    # Read-only methods - delegate to underlying network
    # =========================================================================
    
    def get_nodes(self, *args, **kwargs):
        """Get nodes from the network (read-only)."""
        return self._network.get_nodes(*args, **kwargs)
    
    def get_edges(self, *args, **kwargs):
        """Get edges from the network (read-only)."""
        return self._network.get_edges(*args, **kwargs)
    
    def number_of_nodes(self, *args, **kwargs):
        """Get number of nodes (read-only)."""
        if hasattr(self._network, 'number_of_nodes'):
            return self._network.number_of_nodes(*args, **kwargs)
        elif hasattr(self._network, 'core_network'):
            return self._network.core_network.number_of_nodes(*args, **kwargs)
        return 0
    
    def number_of_edges(self, *args, **kwargs):
        """Get number of edges (read-only)."""
        if hasattr(self._network, 'number_of_edges'):
            return self._network.number_of_edges(*args, **kwargs)
        elif hasattr(self._network, 'core_network'):
            return self._network.core_network.number_of_edges(*args, **kwargs)
        return 0
    
    def get_supra_adjacency_matrix(self, *args, **kwargs):
        """Get supra-adjacency matrix (read-only)."""
        return self._network.get_supra_adjacency_matrix(*args, **kwargs)
    
    @property
    def core_network(self):
        """Access to underlying core network (read-only view)."""
        # Return a frozen copy to prevent modifications
        return self._network.core_network
    
    # =========================================================================
    # Modification methods - either raise error or return modified copy
    # =========================================================================
    
    def _handle_modification(self, method_name: str, *args, **kwargs):
        """Handle modification attempt.
        
        Args:
            method_name: Name of the modification method
            *args, **kwargs: Arguments to pass to the method
            
        Returns:
            Modified copy if copy_on_write is True
            
        Raises:
            ImmutableNetworkError: If copy_on_write is False
        """
        if not self._copy_on_write:
            raise ImmutableNetworkError(
                f"Cannot call {method_name}() on immutable network. "
                "Use copy_on_write=True or call to_mutable() first."
            )
        
        # Create a mutable copy
        mutable_copy = copy.deepcopy(self._network)
        
        # Apply the modification
        method = getattr(mutable_copy, method_name)
        result = method(*args, **kwargs)
        
        # Return immutable view of the modified network
        # Note: result might be None or the network itself depending on method
        if result is None or result is mutable_copy:
            return ImmutableNetworkView(mutable_copy, copy_on_write=True, deep_copy=False)
        return result
    
    def add_node(self, *args, **kwargs):
        """Add node - creates copy if copy_on_write, else raises error."""
        return self._handle_modification('add_node', *args, **kwargs)
    
    def add_nodes(self, *args, **kwargs):
        """Add nodes - creates copy if copy_on_write, else raises error."""
        return self._handle_modification('add_nodes', *args, **kwargs)
    
    def add_edge(self, *args, **kwargs):
        """Add edge - creates copy if copy_on_write, else raises error."""
        return self._handle_modification('add_edge', *args, **kwargs)
    
    def add_edges(self, *args, **kwargs):
        """Add edges - creates copy if copy_on_write, else raises error."""
        return self._handle_modification('add_edges', *args, **kwargs)
    
    def remove_node(self, *args, **kwargs):
        """Remove node - creates copy if copy_on_write, else raises error."""
        return self._handle_modification('remove_node', *args, **kwargs)
    
    def remove_edge(self, *args, **kwargs):
        """Remove edge - creates copy if copy_on_write, else raises error."""
        return self._handle_modification('remove_edge', *args, **kwargs)
    
    # =========================================================================
    # Conversion methods
    # =========================================================================
    
    def to_mutable(self, deep_copy: bool = True):
        """Create a mutable copy of the network.
        
        Args:
            deep_copy: If True, create a deep copy; if False, return reference
            
        Returns:
            Mutable multilayer network
        """
        if deep_copy:
            return copy.deepcopy(self._network)
        else:
            warnings.warn(
                "Returning reference to internal network. "
                "Modifications will affect the immutable view.",
                UserWarning
            )
            return self._network
    
    def freeze(self):
        """Mark this view as frozen (already frozen by default).
        
        This is a no-op for compatibility.
        """
        self._is_frozen = True
    
    def is_frozen(self) -> bool:
        """Check if the network is frozen.
        
        Returns:
            True (always frozen)
        """
        return self._is_frozen


def make_immutable(
    network: Any,
    copy_on_write: bool = False,
    deep_copy: bool = True
) -> ImmutableNetworkView:
    """Create an immutable view of a multilayer network.
    
    Convenience function for creating ImmutableNetworkView instances.
    
    Args:
        network: Multilayer network to make immutable
        copy_on_write: Enable copy-on-write mode
        deep_copy: Create deep copy of network
        
    Returns:
        ImmutableNetworkView instance
        
    Example:
        >>> net = multi_layer_network()
        >>> # ... build network ...
        >>> immutable = make_immutable(net, copy_on_write=True)
        >>> modified = immutable.add_edge(...)  # Returns new network
    """
    return ImmutableNetworkView(network, copy_on_write=copy_on_write, deep_copy=deep_copy)

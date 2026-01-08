"""Test for empty group handling in SelectionUQ.

This test verifies that SelectionUQ handles cases where grouping is configured
but no groups are produced (e.g., no items match the selection criteria).
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q


def test_empty_groups_handled_gracefully():
    """Test that empty groups are handled without raising ValueError."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Create a very simple network
    edges = [
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    
    # Query that might produce empty groups in some samples
    # Using seed method with small network - some samples may have no items
    # after filtering if the computation fails
    result = (
        Q.nodes()
        .where(degree__gt=0)  # Simple filter
        .compute("degree")
        .order_by("degree", desc=True)
        .limit(5)
        .uq(method="seed", n_samples=5, seed=42)
        .execute(net)
    )
    
    # Should not raise ValueError about empty groups
    assert "uq" in result.meta
    assert result.meta["uq"]["type"] == "selection"
    
    # Should have items (network is not empty)
    assert len(result.items) > 0


def test_truly_empty_network_with_uq():
    """Test UQ on a network that produces no results."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Empty network
    edges = []
    net.add_edges(edges, input_type="list")
    
    # Query on empty network should handle gracefully
    result = (
        Q.nodes()
        .compute("degree")
        .order_by("degree", desc=True)
        .limit(5)
        .uq(method="seed", n_samples=5, seed=42)
        .execute(net)
    )
    
    # Should complete without error
    assert "uq" in result.meta
    assert len(result.items) == 0  # No items in empty network


if __name__ == "__main__":
    test_empty_groups_handled_gracefully()
    print("✓ Empty groups handled gracefully")
    
    test_truly_empty_network_with_uq()
    print("✓ Empty network handled gracefully")
    
    print("\nAll tests passed!")

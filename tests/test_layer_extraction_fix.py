"""
Test for layer extraction fix - ensures get_layers returns list of graphs, not dict.

This test addresses the issue where get_layers() was returning a dictionary
as the second element instead of a list of NetworkX graphs, causing
AttributeError when iterating over the results.
"""

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Core imports
from py3plex.core import multinet

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("networkx not available")

try:
    from py3plex.algorithms.statistics.basic_statistics import core_network_statistics
    STATS_AVAILABLE = True
except ImportError:
    STATS_AVAILABLE = False
    logger.warning("statistics module not available")

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    # Create a mock pytest module
    class MockPytest:
        class mark:
            @staticmethod
            def skipif(condition, reason=None):
                def decorator(func):
                    if condition:
                        def skipped_func(*args, **kwargs):
                            logger.info(f"Skipping test: {reason}")
                            return None
                        return skipped_func
                    return func
                return decorator
    pytest = MockPytest()
    PYTEST_AVAILABLE = False

DEPENDENCIES_AVAILABLE = NETWORKX_AVAILABLE and STATS_AVAILABLE


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Required dependencies not available")
def test_get_layers_returns_list_of_graphs():
    """
    Test that get_layers() returns a list of NetworkX graphs as the second element,
    not a dictionary. This prevents the AttributeError when calling .nodes() on strings.
    """
    # Load a test network
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/epigenetics.gpickle",
        directed=False,
        input_type="gpickle_biomine"
    )
    
    # Get layers
    names, networks, multiedges = multilayer_network.get_layers(verbose=False)
    
    # Assert that networks is a list, not a dict
    assert isinstance(networks, (list, tuple)), \
        f"Expected networks to be a list or tuple, got {type(networks)}"
    
    # Assert that each element in networks is a NetworkX graph
    for i, network in enumerate(networks):
        assert hasattr(network, 'nodes'), \
            f"Network at index {i} does not have 'nodes' method. Type: {type(network)}"
        assert hasattr(network, 'edges'), \
            f"Network at index {i} does not have 'edges' method. Type: {type(network)}"
        
        # Verify we can call nodes() without error
        node_count = len(network.nodes())
        assert isinstance(node_count, int) and node_count >= 0, \
            f"Expected non-negative integer node count, got {node_count}"
    
    # Assert that names and networks have the same length
    assert len(names) == len(networks), \
        f"Names and networks should have same length. Got {len(names)} names and {len(networks)} networks"
    
    logger.info(f"Successfully extracted {len(networks)} layers")


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Required dependencies not available")
def test_layer_extraction_with_statistics():
    """
    Test the original example use case - iterating over layers and computing statistics.
    This is the exact pattern from example_layer_extraction.py that was failing.
    """
    # Load network
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/epigenetics.gpickle",
        directed=False,
        input_type="gpickle_biomine"
    )
    
    # Get layers
    names, networks, multiedges = multilayer_network.get_layers(verbose=False)
    
    # The original failing pattern - iterate and compute statistics
    statistics_computed = 0
    for name, network, multiedgelist in zip(names, networks, multiedges):
        # This should not raise AttributeError
        stats = core_network_statistics(network)
        
        # Verify we got a valid DataFrame back
        assert stats is not None, f"Statistics for layer {name} is None"
        assert hasattr(stats, 'shape'), f"Statistics should be a DataFrame for layer {name}"
        
        statistics_computed += 1
    
    assert statistics_computed > 0, "Should have computed statistics for at least one layer"
    logger.info(f"Successfully computed statistics for {statistics_computed} layers")


if __name__ == "__main__":
    # Allow running without pytest
    if DEPENDENCIES_AVAILABLE:
        logger.info("Running test_get_layers_returns_list_of_graphs...")
        try:
            test_get_layers_returns_list_of_graphs()
            logger.info("[OK] test_get_layers_returns_list_of_graphs passed")
        except AssertionError as e:
            logger.error(f"[X] test_get_layers_returns_list_of_graphs failed: {e}")
        
        logger.info("Running test_layer_extraction_with_statistics...")
        try:
            test_layer_extraction_with_statistics()
            logger.info("[OK] test_layer_extraction_with_statistics passed")
        except AssertionError as e:
            logger.error(f"[X] test_layer_extraction_with_statistics failed: {e}")
    else:
        logger.warning("Dependencies not available, skipping tests")

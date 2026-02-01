#!/usr/bin/env python3
"""
Property-based tests for Label Propagation community detection.

Tests properties of Label Propagation algorithms:
- Supra-graph label propagation
- Multiplex consensus label propagation
- Partition completeness
- Determinism with seed
- Community validity
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from py3plex.core.multinet import multi_layer_network

# Guard for label propagation availability
try:
    from py3plex.algorithms.community_detection.label_propagation import (
        multilayer_label_propagation_supra,
        multiplex_label_propagation_consensus,
    )
    LABEL_PROP_AVAILABLE = True
except ImportError:
    LABEL_PROP_AVAILABLE = False
    multilayer_label_propagation_supra = None
    multiplex_label_propagation_consensus = None


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_lp_supra_every_node_assigned(n):
    """
    Test that supra-graph label propagation assigns all node-layer pairs.
    
    Property: All node-layer tuples are in partition.
    """
    net = multi_layer_network(directed=False)
    
    # Create 2-layer network
    for i in range(n):
        net.add_nodes([
            {'source': f'n{i}', 'type': 'L1'},
            {'source': f'n{i}', 'type': 'L2'},
        ])
    
    # Add edges within each layer
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'},
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L2', 'target_type': 'L2'},
        ])
    
    result = multilayer_label_propagation_supra(
        net, omega=0.5, random_state=42
    )
    partition = result['partition_supra']
    
    # Check all node-layer pairs assigned
    node_layers = set(net.get_nodes())
    
    assert set(partition.keys()) == node_layers, \
        "Not all node-layer pairs assigned"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_lp_supra_no_foreign_nodes(n):
    """
    Test that partition contains no nodes not in graph.
    
    Property: partition.keys() ⊆ network nodes.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    result = multilayer_label_propagation_supra(net, random_state=42)
    partition = result['partition_supra']
    
    # Check no foreign nodes
    partition_nodes = set(partition.keys())
    graph_nodes = set(net.get_nodes())
    
    assert partition_nodes.issubset(graph_nodes), \
        f"Foreign nodes in partition: {partition_nodes - graph_nodes}"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_lp_supra_community_ids_valid(n):
    """
    Test that community IDs are valid non-negative integers.
    
    Property: All community IDs are non-negative integers.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    result = multilayer_label_propagation_supra(net, random_state=42)
    partition = result['partition_supra']
    
    for comm_id in partition.values():
        assert isinstance(comm_id, (int, np.int64, np.int32)), \
            f"Community ID not an integer: {type(comm_id)}"
        assert comm_id >= 0, \
            f"Community ID negative: {comm_id}"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=3, max_value=10))
def test_lp_supra_at_least_one_community(n):
    """
    Test that label propagation finds at least one community.
    
    Property: Number of communities >= 1.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    result = multilayer_label_propagation_supra(net, random_state=42)
    partition = result['partition_supra']
    n_communities = len(set(partition.values()))
    
    assert n_communities >= 1, \
        f"Found {n_communities} communities (expected >= 1)"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_lp_supra_deterministic_with_seed(n):
    """
    Test that label propagation is deterministic with same seed.
    
    Property: Same random_state produces same partition.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    seed = 42
    
    result1 = multilayer_label_propagation_supra(net, random_state=seed)
    result2 = multilayer_label_propagation_supra(net, random_state=seed)
    
    assert result1['partition_supra'] == result2['partition_supra'], \
        "Label propagation not deterministic with same random_state"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(omega=st.floats(min_value=0.0, max_value=2.0))
def test_lp_supra_omega_parameter_valid(omega):
    """
    Test that label propagation accepts valid omega parameters.
    
    Property: Algorithm should run for omega in [0.0, 2.0].
    """
    net = multi_layer_network(directed=False)
    
    # 2-layer network
    for i in range(5):
        net.add_nodes([
            {'source': f'n{i}', 'type': 'L1'},
            {'source': f'n{i}', 'type': 'L2'},
        ])
    
    for i in range(4):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'},
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L2', 'target_type': 'L2'},
        ])
    
    # Should not raise exception
    result = multilayer_label_propagation_supra(
        net, omega=omega, random_state=42
    )
    
    assert 'partition_supra' in result, \
        "Result should contain partition_supra"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(n_per_component=st.integers(min_value=3, max_value=5))
def test_lp_supra_disconnected_components_separate_communities(n_per_component):
    """
    Test that disconnected components tend to be in different communities.
    
    Property: For K disconnected components, usually >= K communities.
    """
    net = multi_layer_network(directed=False)
    
    # Create 2 disconnected cliques
    for comp in range(2):
        for i in range(n_per_component):
            node_id = f'c{comp}_n{i}'
            net.add_nodes([{'source': node_id, 'type': 'L1'}])
        
        for i in range(n_per_component):
            for j in range(i+1, n_per_component):
                net.add_edges([{
                    'source': f'c{comp}_n{i}',
                    'target': f'c{comp}_n{j}',
                    'source_type': 'L1',
                    'target_type': 'L1'
                }])
    
    result = multilayer_label_propagation_supra(net, random_state=42)
    partition = result['partition_supra']
    n_communities = len(set(partition.values()))
    
    # Should find at least 2 communities
    assert n_communities >= 2, \
        f"Found {n_communities} communities but have 2 disconnected components"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_lp_supra_converged_flag(n):
    """
    Test that convergence flag is present and boolean.
    
    Property: Result contains 'converged' boolean field.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    result = multilayer_label_propagation_supra(net, random_state=42)
    
    assert 'converged' in result, \
        "Result should contain 'converged' field"
    assert isinstance(result['converged'], bool), \
        f"'converged' should be bool, got {type(result['converged'])}"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_lp_consensus_every_node_assigned(n):
    """
    Test that consensus label propagation assigns all nodes.
    
    Property: All base nodes are in partition when using majority projection.
    """
    net = multi_layer_network(directed=False)
    
    # Create 2-layer network
    for i in range(n):
        net.add_nodes([
            {'source': f'n{i}', 'type': 'L1'},
            {'source': f'n{i}', 'type': 'L2'},
        ])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'},
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L2', 'target_type': 'L2'},
        ])
    
    result = multiplex_label_propagation_consensus(
        net, random_state=42
    )
    
    # Check node-level partition (consensus gives node assignments, not node-layer pairs)
    partition_nodes = result["partition_nodes"]
    base_nodes = set([n[0] for n in net.get_nodes()])  # Extract base node names
    
    assert set(partition_nodes.keys()) == base_nodes, \
        "Not all base nodes assigned in consensus partition"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_lp_consensus_deterministic_with_seed(n):
    """
    Test that consensus label propagation is deterministic with seed.
    
    Property: Same random_state produces same partition.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([
            {'source': f'n{i}', 'type': 'L1'},
            {'source': f'n{i}', 'type': 'L2'},
        ])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'},
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L2', 'target_type': 'L2'},
        ])
    
    seed = 42
    
    result1 = multiplex_label_propagation_consensus(net, random_state=seed)
    result2 = multiplex_label_propagation_consensus(net, random_state=seed)
    
    assert result1["partition_nodes"] == result2["partition_nodes"], \
        "Consensus LP not deterministic with same random_state"


@pytest.mark.skipif(not LABEL_PROP_AVAILABLE, reason="Label propagation not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_lp_consensus_converged_flag(n):
    """
    Test that consensus result contains converged flag.
    
    Property: Result contains 'converged' boolean field.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([
            {'source': f'n{i}', 'type': 'L1'},
            {'source': f'n{i}', 'type': 'L2'},
        ])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'},
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L2', 'target_type': 'L2'},
        ])
    
    result = multiplex_label_propagation_consensus(net, random_state=42)
    
    assert 'converged' in result, \
        "Result should contain 'converged' field"
    assert isinstance(result['converged'], bool), \
        f"'converged' should be bool, got {type(result['converged'])}"


# Import numpy if needed for int64 type checking
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

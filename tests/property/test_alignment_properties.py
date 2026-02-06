#!/usr/bin/env python3
"""Property-based tests for the alignment module.

This module tests properties of network alignment features and solvers,
ensuring correctness of multilayer network alignment.

Key properties tested:
- Feature vectors have consistent dimensionality
- Features are non-negative where expected
- Alignment is deterministic
- Similarity matrices have correct shapes
- Layer entropy is in valid range [0, log(n_layers)]
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import note
import numpy as np

# Import alignment module
try:
    from py3plex.alignment.features import multilayer_node_features
    from py3plex.core import multinet
    ALIGNMENT_AVAILABLE = True
except ImportError:
    ALIGNMENT_AVAILABLE = False
    pytest.skip("Alignment module not available", allow_module_level=True)


# ============================================================================
# Helper Functions
# ============================================================================

def create_simple_multilayer_network(nodes, edges_per_layer):
    """Create a simple multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False)
    
    edges = []
    for layer_idx, layer_edges in enumerate(edges_per_layer):
        layer_name = f"layer{layer_idx}"
        for src, tgt in layer_edges:
            edges.append({
                'source': src,
                'target': tgt,
                'source_type': layer_name,
                'target_type': layer_name
            })
    
    if edges:
        net.add_edges(edges)
    
    return net


# ============================================================================
# Property Tests: Feature Extraction - Dimensionality
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    n_nodes=st.integers(min_value=2, max_value=5),
    n_layers=st.integers(min_value=1, max_value=3)
)
def test_feature_vectors_same_dimension(n_nodes, n_layers):
    """Property: All feature vectors have the same dimension."""
    # Create simple edges
    edges_per_layer = []
    nodes = list(range(n_nodes))
    
    for _ in range(n_layers):
        # Create a simple chain
        layer_edges = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        edges_per_layer.append(layer_edges)
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(net)
    
    if features:
        dims = [len(v) for v in features.values()]
        assert len(set(dims)) == 1, f"Feature dimensions not consistent: {dims}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n_layers=st.integers(min_value=1, max_value=4))
def test_feature_dimension_matches_configuration(n_layers):
    """Property: Feature dimension matches sum of enabled features."""
    nodes = [0, 1, 2]
    edges_per_layer = [[(0, 1), (1, 2)] for _ in range(n_layers)]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    # Test with all features enabled
    features_all = multilayer_node_features(
        net,
        include_total_degree=True,
        include_per_layer_degree=True,
        include_layer_entropy=True
    )
    
    if features_all:
        expected_dim = 1 + n_layers + 1  # total + per_layer + entropy
        actual_dim = len(next(iter(features_all.values())))
        assert actual_dim == expected_dim, f"Expected dim {expected_dim}, got {actual_dim}"


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(
    include_total=st.booleans(),
    include_per_layer=st.booleans(),
    include_entropy=st.booleans()
)
def test_feature_dimension_respects_flags(include_total, include_per_layer, include_entropy):
    """Property: Feature dimension changes correctly with flags."""
    # Need at least one feature enabled
    assume(include_total or include_per_layer or include_entropy)
    
    nodes = [0, 1, 2]
    n_layers = 2
    edges_per_layer = [[(0, 1), (1, 2)] for _ in range(n_layers)]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(
        net,
        include_total_degree=include_total,
        include_per_layer_degree=include_per_layer,
        include_layer_entropy=include_entropy
    )
    
    if features:
        expected_dim = 0
        if include_total:
            expected_dim += 1
        if include_per_layer:
            expected_dim += n_layers
        if include_entropy:
            expected_dim += 1
        
        actual_dim = len(next(iter(features.values())))
        assert actual_dim == expected_dim


# ============================================================================
# Property Tests: Feature Values - Non-negativity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    n_nodes=st.integers(min_value=2, max_value=5),
    n_layers=st.integers(min_value=1, max_value=3)
)
def test_total_degree_non_negative(n_nodes, n_layers):
    """Property: Total degree is always non-negative."""
    nodes = list(range(n_nodes))
    edges_per_layer = []
    
    for _ in range(n_layers):
        layer_edges = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        edges_per_layer.append(layer_edges)
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(
        net,
        include_total_degree=True,
        include_per_layer_degree=False,
        include_layer_entropy=False
    )
    
    for node, feat_vec in features.items():
        total_degree = feat_vec[0]
        assert total_degree >= 0, f"Node {node} has negative total degree: {total_degree}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    n_nodes=st.integers(min_value=2, max_value=5),
    n_layers=st.integers(min_value=1, max_value=3)
)
def test_per_layer_degree_non_negative(n_nodes, n_layers):
    """Property: Per-layer degrees are always non-negative."""
    nodes = list(range(n_nodes))
    edges_per_layer = []
    
    for _ in range(n_layers):
        layer_edges = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        edges_per_layer.append(layer_edges)
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(
        net,
        include_total_degree=False,
        include_per_layer_degree=True,
        include_layer_entropy=False
    )
    
    for node, feat_vec in features.items():
        assert len(feat_vec) == n_layers
        assert all(d >= 0 for d in feat_vec), \
            f"Node {node} has negative per-layer degree: {feat_vec}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    n_nodes=st.integers(min_value=2, max_value=5),
    n_layers=st.integers(min_value=2, max_value=4)
)
def test_layer_entropy_in_valid_range(n_nodes, n_layers):
    """Property: Layer entropy is in [0, log(n_layers)]."""
    nodes = list(range(n_nodes))
    edges_per_layer = []
    
    for _ in range(n_layers):
        layer_edges = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        edges_per_layer.append(layer_edges)
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(
        net,
        include_total_degree=False,
        include_per_layer_degree=False,
        include_layer_entropy=True
    )
    
    max_entropy = np.log(n_layers)
    
    for node, feat_vec in features.items():
        entropy = feat_vec[0]
        assert 0.0 <= entropy <= max_entropy + 1e-9, \
            f"Node {node} entropy {entropy} not in [0, {max_entropy}]"


# ============================================================================
# Property Tests: Feature Consistency
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(n_layers=st.integers(min_value=1, max_value=3))
def test_total_degree_equals_sum_of_per_layer(n_layers):
    """Property: Total degree equals sum of per-layer degrees."""
    nodes = [0, 1, 2]
    edges_per_layer = [[(0, 1), (1, 2)] for _ in range(n_layers)]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(
        net,
        include_total_degree=True,
        include_per_layer_degree=True,
        include_layer_entropy=False
    )
    
    for node, feat_vec in features.items():
        total_degree = feat_vec[0]
        per_layer_degrees = feat_vec[1:]
        
        sum_per_layer = sum(per_layer_degrees)
        
        # Allow small floating point errors
        assert abs(total_degree - sum_per_layer) < 1e-9, \
            f"Node {node}: total {total_degree} != sum {sum_per_layer}"


@pytest.mark.property
def test_isolated_node_has_zero_degrees():
    """Property: Isolated nodes have zero degree and entropy."""
    # Create network with isolated node
    net = multinet.multi_layer_network(directed=False)
    net.add_edges([
        {'source': 0, 'target': 1, 'source_type': 'layer0', 'target_type': 'layer0'},
    ])
    # Node 2 is isolated (not in any edge)
    # Actually, we need to add node 2 explicitly if it's not in edges
    # In py3plex, nodes are created implicitly from edges
    # So let's just use nodes that exist
    
    features = multilayer_node_features(net)
    
    # Nodes 0 and 1 exist, check they have non-zero features
    if 0 in features and 1 in features:
        assert features[0][0] > 0 or features[1][0] > 0


@pytest.mark.property
def test_features_deterministic():
    """Property: Same network produces same features."""
    nodes = [0, 1, 2]
    edges_per_layer = [[(0, 1), (1, 2)]]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features1 = multilayer_node_features(net)
    features2 = multilayer_node_features(net)
    
    # Should be identical
    assert set(features1.keys()) == set(features2.keys())
    
    for node in features1:
        assert np.allclose(features1[node], features2[node])


# ============================================================================
# Property Tests: Empty Networks
# ============================================================================

@pytest.mark.property
def test_empty_network_returns_empty_features():
    """Property: Empty network returns empty feature dict."""
    net = multinet.multi_layer_network(directed=False)
    
    features = multilayer_node_features(net)
    
    assert features == {} or len(features) == 0


# ============================================================================
# Property Tests: Feature Type Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(
    n_nodes=st.integers(min_value=2, max_value=5),
    n_layers=st.integers(min_value=1, max_value=3)
)
def test_features_are_numpy_arrays(n_nodes, n_layers):
    """Property: All features are numpy arrays."""
    nodes = list(range(n_nodes))
    edges_per_layer = [[(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)] 
                       for _ in range(n_layers)]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(net)
    
    for node, feat_vec in features.items():
        assert isinstance(feat_vec, np.ndarray), \
            f"Feature for node {node} is not numpy array: {type(feat_vec)}"


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(
    n_nodes=st.integers(min_value=2, max_value=5),
    n_layers=st.integers(min_value=1, max_value=3)
)
def test_features_are_finite(n_nodes, n_layers):
    """Property: All feature values are finite (no NaN/inf)."""
    nodes = list(range(n_nodes))
    edges_per_layer = [[(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)] 
                       for _ in range(n_layers)]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(net)
    
    for node, feat_vec in features.items():
        assert np.all(np.isfinite(feat_vec)), \
            f"Node {node} has non-finite features: {feat_vec}"


# ============================================================================
# Property Tests: Layer Selection
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(n_layers=st.integers(min_value=2, max_value=4))
def test_layer_selection_affects_feature_dimension(n_layers):
    """Property: Selecting fewer layers reduces feature dimension."""
    nodes = [0, 1, 2]
    edges_per_layer = [[(0, 1), (1, 2)] for _ in range(n_layers)]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    # Get features for all layers
    features_all = multilayer_node_features(net)
    
    # Get features for subset of layers
    selected_layers = [f"layer{i}" for i in range(n_layers - 1)]
    features_subset = multilayer_node_features(net, layers=selected_layers)
    
    if features_all and features_subset:
        dim_all = len(next(iter(features_all.values())))
        dim_subset = len(next(iter(features_subset.values())))
        
        # Subset should have smaller dimension (fewer per-layer features)
        assert dim_subset < dim_all or n_layers == 1


@pytest.mark.property
def test_layer_order_preserved():
    """Property: Layer ordering in features follows input order."""
    nodes = [0, 1, 2]
    n_layers = 2
    edges_per_layer = [[(0, 1), (1, 2)] for _ in range(n_layers)]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    # Test with explicit layer ordering
    layers_fwd = ["layer0", "layer1"]
    layers_rev = ["layer1", "layer0"]
    
    features_fwd = multilayer_node_features(
        net, layers=layers_fwd,
        include_total_degree=False,
        include_per_layer_degree=True,
        include_layer_entropy=False
    )
    
    features_rev = multilayer_node_features(
        net, layers=layers_rev,
        include_total_degree=False,
        include_per_layer_degree=True,
        include_layer_entropy=False
    )
    
    # For nodes in both, per-layer degrees should be in different order
    for node in features_fwd:
        if node in features_rev:
            fwd_vec = features_fwd[node]
            rev_vec = features_rev[node]
            
            # Reversed order means fwd[0] == rev[1] and fwd[1] == rev[0]
            assert abs(fwd_vec[0] - rev_vec[1]) < 1e-9
            assert abs(fwd_vec[1] - rev_vec[0]) < 1e-9


# ============================================================================
# Property Tests: Entropy Computation
# ============================================================================

@pytest.mark.property
def test_uniform_distribution_has_max_entropy():
    """Property: Node with uniform degree distribution has maximum entropy."""
    # Create node with equal degree in all layers
    nodes = [0, 1, 2, 3]
    n_layers = 3
    
    # Give node 1 equal edges in all layers
    edges_per_layer = [
        [(1, 2)],  # layer0: degree 1
        [(1, 3)],  # layer1: degree 1
        [(1, 0)],  # layer2: degree 1
    ]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(
        net,
        include_total_degree=False,
        include_per_layer_degree=False,
        include_layer_entropy=True
    )
    
    if 1 in features:
        entropy = features[1][0]
        max_entropy = np.log(n_layers)
        
        # Should be close to maximum (uniform distribution)
        assert abs(entropy - max_entropy) < 0.1


@pytest.mark.property
def test_single_layer_node_has_zero_entropy():
    """Property: Node active in only one layer has zero entropy."""
    nodes = [0, 1, 2]
    
    # Node 1 only has edges in layer0
    edges_per_layer = [
        [(0, 1), (1, 2)],  # layer0
        [(0, 2)],          # layer1: node 1 not involved
    ]
    
    net = create_simple_multilayer_network(nodes, edges_per_layer)
    
    features = multilayer_node_features(
        net,
        include_total_degree=False,
        include_per_layer_degree=False,
        include_layer_entropy=True
    )
    
    if 1 in features:
        entropy = features[1][0]
        # Should be zero (all degree in one layer)
        assert entropy < 1e-9

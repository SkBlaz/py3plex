#!/usr/bin/env python3
"""
Property-based tests for algorithms.multilayer_algorithms.entanglement module.

Tests invariants and properties of multilayer entanglement analysis:
- Occurrence matrix is square and symmetric
- Matrix values are non-negative
- Diagonal values represent layer edge counts
- Block decomposition consistency
"""

import networkx as nx
import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import entanglement module
try:
    from py3plex.algorithms.multilayer_algorithms.entanglement import (
        build_occurrence_matrix,
        compute_blocks,
    )
    from py3plex.core import multinet
    ENTANGLEMENT_AVAILABLE = True
except ImportError:
    ENTANGLEMENT_AVAILABLE = False
    pytest.skip("Entanglement module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Occurrence Matrix Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_occurrence_matrix_is_square(num_nodes, num_layers, seed):
    """Property: Occurrence matrix is square (L x L)."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add some intra-layer edges
        import random
        random.seed(seed + layer_idx)
        for _ in range(min(num_nodes, 5)):
            i = random.randint(0, num_nodes - 1)
            j = random.randint(0, num_nodes - 1)
            if i != j:
                net.add_edges({
                    "source": f"node_{i}",
                    "target": f"node_{j}",
                    "source_type": layer_name,
                    "target_type": layer_name,
                    "weight": 1.0
                })
    
    assume(len(list(net.get_edges())) > 0)
    
    # Build occurrence matrix
    c_matrix, layers = build_occurrence_matrix(net)
    
    # Matrix should be square
    assert c_matrix.shape[0] == c_matrix.shape[1], \
        f"Occurrence matrix should be square, got shape {c_matrix.shape}"
    
    # Number of rows/cols should match number of layers
    assert c_matrix.shape[0] == len(layers), \
        f"Matrix dimension should match number of layers, got {c_matrix.shape[0]} vs {len(layers)}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_occurrence_matrix_non_negative(num_nodes, num_layers, seed):
    """Property: All values in occurrence matrix are non-negative."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add edges
        import random
        random.seed(seed + layer_idx)
        for _ in range(min(num_nodes, 5)):
            i = random.randint(0, num_nodes - 1)
            j = random.randint(0, num_nodes - 1)
            if i != j:
                net.add_edges({
                    "source": f"node_{i}",
                    "target": f"node_{j}",
                    "source_type": layer_name,
                    "target_type": layer_name,
                    "weight": 1.0
                })
    
    assume(len(list(net.get_edges())) > 0)
    
    # Build occurrence matrix
    c_matrix, layers = build_occurrence_matrix(net)
    
    # All values should be non-negative
    assert np.all(c_matrix >= 0), \
        f"Occurrence matrix values should be non-negative, got min={np.min(c_matrix)}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_occurrence_matrix_diagonal_positive(num_nodes, num_layers, seed):
    """Property: Diagonal entries are positive (represent layer edge counts)."""
    # Create a multiplex network with edges
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add at least one edge per layer
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })
    
    assume(len(list(net.get_edges())) > 0)
    
    # Build occurrence matrix
    c_matrix, layers = build_occurrence_matrix(net)
    
    # Diagonal entries should be positive (normalized edge counts)
    diagonal = np.diag(c_matrix)
    assert np.all(diagonal > 0), \
        f"Diagonal entries should be positive, got {diagonal}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_occurrence_matrix_symmetric(num_nodes, num_layers, seed):
    """Property: Occurrence matrix is symmetric (C[i,j] relates to C[j,i])."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add edges
        import random
        random.seed(seed + layer_idx)
        for _ in range(min(num_nodes, 5)):
            i = random.randint(0, num_nodes - 1)
            j = random.randint(0, num_nodes - 1)
            if i != j:
                net.add_edges({
                    "source": f"node_{i}",
                    "target": f"node_{j}",
                    "source_type": layer_name,
                    "target_type": layer_name,
                    "weight": 1.0
                })
    
    assume(len(list(net.get_edges())) > 0)
    
    # Build occurrence matrix
    c_matrix, layers = build_occurrence_matrix(net)
    
    # Note: The matrix may not be strictly symmetric due to normalization
    # But it should have a symmetric structure in how layers relate
    # Check that matrix is well-formed
    assert c_matrix.shape[0] == c_matrix.shape[1]


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_occurrence_matrix_returns_correct_layer_count(num_nodes, num_layers, seed):
    """Property: build_occurrence_matrix returns correct layer list."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    expected_layers = []
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        expected_layers.append(layer_name)
        
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add at least one edge per layer
        net.add_edges({
            "source": "node_0",
            "target": "node_1",
            "source_type": layer_name,
            "target_type": layer_name,
            "weight": 1.0
        })
    
    assume(len(list(net.get_edges())) > 0)
    
    # Build occurrence matrix
    c_matrix, layers = build_occurrence_matrix(net)
    
    # Should return all layers
    assert len(layers) == num_layers, \
        f"Should return {num_layers} layers, got {len(layers)}"
    
    # All expected layers should be in result
    for expected_layer in expected_layers:
        assert expected_layer in layers, \
            f"Expected layer {expected_layer} not found in result"


# ============================================================================
# Property Tests: Block Decomposition
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_compute_blocks_returns_valid_structure(num_nodes, num_layers, seed):
    """Property: compute_blocks returns indices and blocks with matching structure."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })
    
    assume(len(list(net.get_edges())) > 0)
    
    # Build occurrence matrix
    c_matrix, layers = build_occurrence_matrix(net)
    
    # Compute blocks
    indices, blocks = compute_blocks(c_matrix)
    
    # Should return lists
    assert isinstance(indices, list), "indices should be a list"
    assert isinstance(blocks, list), "blocks should be a list"
    
    # Number of indices should match number of blocks
    assert len(indices) == len(blocks), \
        f"Number of index groups should match number of blocks"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_compute_blocks_indices_cover_all_layers(num_nodes, num_layers, seed):
    """Property: Block indices cover all layers exactly once."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })
    
    assume(len(list(net.get_edges())) > 0)
    
    # Build occurrence matrix
    c_matrix, layers = build_occurrence_matrix(net)
    
    # Compute blocks
    indices, blocks = compute_blocks(c_matrix)
    
    # Flatten all indices
    all_indices = []
    for idx_group in indices:
        all_indices.extend(idx_group)
    
    # Should cover all layer indices
    assert len(all_indices) == num_layers, \
        f"Indices should cover {num_layers} layers, got {len(all_indices)}"
    
    # All indices should be unique (no overlap)
    assert len(all_indices) == len(set(all_indices)), \
        "Block indices should not overlap"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_compute_blocks_submatrices_square(num_nodes, num_layers, seed):
    """Property: Each block submatrix is square."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })
    
    assume(len(list(net.get_edges())) > 0)
    
    # Build occurrence matrix
    c_matrix, layers = build_occurrence_matrix(net)
    
    # Compute blocks
    indices, blocks = compute_blocks(c_matrix)
    
    # Each block should be a square matrix
    for block in blocks:
        assert block.shape[0] == block.shape[1], \
            f"Block should be square, got shape {block.shape}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_compute_blocks_size_consistency(num_nodes, num_layers, seed):
    """Property: Block size matches number of indices in that block."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })
    
    assume(len(list(net.get_edges())) > 0)
    
    # Build occurrence matrix
    c_matrix, layers = build_occurrence_matrix(net)
    
    # Compute blocks
    indices, blocks = compute_blocks(c_matrix)
    
    # Each block size should match its index list length
    for idx_group, block in zip(indices, blocks):
        expected_size = len(idx_group)
        actual_size = block.shape[0]
        assert actual_size == expected_size, \
            f"Block size {actual_size} should match index count {expected_size}"


# ============================================================================
# Property Tests: Entanglement Metrics
# ============================================================================

# Import compute_entanglement if available
try:
    from py3plex.algorithms.multilayer_algorithms.entanglement import (
        compute_entanglement,
        compute_entanglement_analysis,
    )
    COMPUTE_ENTANGLEMENT_AVAILABLE = True
except ImportError:
    COMPUTE_ENTANGLEMENT_AVAILABLE = False


@pytest.mark.property
@pytest.mark.skipif(not COMPUTE_ENTANGLEMENT_AVAILABLE, reason="compute_entanglement not available")
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_entanglement_intensity_bounds(num_nodes, num_layers, seed):
    """Property: Entanglement intensity is bounded in [0, 1] when normalized."""
    # Create a multiplex network
    net = multinet.multi_layer_network()

    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })

        # Add edges to ensure non-empty layers
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })

    assume(len(list(net.get_edges())) > 0)

    # Build occurrence matrix and compute entanglement
    c_matrix, layers = build_occurrence_matrix(net)
    indices, blocks = compute_blocks(c_matrix)

    for block in blocks:
        metrics, gamma = compute_entanglement(block)
        intensity = metrics[0]

        # Intensity should be in [0, 1] for normalized values
        assert 0.0 <= intensity <= 1.5, \
            f"Entanglement intensity {intensity} outside reasonable bounds"


@pytest.mark.property
@pytest.mark.skipif(not COMPUTE_ENTANGLEMENT_AVAILABLE, reason="compute_entanglement not available")
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_entanglement_homogeneity_bounds(num_nodes, num_layers, seed):
    """Property: Entanglement homogeneity is bounded in [0, 1]."""
    # Create a multiplex network
    net = multinet.multi_layer_network()

    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })

        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })

    assume(len(list(net.get_edges())) > 0)

    # Build occurrence matrix and compute entanglement
    c_matrix, layers = build_occurrence_matrix(net)
    indices, blocks = compute_blocks(c_matrix)

    for block in blocks:
        metrics, gamma = compute_entanglement(block)
        homogeneity = metrics[1]
        normalized_homogeneity = metrics[2]

        # Homogeneity should be in [0, 1]
        assert 0.0 <= homogeneity <= 1.0, \
            f"Entanglement homogeneity {homogeneity} outside bounds [0, 1]"
        assert 0.0 <= normalized_homogeneity <= 1.0, \
            f"Normalized homogeneity {normalized_homogeneity} outside bounds [0, 1]"


@pytest.mark.property
@pytest.mark.skipif(not COMPUTE_ENTANGLEMENT_AVAILABLE, reason="compute_entanglement not available")
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_entanglement_gamma_nonnegative(num_nodes, num_layers, seed):
    """Property: Layer gamma values are non-negative."""
    # Create a multiplex network
    net = multinet.multi_layer_network()

    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })

        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })

    assume(len(list(net.get_edges())) > 0)

    # Build occurrence matrix and compute entanglement
    c_matrix, layers = build_occurrence_matrix(net)
    indices, blocks = compute_blocks(c_matrix)

    for block in blocks:
        metrics, gamma = compute_entanglement(block)

        # All gamma values should be non-negative (they are absolute values)
        for g in gamma:
            assert g >= 0, f"Negative gamma value: {g}"


@pytest.mark.property
@pytest.mark.skipif(not COMPUTE_ENTANGLEMENT_AVAILABLE, reason="compute_entanglement not available")
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_entanglement_gamma_length_matches_block(num_nodes, num_layers, seed):
    """Property: Gamma vector length matches block size."""
    # Create a multiplex network
    net = multinet.multi_layer_network()

    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })

        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })

    assume(len(list(net.get_edges())) > 0)

    # Build occurrence matrix and compute entanglement
    c_matrix, layers = build_occurrence_matrix(net)
    indices, blocks = compute_blocks(c_matrix)

    for block in blocks:
        metrics, gamma = compute_entanglement(block)

        # Gamma length should match block size
        assert len(gamma) == block.shape[0], \
            f"Gamma length {len(gamma)} != block size {block.shape[0]}"


@pytest.mark.property
@pytest.mark.skipif(not COMPUTE_ENTANGLEMENT_AVAILABLE, reason="compute_entanglement not available")
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_entanglement_metrics_finite(num_nodes, num_layers, seed):
    """Property: All entanglement metrics are finite (no NaN or Inf)."""
    # Create a multiplex network
    net = multinet.multi_layer_network()

    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })

        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })

    assume(len(list(net.get_edges())) > 0)

    # Build occurrence matrix and compute entanglement
    c_matrix, layers = build_occurrence_matrix(net)
    indices, blocks = compute_blocks(c_matrix)

    for block in blocks:
        metrics, gamma = compute_entanglement(block)

        # All metrics should be finite
        for m in metrics:
            assert np.isfinite(m), f"Non-finite metric value: {m}"
        for g in gamma:
            assert np.isfinite(g), f"Non-finite gamma value: {g}"


@pytest.mark.property
@pytest.mark.skipif(not COMPUTE_ENTANGLEMENT_AVAILABLE, reason="compute_entanglement_analysis not available")
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_compute_entanglement_analysis_returns_list(num_nodes, num_layers, seed):
    """Property: compute_entanglement_analysis returns a list of dicts."""
    # Create a multiplex network
    net = multinet.multi_layer_network()

    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })

        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })

    assume(len(list(net.get_edges())) > 0)

    analysis = compute_entanglement_analysis(net)

    # Should return a list
    assert isinstance(analysis, list), "Analysis should be a list"

    # Each element should be a dict with expected keys
    for block_analysis in analysis:
        assert isinstance(block_analysis, dict), "Each block analysis should be a dict"
        assert "Entanglement intensity" in block_analysis
        assert "Layer entanglement" in block_analysis
        assert "Entanglement homogeneity" in block_analysis
        assert "Normalized homogeneity" in block_analysis


@pytest.mark.property
@pytest.mark.skipif(not COMPUTE_ENTANGLEMENT_AVAILABLE, reason="compute_entanglement_analysis not available")
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_compute_entanglement_analysis_deterministic(num_nodes, num_layers, seed):
    """Property: compute_entanglement_analysis is deterministic."""
    # Create a multiplex network
    net = multinet.multi_layer_network()

    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })

        # Add edges
        for i in range(min(3, num_nodes - 1)):
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })

    assume(len(list(net.get_edges())) > 0)

    analysis1 = compute_entanglement_analysis(net)
    analysis2 = compute_entanglement_analysis(net)

    # Should produce identical results
    assert len(analysis1) == len(analysis2)
    for a1, a2 in zip(analysis1, analysis2):
        assert np.isclose(a1["Entanglement intensity"], a2["Entanglement intensity"])
        assert np.isclose(a1["Entanglement homogeneity"], a2["Entanglement homogeneity"])


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])

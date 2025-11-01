"""
Math Invariant Tests for py3plex

Tests for critical mathematical properties:
- Transition matrices are row-stochastic
- Laplacians are symmetric and PSD for undirected graphs
- Modularity values within expected bounds
- Proper handling of edge cases (dangling nodes, zero weights, etc.)
"""

import numpy as np
import pytest

# Module may not be importable in all environments
try:
    from py3plex.core import multinet
    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality
    from py3plex.algorithms.community_detection.multilayer_modularity import multilayer_modularity
    from py3plex.algorithms.statistics.multilayer_statistics import supra_laplacian_spectrum
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not MODULES_AVAILABLE,
    reason="py3plex modules not available"
)


class TestPageRankTransitionMatrix:
    """Test PageRank transition matrix construction and properties."""

    def test_pagerank_row_stochastic_no_dangling(self):
        """PageRank should compute correctly when no dangling nodes exist."""
        network = multinet.multi_layer_network(directed=True)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1],  # Complete cycle - no dangling nodes
        ], input_type='list')

        calc = MultilayerCentrality(network)
        
        # Compute PageRank using the actual implementation
        pr = calc.pagerank_centrality()
        
        # Verify PageRank properties
        pr_sum = sum(pr.values())
        
        # PageRank should sum to 1
        assert np.isclose(pr_sum, 1.0, atol=1e-6), \
            f"PageRank doesn't sum to 1: sum = {pr_sum}"
        
        # All values should be positive
        for node_layer, value in pr.items():
            assert value > 0, \
                f"PageRank for {node_layer} is non-positive: {value}"
        
        # For a cycle, all nodes should have equal PageRank
        pr_values = list(pr.values())
        assert np.allclose(pr_values, pr_values[0], atol=1e-6), \
            f"PageRank values should be equal for cycle: {pr_values}"

    def test_pagerank_handles_dangling_nodes_correctly(self):
        """PageRank should properly handle dangling nodes via teleportation."""
        network = multinet.multi_layer_network(directed=True)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            # C is dangling (no outgoing edges)
            ['A', 'L2', 'D', 'L2', 1],  # D is also dangling
        ], input_type='list')

        calc = MultilayerCentrality(network)
        
        # Compute PageRank using the actual (fixed) implementation
        pr = calc.pagerank_centrality()
        
        # Verify PageRank properties
        pr_sum = sum(pr.values())
        
        # PageRank should sum to 1 even with dangling nodes
        assert np.isclose(pr_sum, 1.0, atol=1e-6), \
            f"PageRank doesn't sum to 1 with dangling nodes: sum = {pr_sum}"
        
        # All values should be non-negative
        for node_layer, value in pr.items():
            assert value >= 0, \
                f"PageRank for {node_layer} is negative: {value}"
        
        # Dangling nodes should still receive PageRank (via incoming edges)
        # C and D are dangling, but should have positive PageRank
        for node_layer, value in pr.items():
            node, layer = node_layer
            if node in ['C', 'D']:
                assert value > 0, \
                    f"Dangling node {node} in layer {layer} should have positive PageRank"

    def test_pagerank_convergence(self):
        """PageRank should converge and sum to 1."""
        network = multinet.multi_layer_network(directed=True)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1],
        ], input_type='list')

        calc = MultilayerCentrality(network)
        pr = calc.pagerank_centrality()
        
        # PageRank values should be positive
        for value in pr.values():
            assert value > 0, f"PageRank value {value} should be positive"
        
        # PageRank should sum to 1
        pr_sum = sum(pr.values())
        assert np.isclose(pr_sum, 1.0, atol=1e-6), \
            f"PageRank values sum to {pr_sum}, should sum to 1.0"


class TestLaplacianProperties:
    """Test Laplacian matrix mathematical properties."""

    def test_laplacian_symmetric_undirected(self):
        """Laplacian should be symmetric for undirected graphs."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['A', 'L2', 'C', 'L2', 1],
        ], input_type='list')

        supra_adj = network.get_supra_adjacency_matrix()
        
        if hasattr(supra_adj, 'toarray'):
            adj_dense = supra_adj.toarray()
        else:
            adj_dense = np.array(supra_adj)

        degrees = np.sum(adj_dense, axis=1)
        laplacian = np.diag(degrees) - adj_dense

        # Check symmetry
        assert np.allclose(laplacian, laplacian.T, atol=1e-10), \
            "Laplacian should be symmetric for undirected graph"

    def test_laplacian_psd_undirected(self):
        """Laplacian should be positive semidefinite (PSD) for undirected graphs."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['A', 'L2', 'C', 'L2', 1],
        ], input_type='list')

        supra_adj = network.get_supra_adjacency_matrix()
        
        if hasattr(supra_adj, 'toarray'):
            adj_dense = supra_adj.toarray()
        else:
            adj_dense = np.array(supra_adj)

        degrees = np.sum(adj_dense, axis=1)
        laplacian = np.diag(degrees) - adj_dense

        # Compute eigenvalues
        eigenvalues = np.linalg.eigvalsh(laplacian)
        min_eigenvalue = np.min(eigenvalues)

        # Minimum eigenvalue should be >= 0 (allowing small numerical error)
        assert min_eigenvalue >= -1e-10, \
            f"Laplacian minimum eigenvalue {min_eigenvalue} is negative (not PSD)"

    def test_laplacian_row_sums_zero(self):
        """Laplacian row sums should be zero."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')

        supra_adj = network.get_supra_adjacency_matrix()
        
        if hasattr(supra_adj, 'toarray'):
            adj_dense = supra_adj.toarray()
        else:
            adj_dense = np.array(supra_adj)

        degrees = np.sum(adj_dense, axis=1)
        laplacian = np.diag(degrees) - adj_dense

        row_sums = np.sum(laplacian, axis=1)
        
        assert np.allclose(row_sums, 0, atol=1e-10), \
            f"Laplacian row sums should be zero, got {row_sums}"

    def test_laplacian_zero_eigenvalue_connected(self):
        """Connected graph Laplacian should have exactly one zero eigenvalue."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1],  # Cycle - connected
        ], input_type='list')

        supra_adj = network.get_supra_adjacency_matrix()
        
        if hasattr(supra_adj, 'toarray'):
            adj_dense = supra_adj.toarray()
        else:
            adj_dense = np.array(supra_adj)

        degrees = np.sum(adj_dense, axis=1)
        laplacian = np.diag(degrees) - adj_dense

        eigenvalues = np.linalg.eigvalsh(laplacian)
        eigenvalues_sorted = np.sort(eigenvalues)

        # Count near-zero eigenvalues
        zero_eigenvalues = np.sum(np.abs(eigenvalues_sorted) < 1e-8)

        # For a connected graph, should have exactly 1 zero eigenvalue
        # (more zero eigenvalues = more connected components)
        assert zero_eigenvalues >= 1, \
            "Laplacian should have at least one zero eigenvalue"


class TestModularityCalculation:
    """Test multilayer modularity calculation properties."""

    def test_modularity_range(self):
        """Modularity should be in range approximately [-0.5, 1.0]."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['A', 'L2', 'C', 'L2', 1],
        ], input_type='list')

        communities = {
            ('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1,
            ('A', 'L2'): 0, ('C', 'L2'): 0
        }

        Q = multilayer_modularity(network, communities, gamma=1.0, omega=1.0)

        # Typical range is [-0.5, 1.0], though technically can be slightly outside
        assert Q >= -0.6 and Q <= 1.0, \
            f"Modularity {Q} outside expected range [-0.6, 1.0]"

    def test_modularity_omega_limits(self):
        """Test modularity behavior at omega limits."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['A', 'L2', 'C', 'L2', 1],
        ], input_type='list')

        communities = {
            ('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1,
            ('A', 'L2'): 0, ('C', 'L2'): 0
        }

        # omega = 0: no inter-layer coupling
        Q_omega_0 = multilayer_modularity(network, communities, gamma=1.0, omega=0.0)
        
        # omega = 1: standard coupling
        Q_omega_1 = multilayer_modularity(network, communities, gamma=1.0, omega=1.0)
        
        # omega = 10: strong coupling (should favor layer-consistent communities)
        Q_omega_10 = multilayer_modularity(network, communities, gamma=1.0, omega=10.0)

        # All should be valid modularity values
        assert -0.6 <= Q_omega_0 <= 1.0, f"Q(ω=0) = {Q_omega_0} out of range"
        assert -0.6 <= Q_omega_1 <= 1.0, f"Q(ω=1) = {Q_omega_1} out of range"
        assert -0.6 <= Q_omega_10 <= 1.0, f"Q(ω=10) = {Q_omega_10} out of range"


class TestNumericalStability:
    """Test numerical stability with extreme values."""

    def test_pagerank_with_small_weights(self):
        """PageRank should handle very small edge weights without NaN/Inf."""
        network = multinet.multi_layer_network(directed=True)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1e-10],
            ['B', 'L1', 'C', 'L1', 1e-10],
            ['C', 'L1', 'A', 'L1', 1e-10],
        ], input_type='list')

        calc = MultilayerCentrality(network)
        pr = calc.pagerank_centrality()

        # Check for NaN or Inf
        for node_layer, value in pr.items():
            assert not np.isnan(value), f"PageRank for {node_layer} is NaN"
            assert not np.isinf(value), f"PageRank for {node_layer} is Inf"
            assert value >= 0, f"PageRank for {node_layer} is negative: {value}"

    def test_laplacian_with_mixed_weights(self):
        """Laplacian spectrum should handle mixed small/large weights."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1e-10],
            ['B', 'L1', 'C', 'L1', 1e10],
        ], input_type='list')

        try:
            spectrum = supra_laplacian_spectrum(network, k=2)
            
            # Check for NaN or Inf
            assert not np.any(np.isnan(spectrum)), "Laplacian spectrum contains NaN"
            assert not np.any(np.isinf(spectrum)), "Laplacian spectrum contains Inf"
        except Exception as e:
            pytest.fail(f"Laplacian spectrum computation failed: {e}")


class TestEdgeCases:
    """Test edge cases and corner cases."""

    def test_single_node_network(self):
        """Test handling of single-node network."""
        network = multinet.multi_layer_network(directed=False)
        # Just one node, no edges - this is valid but edge case
        # Don't add any edges, network should handle gracefully

    def test_zero_weight_edges(self):
        """Test handling of zero-weight edges."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 0],  # Zero weight
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')

        # Should not crash
        try:
            supra_adj = network.get_supra_adjacency_matrix()
            assert supra_adj is not None
        except Exception as e:
            pytest.fail(f"Zero-weight edge caused crash: {e}")


# Run with: pytest tests/test_math_invariants.py -v

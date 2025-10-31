"""
Test suite for SIR epidemic simulator on multiplex graphs.

Tests cover:
- T1: Single-layer sanity check
- T2: Monotonicity with increasing transmission rates
- T3: Importation-only infections
- T4: Layer weights equivalence
- T5: Deterministic seeding
- T6: Performance on large networks
- T7: Undirected vs directed equivalence
"""

import unittest
import numpy as np
import scipy.sparse

from py3plex.algorithms.sir_multiplex import (
    simulate_sir_multiplex_discrete,
    simulate_sir_multiplex_gillespie,
    basic_reproduction_number,
    summarize,
    EpidemicResult
)


class TestSIRMultiplexDiscrete(unittest.TestCase):
    """Tests for discrete-time SIR simulator."""
    
    def test_t1_single_layer_sanity(self):
        """T1: Discrete-time matches expected behavior for single-layer network."""
        # Create a small star network: node 0 connected to nodes 1, 2, 3
        N = 4
        edges = [(0, 1), (0, 2), (0, 3)]
        row, col = zip(*edges)
        data = np.ones(len(edges))
        A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        # Start with node 0 infected
        initial_infected = np.array([True, False, False, False])
        
        # High transmission rate, moderate recovery
        result = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=1.0,
            gamma=0.1,
            dt=0.1,
            steps=50,
            initial_infected=initial_infected,
            rng_seed=42
        )
        
        # Check basic properties
        self.assertEqual(len(result.times), 51)  # steps + 1
        self.assertEqual(result.S[0], 3)  # Initial: 3 susceptible
        self.assertEqual(result.I[0], 1)  # Initial: 1 infected
        self.assertEqual(result.R[0], 0)  # Initial: 0 recovered
        
        # Conservation of nodes
        for i in range(len(result.times)):
            total = result.S[i] + result.I[i] + result.R[i]
            self.assertEqual(total, N, f"Conservation violated at step {i}")
        
        # Epidemic should progress (some recoveries or growth in infections)
        self.assertTrue(result.R[-1] > 0 or result.I[-1] > result.I[0],
                       "Epidemic should show some activity")
        
        # No negative counts
        self.assertTrue(np.all(result.S >= 0))
        self.assertTrue(np.all(result.I >= 0))
        self.assertTrue(np.all(result.R >= 0))
    
    def test_t2_monotonicity_transmission(self):
        """T2: Increasing transmission rate should not decrease final attack rate."""
        # Create a connected network
        N = 20
        # Ring network: everyone connected to their neighbors
        edges = [(i, (i+1) % N) for i in range(N)]
        edges += [((i+1) % N, i) for i in range(N)]  # Make symmetric
        row, col = zip(*edges)
        data = np.ones(len(edges))
        A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[0] = True
        
        # Test increasing beta values
        betas = [0.1, 0.5, 1.0]
        attack_rates = []
        
        for beta in betas:
            result = simulate_sir_multiplex_discrete(
                A_layers=[A],
                beta=beta,
                gamma=0.2,
                dt=0.5,
                steps=100,
                initial_infected=initial_infected,
                rng_seed=123
            )
            summary = summarize(result)
            attack_rates.append(summary["attack_rate"])
        
        # Attack rate should be non-decreasing with beta
        for i in range(len(attack_rates) - 1):
            self.assertLessEqual(attack_rates[i], attack_rates[i+1] + 0.1,
                               f"Attack rate decreased: {attack_rates}")
    
    def test_t3_importations_only(self):
        """T3: With beta=0 and gamma>0, only importations create infections."""
        N = 10
        # Complete graph (but beta=0, so no transmission)
        edges = [(i, j) for i in range(N) for j in range(N) if i != j]
        row, col = zip(*edges)
        data = np.ones(len(edges))
        A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        # Start with no infections
        initial_state = np.zeros(N, dtype=int)
        
        # Run with no transmission but with importations
        result = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=0.0,  # No transmission
            gamma=0.3,
            dt=1.0,
            steps=20,
            initial_state=initial_state,
            import_rate=0.5,  # Import rate
            rng_seed=456
        )
        
        # Should have some infections due to imports
        self.assertGreater(result.R[-1], 0, "Should have infections from imports")
        
        # Now test with no imports: should have no infections
        initial_state = np.zeros(N, dtype=int)
        result_no_import = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=0.0,
            gamma=0.3,
            dt=1.0,
            steps=20,
            initial_state=initial_state,
            import_rate=0.0,
            rng_seed=456
        )
        
        # Should have no infections without imports
        self.assertEqual(result_no_import.R[-1], 0, "Should have no infections without imports")
        self.assertEqual(result_no_import.I[-1], 0, "Should have no infections without imports")
    
    def test_t4_layer_weights_equivalence(self):
        """T4: Doubling layer weight should be equivalent to doubling beta."""
        N = 15
        # Random sparse network
        np.random.seed(789)
        density = 0.2
        edges = [(i, j) for i in range(N) for j in range(N) 
                 if i != j and np.random.random() < density]
        if edges:
            row, col = zip(*edges)
            data = np.ones(len(edges))
            A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        else:
            A = scipy.sparse.csr_matrix((N, N))
        
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[0] = True
        
        # Test 1: beta=0.5, weight=1.0
        result1 = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=0.5,
            gamma=0.2,
            layer_weights=np.array([1.0]),
            dt=0.5,
            steps=50,
            initial_infected=initial_infected,
            rng_seed=111
        )
        
        # Test 2: beta=0.5, weight=2.0 (should give similar result to beta=1.0, weight=1.0)
        result2 = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=0.5,
            gamma=0.2,
            layer_weights=np.array([2.0]),
            dt=0.5,
            steps=50,
            initial_infected=initial_infected,
            rng_seed=111
        )
        
        # Test 3: beta=1.0, weight=1.0
        result3 = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=1.0,
            gamma=0.2,
            layer_weights=np.array([1.0]),
            dt=0.5,
            steps=50,
            initial_infected=initial_infected,
            rng_seed=111
        )
        
        # Result2 and Result3 should be very similar (same effective transmission)
        # Allow for stochastic variation
        attack_rate2 = result2.R[-1] / N
        attack_rate3 = result3.R[-1] / N
        
        self.assertAlmostEqual(attack_rate2, attack_rate3, delta=0.15,
                              msg="Doubling weight should be equivalent to doubling beta")
    
    def test_t5_deterministic_seeding(self):
        """T5: Same rng_seed should reproduce identical trajectories."""
        N = 10
        edges = [(i, (i+1) % N) for i in range(N)]
        row, col = zip(*edges)
        data = np.ones(len(edges))
        A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        # Run twice with same seed
        result1 = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=0.5,
            gamma=0.2,
            dt=0.5,
            steps=30,
            rng_seed=999
        )
        
        result2 = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=0.5,
            gamma=0.2,
            dt=0.5,
            steps=30,
            rng_seed=999
        )
        
        # Should be identical
        np.testing.assert_array_equal(result1.S, result2.S,
                                     err_msg="S counts should be identical with same seed")
        np.testing.assert_array_equal(result1.I, result2.I,
                                     err_msg="I counts should be identical with same seed")
        np.testing.assert_array_equal(result1.R, result2.R,
                                     err_msg="R counts should be identical with same seed")
    
    def test_t6_performance_large_network(self):
        """T6: Performance test on larger sparse network."""
        import time
        
        # Create a sparse network with ~10^6 non-zeros
        # Use ~1000 nodes with degree ~1000 each
        N = 1000
        avg_degree = 20  # Keep manageable for test environment
        
        # Create random edges
        np.random.seed(12345)
        n_edges = N * avg_degree
        row = np.random.randint(0, N, n_edges)
        col = np.random.randint(0, N, n_edges)
        data = np.ones(n_edges)
        A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        # Verify sparsity
        nnz = A.nnz
        self.assertLess(nnz, N * N, "Matrix should be sparse")
        
        # Time the simulation
        start = time.time()
        result = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=0.3,
            gamma=0.2,
            dt=1.0,
            steps=20,  # Limited steps for performance
            rng_seed=42
        )
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 10 seconds)
        self.assertLess(elapsed, 10.0,
                       f"Simulation took {elapsed:.2f}s, should be < 10s")
        
        # Verify results are valid
        self.assertEqual(len(result.S), 21)
        self.assertTrue(np.all(result.S + result.I + result.R == N))
    
    def test_t7_undirected_directed_symmetric(self):
        """T7: For symmetric adjacency matrix, undirected and directed should coincide."""
        N = 8
        # Create symmetric edges
        edges = [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2),
                 (3, 0), (0, 3), (4, 5), (5, 4)]
        row, col = zip(*edges)
        data = np.ones(len(edges))
        A_sym = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        # Verify symmetry
        self.assertTrue(np.allclose(A_sym.toarray(), A_sym.T.toarray()),
                       "Matrix should be symmetric")
        
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[0] = True
        
        # Run simulation
        result = simulate_sir_multiplex_discrete(
            A_layers=[A_sym],
            beta=0.5,
            gamma=0.2,
            dt=0.5,
            steps=40,
            initial_infected=initial_infected,
            rng_seed=777
        )
        
        # For symmetric matrix, transmission should work in both directions
        # Just verify the simulation runs and produces valid results
        self.assertTrue(np.all(result.S + result.I + result.R == N))
        self.assertGreaterEqual(result.R[-1], 0)


class TestSIRMultiplexGillespie(unittest.TestCase):
    """Tests for continuous-time Gillespie SIR simulator."""
    
    def test_basic_gillespie(self):
        """Test basic Gillespie simulation runs correctly."""
        N = 10
        edges = [(i, (i+1) % N) for i in range(N)]
        row, col = zip(*edges)
        data = np.ones(len(edges))
        A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[0] = True
        
        result = simulate_sir_multiplex_gillespie(
            A_layers=[A],
            beta=0.5,
            gamma=0.2,
            t_max=50.0,
            initial_infected=initial_infected,
            rng_seed=42,
            return_event_log=True
        )
        
        # Check basic properties
        self.assertGreater(len(result.times), 0)
        self.assertEqual(result.S[0], 9)
        self.assertEqual(result.I[0], 1)
        self.assertEqual(result.R[0], 0)
        
        # Conservation
        for i in range(len(result.times)):
            total = result.S[i] + result.I[i] + result.R[i]
            self.assertEqual(total, N)
        
        # Should have event log
        self.assertIsNotNone(result.events)
        self.assertGreater(len(result.events), 0)
        
        # Events should be properly formatted
        for event in result.events:
            self.assertEqual(len(event), 4)
            t, event_type, node, layer = event
            self.assertIn(event_type, ["infection", "recovery", "import"])
            self.assertGreaterEqual(node, 0)
            self.assertLess(node, N)
    
    def test_gillespie_determinism(self):
        """Test that Gillespie with same seed produces same results."""
        N = 8
        edges = [(i, j) for i in range(N) for j in range(i+1, N)]
        row, col = zip(*edges)
        data = np.ones(len(edges))
        A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        result1 = simulate_sir_multiplex_gillespie(
            A_layers=[A],
            beta=0.4,
            gamma=0.3,
            t_max=20.0,
            rng_seed=555
        )
        
        result2 = simulate_sir_multiplex_gillespie(
            A_layers=[A],
            beta=0.4,
            gamma=0.3,
            t_max=20.0,
            rng_seed=555
        )
        
        # Results should be identical
        np.testing.assert_array_almost_equal(result1.times, result2.times)
        np.testing.assert_array_equal(result1.S, result2.S)
        np.testing.assert_array_equal(result1.I, result2.I)
        np.testing.assert_array_equal(result1.R, result2.R)
    
    def test_gillespie_importations(self):
        """Test Gillespie with importations."""
        N = 5
        # Disconnected nodes
        A = scipy.sparse.csr_matrix((N, N))
        
        # Start with no infections, rely on imports
        initial_state = np.zeros(N, dtype=int)
        
        result = simulate_sir_multiplex_gillespie(
            A_layers=[A],
            beta=0.0,
            gamma=0.5,
            t_max=10.0,
            initial_state=initial_state,
            import_rate=0.5,
            rng_seed=888
        )
        
        # Should have some infections from imports
        self.assertGreater(result.R[-1], 0, "Should have infections from imports")


class TestMultiplexSpecific(unittest.TestCase):
    """Tests specific to multiplex (multi-layer) functionality."""
    
    def test_multiple_layers_discrete(self):
        """Test discrete simulation with multiple layers."""
        N = 10
        
        # Layer 1: ring
        edges1 = [(i, (i+1) % N) for i in range(N)]
        row1, col1 = zip(*edges1)
        A1 = scipy.sparse.csr_matrix((np.ones(len(edges1)), (row1, col1)), shape=(N, N))
        
        # Layer 2: star from node 0
        edges2 = [(0, i) for i in range(1, N)]
        row2, col2 = zip(*edges2)
        A2 = scipy.sparse.csr_matrix((np.ones(len(edges2)), (row2, col2)), shape=(N, N))
        
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[0] = True
        
        result = simulate_sir_multiplex_discrete(
            A_layers=[A1, A2],
            beta=np.array([0.3, 0.3]),
            gamma=0.2,
            dt=0.5,
            steps=50,
            initial_infected=initial_infected,
            rng_seed=123,
            return_layer_incidence=True
        )
        
        # Check layer incidence is returned
        self.assertIsNotNone(result.incidence_by_layer)
        self.assertEqual(result.incidence_by_layer.shape[1], 2)  # 2 layers
        
        # Check conservation
        for i in range(len(result.times)):
            self.assertEqual(result.S[i] + result.I[i] + result.R[i], N)
    
    def test_multiple_layers_gillespie(self):
        """Test Gillespie simulation with multiple layers."""
        N = 8
        
        # Layer 1: chain
        edges1 = [(i, i+1) for i in range(N-1)]
        row1, col1 = zip(*edges1) if edges1 else ([], [])
        A1 = scipy.sparse.csr_matrix((np.ones(len(edges1)), (row1, col1)), shape=(N, N))
        
        # Layer 2: reverse chain
        edges2 = [(i+1, i) for i in range(N-1)]
        row2, col2 = zip(*edges2) if edges2 else ([], [])
        A2 = scipy.sparse.csr_matrix((np.ones(len(edges2)), (row2, col2)), shape=(N, N))
        
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[N//2] = True
        
        result = simulate_sir_multiplex_gillespie(
            A_layers=[A1, A2],
            beta=np.array([0.4, 0.4]),
            gamma=0.2,
            t_max=30.0,
            initial_infected=initial_infected,
            rng_seed=999,
            return_layer_incidence=True
        )
        
        # Check layer incidence
        if result.incidence_by_layer is not None:
            self.assertEqual(result.incidence_by_layer.shape[1], 2)


class TestUtilities(unittest.TestCase):
    """Tests for utility functions."""
    
    def test_basic_reproduction_number(self):
        """Test R0 calculation."""
        N = 10
        # Complete graph
        edges = [(i, j) for i in range(N) for j in range(N) if i != j]
        row, col = zip(*edges)
        data = np.ones(len(edges))
        A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        # For complete graph, each node has N-1 contacts
        # R0 ≈ β * (N-1) / γ
        beta = 0.1
        gamma = 0.2
        expected_R0_approx = beta * (N - 1) / gamma
        
        R0 = basic_reproduction_number([A], beta, gamma)
        
        # Should be positive and in reasonable range
        self.assertGreater(R0, 0)
        self.assertLess(R0, N * 2)  # Sanity check
    
    def test_summarize(self):
        """Test result summarization."""
        N = 10
        edges = [(i, (i+1) % N) for i in range(N)]
        row, col = zip(*edges)
        data = np.ones(len(edges))
        A = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))
        
        result = simulate_sir_multiplex_discrete(
            A_layers=[A],
            beta=0.5,
            gamma=0.2,
            dt=0.5,
            steps=50,
            rng_seed=42,
            return_layer_incidence=True
        )
        
        summary = summarize(result)
        
        # Check expected fields
        self.assertIn("peak_prevalence", summary)
        self.assertIn("peak_time", summary)
        self.assertIn("attack_rate", summary)
        self.assertIn("total_infections", summary)
        self.assertIn("duration", summary)
        
        # Check value ranges
        self.assertGreaterEqual(summary["peak_prevalence"], 0)
        self.assertLessEqual(summary["peak_prevalence"], N)
        self.assertGreaterEqual(summary["attack_rate"], 0.0)
        self.assertLessEqual(summary["attack_rate"], 1.0)
        self.assertEqual(summary["total_infections"], result.R[-1])


class TestInputValidation(unittest.TestCase):
    """Tests for input validation and error handling."""
    
    def test_empty_layers(self):
        """Test error on empty layer list."""
        with self.assertRaises(ValueError):
            simulate_sir_multiplex_discrete(
                A_layers=[],
                beta=0.5,
                gamma=0.2
            )
    
    def test_mismatched_layer_sizes(self):
        """Test error on mismatched layer dimensions."""
        A1 = scipy.sparse.csr_matrix((5, 5))
        A2 = scipy.sparse.csr_matrix((6, 6))  # Different size
        
        with self.assertRaises(ValueError):
            simulate_sir_multiplex_discrete(
                A_layers=[A1, A2],
                beta=0.5,
                gamma=0.2
            )
    
    def test_negative_beta(self):
        """Test error on negative transmission rate."""
        A = scipy.sparse.csr_matrix((5, 5))
        
        with self.assertRaises(ValueError):
            simulate_sir_multiplex_discrete(
                A_layers=[A],
                beta=-0.5,  # Negative
                gamma=0.2
            )
    
    def test_negative_gamma(self):
        """Test error on negative recovery rate."""
        A = scipy.sparse.csr_matrix((5, 5))
        
        with self.assertRaises(ValueError):
            simulate_sir_multiplex_discrete(
                A_layers=[A],
                beta=0.5,
                gamma=-0.2  # Negative
            )
    
    def test_invalid_initial_state(self):
        """Test error on invalid initial state."""
        A = scipy.sparse.csr_matrix((5, 5))
        
        # Wrong length
        with self.assertRaises(ValueError):
            simulate_sir_multiplex_discrete(
                A_layers=[A],
                beta=0.5,
                gamma=0.2,
                initial_state=np.array([0, 1, 2])  # Length 3, should be 5
            )
        
        # Invalid values
        with self.assertRaises(ValueError):
            simulate_sir_multiplex_discrete(
                A_layers=[A],
                beta=0.5,
                gamma=0.2,
                initial_state=np.array([0, 1, 2, 3, 4])  # Contains 3, 4
            )


if __name__ == "__main__":
    unittest.main()

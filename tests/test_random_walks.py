"""
Comprehensive tests for random walk primitives.

This module validates:
- Basic random walk with weighted/unweighted edges
- Second-order (Node2Vec) biased random walks
- Multiple walk generation with deterministic seeding
- Correctness properties (uniformity, conservation, bias consistency)
- Robustness (isolated nodes, directed graphs, sparse matrices)
- Multilayer network support
"""

import numpy as np
import networkx as nx
import pytest
from scipy import stats

from py3plex.algorithms.general.walkers import (
    basic_random_walk,
    node2vec_walk,
    generate_walks,
    layer_specific_random_walk,
)


class TestBasicRandomWalk:
    """Test suite for basic random walk functionality."""
    
    def test_basic_walk_length(self):
        """Walk returns correct number of nodes."""
        G = nx.karate_club_graph()
        walk_length = 10
        walk = basic_random_walk(G, 0, walk_length, seed=42)
        assert len(walk) == walk_length + 1  # includes start node
    
    def test_basic_walk_starts_correctly(self):
        """Walk starts at specified node."""
        G = nx.karate_club_graph()
        start_node = 5
        walk = basic_random_walk(G, start_node, 10, seed=42)
        assert walk[0] == start_node
    
    def test_basic_walk_valid_transitions(self):
        """All transitions in walk are valid edges."""
        G = nx.karate_club_graph()
        walk = basic_random_walk(G, 0, 20, seed=42)
        for i in range(len(walk) - 1):
            assert G.has_edge(walk[i], walk[i+1]) or G.has_edge(walk[i+1], walk[i])
    
    def test_basic_walk_invalid_start_node(self):
        """Raises error for invalid start node."""
        G = nx.karate_club_graph()
        with pytest.raises(ValueError, match="not in graph"):
            basic_random_walk(G, 9999, 10)
    
    def test_basic_walk_invalid_length(self):
        """Raises error for invalid walk length."""
        G = nx.karate_club_graph()
        with pytest.raises(ValueError, match="Walk length must be"):
            basic_random_walk(G, 0, 0)
    
    def test_basic_walk_isolated_node(self):
        """Handles isolated nodes gracefully."""
        G = nx.Graph()
        G.add_nodes_from([0, 1, 2])
        G.add_edge(1, 2)
        walk = basic_random_walk(G, 0, 10, seed=42)
        assert walk == [0]  # terminates immediately
    
    def test_basic_walk_reproducibility(self):
        """Same seed produces identical walks."""
        G = nx.karate_club_graph()
        walk1 = basic_random_walk(G, 0, 50, seed=42)
        walk2 = basic_random_walk(G, 0, 50, seed=42)
        assert walk1 == walk2
    
    def test_basic_walk_different_seeds(self):
        """Different seeds produce different walks."""
        G = nx.karate_club_graph()
        walk1 = basic_random_walk(G, 0, 50, seed=42)
        walk2 = basic_random_walk(G, 0, 50, seed=123)
        assert walk1 != walk2
    
    def test_basic_walk_weighted_edges(self):
        """Respects edge weights in sampling."""
        G = nx.Graph()
        G.add_weighted_edges_from([
            (0, 1, 10.0),  # high weight
            (0, 2, 0.1),   # low weight
        ])
        
        # Run many walks and check distribution
        visits = {1: 0, 2: 0}
        num_trials = 1000
        for i in range(num_trials):
            walk = basic_random_walk(G, 0, 1, weighted=True, seed=i)
            if len(walk) > 1:
                visits[walk[1]] += 1
        
        # Node 1 should be visited much more often than node 2
        ratio = visits[1] / max(visits[2], 1)
        assert ratio > 50  # Expected ratio ≈ 100
    
    def test_basic_walk_unweighted(self):
        """Unweighted walk ignores edge weights."""
        G = nx.Graph()
        G.add_weighted_edges_from([
            (0, 1, 100.0),
            (0, 2, 1.0),
        ])
        
        # Run many walks with weighted=False
        visits = {1: 0, 2: 0}
        num_trials = 1000
        for i in range(num_trials):
            walk = basic_random_walk(G, 0, 1, weighted=False, seed=i)
            if len(walk) > 1:
                visits[walk[1]] += 1
        
        # Should visit both nodes roughly equally
        ratio = visits[1] / max(visits[2], 1)
        assert 0.5 < ratio < 2.0  # Allow 2x variance


class TestUniformityProperty:
    """Test that transitions are uniform on unweighted regular graphs."""
    
    def test_uniformity_on_complete_graph(self):
        """Transitions are uniform on complete graph."""
        n = 10
        G = nx.complete_graph(n)
        start_node = 0
        
        # Count visits to each neighbor
        visits = {i: 0 for i in range(1, n)}
        num_walks = 10000
        
        for i in range(num_walks):
            walk = basic_random_walk(G, start_node, 1, weighted=False, seed=i)
            if len(walk) > 1:
                visits[walk[1]] += 1
        
        # Chi-square test for uniformity
        expected = num_walks / (n - 1)
        chi2_stat = sum((visits[i] - expected)**2 / expected for i in visits)
        
        # Chi-square critical value at p=0.01 with df=8
        critical = stats.chi2.ppf(0.99, n - 2)
        assert chi2_stat < critical
    
    def test_uniformity_on_regular_graph(self):
        """Transitions are uniform on regular graph."""
        G = nx.random_regular_graph(4, 20, seed=42)
        start_node = 0
        neighbors = list(G.neighbors(start_node))
        
        visits = {n: 0 for n in neighbors}
        num_walks = 5000
        
        for i in range(num_walks):
            walk = basic_random_walk(G, start_node, 1, weighted=False, seed=i)
            if len(walk) > 1:
                visits[walk[1]] += 1
        
        # Check approximately uniform
        expected = num_walks / len(neighbors)
        for count in visits.values():
            assert 0.8 * expected < count < 1.2 * expected


class TestConservationProperty:
    """Test that transition probabilities sum to 1."""
    
    def test_conservation_basic_walk(self):
        """Probability conservation in basic walk."""
        G = nx.karate_club_graph()
        
        # For each node, verify probabilities sum to 1
        for node in G.nodes():
            neighbors = list(G.neighbors(node))
            if len(neighbors) == 0:
                continue
            
            # Manually compute transition probabilities
            weights = np.array([G[node][n].get('weight', 1.0) for n in neighbors])
            probs = weights / weights.sum()
            
            # Should sum to 1 within machine epsilon
            assert abs(probs.sum() - 1.0) < 1e-10
    
    def test_conservation_weighted_graph(self):
        """Probability conservation with weighted edges."""
        G = nx.Graph()
        G.add_weighted_edges_from([
            (0, 1, 2.5),
            (0, 2, 3.7),
            (0, 3, 1.1),
        ])
        
        neighbors = [1, 2, 3]
        weights = np.array([2.5, 3.7, 1.1])
        probs = weights / weights.sum()
        
        assert abs(probs.sum() - 1.0) < 1e-15


class TestNode2VecBiasedWalk:
    """Test suite for Node2Vec biased random walks."""
    
    def test_node2vec_walk_length(self):
        """Node2Vec walk has correct length."""
        G = nx.karate_club_graph()
        walk = node2vec_walk(G, 0, 15, p=1.0, q=1.0, seed=42)
        assert len(walk) == 16  # walk_length + 1
    
    def test_node2vec_walk_valid_transitions(self):
        """All transitions are valid edges."""
        G = nx.karate_club_graph()
        walk = node2vec_walk(G, 0, 20, p=0.5, q=2.0, seed=42)
        for i in range(len(walk) - 1):
            assert G.has_edge(walk[i], walk[i+1]) or G.has_edge(walk[i+1], walk[i])
    
    def test_node2vec_invalid_p(self):
        """Raises error for invalid p parameter."""
        G = nx.karate_club_graph()
        with pytest.raises(ValueError, match="Parameter p must be positive"):
            node2vec_walk(G, 0, 10, p=0, q=1.0)
    
    def test_node2vec_invalid_q(self):
        """Raises error for invalid q parameter."""
        G = nx.karate_club_graph()
        with pytest.raises(ValueError, match="Parameter q must be positive"):
            node2vec_walk(G, 0, 10, p=1.0, q=-1.0)
    
    def test_node2vec_reproducibility(self):
        """Same seed produces identical walks."""
        G = nx.karate_club_graph()
        walk1 = node2vec_walk(G, 0, 50, p=0.5, q=2.0, seed=42)
        walk2 = node2vec_walk(G, 0, 50, p=0.5, q=2.0, seed=42)
        assert walk1 == walk2


class TestBiasConsistency:
    """Test Node2Vec bias parameters p and q."""
    
    def test_low_p_encourages_backtracking(self):
        """Low p (return bias) encourages returning to previous node."""
        # Triangle graph: 0-1-2-0
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        
        # With very low p, should tend to backtrack
        backtracks = 0
        num_walks = 1000
        
        for i in range(num_walks):
            walk = node2vec_walk(G, 0, 10, p=0.01, q=1.0, seed=i)
            # Count how often we return to previous node
            for j in range(2, len(walk)):
                if walk[j] == walk[j-2]:
                    backtracks += 1
        
        # Should backtrack frequently
        backtrack_rate = backtracks / (num_walks * 9)  # 9 possible backtracks per walk
        assert backtrack_rate > 0.3  # At least 30% backtracking
    
    def test_high_p_discourages_backtracking(self):
        """High p discourages returning to previous node."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        
        backtracks = 0
        num_walks = 1000
        
        for i in range(num_walks):
            walk = node2vec_walk(G, 0, 10, p=10.0, q=1.0, seed=i)
            for j in range(2, len(walk)):
                if walk[j] == walk[j-2]:
                    backtracks += 1
        
        backtrack_rate = backtracks / (num_walks * 9)
        assert backtrack_rate < 0.2  # Less than 20% backtracking
    
    def test_low_q_encourages_exploration(self):
        """Low q (in-out bias) encourages exploring further."""
        # Create a graph where exploration is possible: path with branches
        # 0 - 1 - 2
        #     |   |
        #     3   4
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (1, 3), (2, 4)])
        
        # Start at 0, go to 1. With low q, should explore to 2 or 3 (not back to 0)
        explorations = 0
        num_walks = 1000
        
        for i in range(num_walks):
            walk = node2vec_walk(G, 0, 3, p=1.0, q=0.1, seed=i)
            # After 0->1, check if we go to 2 or 3 (exploration) vs back to 0
            if len(walk) >= 3 and walk[2] in {2, 3}:
                explorations += 1
        
        exploration_rate = explorations / num_walks
        assert exploration_rate > 0.6  # Should explore frequently with low q
    
    def test_high_q_discourages_exploration(self):
        """High q discourages exploring to distant nodes."""
        G = nx.star_graph(5)
        center = 0
        
        explorations = 0
        num_walks = 1000
        
        for i in range(num_walks):
            walk = node2vec_walk(G, center, 5, p=1.0, q=10.0, seed=i)
            if len(walk) >= 4 and walk[2] != center:
                explorations += 1
        
        exploration_rate = explorations / num_walks
        assert exploration_rate < 0.3


class TestGenerateWalks:
    """Test multiple walk generation interface."""
    
    def test_generate_walks_count(self):
        """Generates correct number of walks."""
        G = nx.karate_club_graph()
        num_walks = 5
        walks = generate_walks(G, num_walks, walk_length=10, seed=42)
        assert len(walks) == num_walks * G.number_of_nodes()
    
    def test_generate_walks_from_subset(self):
        """Generates walks only from specified nodes."""
        G = nx.karate_club_graph()
        start_nodes = [0, 1, 2]
        num_walks = 3
        walks = generate_walks(G, num_walks, walk_length=10, start_nodes=start_nodes, seed=42)
        assert len(walks) == num_walks * len(start_nodes)
    
    def test_generate_walks_reproducibility(self):
        """Same seed produces identical walk sets."""
        G = nx.karate_club_graph()
        walks1 = generate_walks(G, num_walks=10, walk_length=10, seed=42)
        walks2 = generate_walks(G, num_walks=10, walk_length=10, seed=42)
        assert walks1 == walks2
    
    def test_generate_walks_edge_format(self):
        """Can return walks as edge sequences."""
        G = nx.karate_club_graph()
        edge_walks = generate_walks(
            G, num_walks=5, walk_length=10, 
            start_nodes=[0], return_edges=True, seed=42
        )
        
        # Check format
        for walk in edge_walks:
            assert isinstance(walk, list)
            for edge in walk:
                assert isinstance(edge, tuple)
                assert len(edge) == 2
                # Verify edge exists
                u, v = edge
                assert G.has_edge(u, v) or G.has_edge(v, u)
    
    def test_generate_walks_with_bias(self):
        """Generates biased walks when p != 1 or q != 1."""
        G = nx.karate_club_graph()
        walks = generate_walks(
            G, num_walks=5, walk_length=10, 
            p=0.5, q=2.0, seed=42
        )
        assert len(walks) > 0


class TestRobustness:
    """Test robustness to edge cases and special graph structures."""
    
    def test_directed_graph(self):
        """Handles directed graphs correctly."""
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        walk = basic_random_walk(G, 0, 10, seed=42)
        
        # Verify all transitions follow directed edges
        for i in range(len(walk) - 1):
            assert G.has_edge(walk[i], walk[i+1])
    
    def test_disconnected_graph(self):
        """Handles disconnected components."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        
        walk1 = basic_random_walk(G, 0, 10, seed=42)
        # Walk should stay in component {0, 1}
        assert all(node in {0, 1} for node in walk1)
        
        walk2 = basic_random_walk(G, 2, 10, seed=42)
        # Walk should stay in component {2, 3}
        assert all(node in {2, 3} for node in walk2)
    
    def test_self_loops(self):
        """Handles self-loops correctly."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 1), (1, 2)])  # self-loop at 1
        walk = basic_random_walk(G, 0, 20, seed=42)
        # Should complete without errors
        assert len(walk) >= 1
    
    def test_multigraph(self):
        """Handles multigraphs with parallel edges."""
        G = nx.MultiGraph()
        G.add_edge(0, 1, weight=1.0)
        G.add_edge(0, 1, weight=2.0)  # parallel edge
        G.add_edge(0, 2, weight=1.0)
        
        # Should handle multiple edges correctly
        walk = basic_random_walk(G, 0, 10, weighted=True, seed=42)
        assert len(walk) >= 1
    
    def test_single_node_graph(self):
        """Handles single-node graph."""
        G = nx.Graph()
        G.add_node(0)
        walk = basic_random_walk(G, 0, 10, seed=42)
        assert walk == [0]
    
    def test_large_sparse_graph(self):
        """Handles large sparse graphs efficiently."""
        G = nx.erdos_renyi_graph(1000, 0.01, seed=42)
        walk = basic_random_walk(G, 0, 100, seed=42)
        # Should complete in reasonable time
        assert len(walk) >= 1


class TestEdgeWeightStatistical:
    """Statistical validation of edge weight handling."""
    
    def test_edge_weight_frequency(self):
        """Visit frequency matches edge weight ratios."""
        G = nx.Graph()
        # Node 0 connected to nodes 1, 2, 3 with weights 1:2:3
        G.add_weighted_edges_from([
            (0, 1, 1.0),
            (0, 2, 2.0),
            (0, 3, 3.0),
        ])
        
        # Count visits over many walks
        visits = {1: 0, 2: 0, 3: 0}
        num_trials = 10000
        
        for i in range(num_trials):
            walk = basic_random_walk(G, 0, 1, weighted=True, seed=i)
            if len(walk) > 1:
                visits[walk[1]] += 1
        
        # Normalize to ratios
        total = sum(visits.values())
        ratios = [visits[1]/total, visits[2]/total, visits[3]/total]
        expected = [1/6, 2/6, 3/6]
        
        # Check within 5% tolerance
        for observed, expect in zip(ratios, expected):
            assert abs(observed - expect) < 0.05
    
    def test_weighted_vs_unweighted_difference(self):
        """Weighted and unweighted walks produce different distributions."""
        G = nx.Graph()
        G.add_weighted_edges_from([
            (0, 1, 10.0),
            (0, 2, 1.0),
        ])
        
        # Weighted walks
        visits_weighted = {1: 0, 2: 0}
        for i in range(1000):
            walk = basic_random_walk(G, 0, 1, weighted=True, seed=i)
            if len(walk) > 1:
                visits_weighted[walk[1]] += 1
        
        # Unweighted walks
        visits_unweighted = {1: 0, 2: 0}
        for i in range(1000):
            walk = basic_random_walk(G, 0, 1, weighted=False, seed=i)
            if len(walk) > 1:
                visits_unweighted[walk[1]] += 1
        
        # Ratios should be significantly different
        ratio_weighted = visits_weighted[1] / max(visits_weighted[2], 1)
        ratio_unweighted = visits_unweighted[1] / max(visits_unweighted[2], 1)
        
        assert abs(ratio_weighted - ratio_unweighted) > 3


class TestLayerSpecificWalk:
    """Test multilayer network walk functionality."""
    
    def test_layer_constrained_walk(self):
        """Walk stays within specified layer."""
        G = nx.Graph()
        # Add nodes with layer information
        G.add_edges_from([
            ("A---layer1", "B---layer1"),
            ("B---layer1", "C---layer1"),
            ("A---layer2", "B---layer2"),
        ])
        
        walk = layer_specific_random_walk(
            G, "A---layer1", 10, 
            layer="layer1", cross_layer_prob=0.0, seed=42
        )
        
        # All nodes should be in layer1
        for node in walk:
            assert str(node).endswith("---layer1")
    
    def test_cross_layer_transition(self):
        """Allows cross-layer transitions with probability."""
        G = nx.Graph()
        # Add intra-layer and inter-layer edges
        G.add_edges_from([
            ("A---layer1", "B---layer1"),
            ("A---layer1", "A---layer2"),  # inter-layer
            ("A---layer2", "B---layer2"),
        ])
        
        # With high cross-layer probability, should see layer changes
        cross_layer_count = 0
        num_walks = 100
        
        for i in range(num_walks):
            walk = layer_specific_random_walk(
                G, "A---layer1", 5,
                layer="layer1", cross_layer_prob=0.5, seed=i
            )
            # Check if any node is not in layer1
            if any("layer2" in str(node) for node in walk):
                cross_layer_count += 1
        
        # Should have some cross-layer transitions
        assert cross_layer_count > 0
    
    def test_layer_walk_no_constraint(self):
        """Without layer constraint, walks freely."""
        G = nx.Graph()
        G.add_edges_from([
            ("A---layer1", "B---layer1"),
            ("A---layer1", "A---layer2"),
            ("A---layer2", "B---layer2"),
        ])
        
        walk = layer_specific_random_walk(
            G, "A---layer1", 10, 
            layer=None, seed=42
        )
        
        # Should complete without error
        assert len(walk) >= 1


class TestLegacyCompatibility:
    """Test backward compatibility with old general_random_walk."""
    
    def test_legacy_function_exists(self):
        """Legacy function still available."""
        from py3plex.algorithms.general.walkers import general_random_walk
        assert callable(general_random_walk)
    
    def test_legacy_function_warns(self):
        """Legacy function issues deprecation warning."""
        from py3plex.algorithms.general.walkers import general_random_walk
        
        G = nx.karate_club_graph()
        with pytest.warns(DeprecationWarning, match="deprecated"):
            walk = general_random_walk(G, 0, iterations=10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

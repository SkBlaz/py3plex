# New Property-Based Tests Added

This document describes the property-based tests added to expand test coverage for py3plex multilayer networks.

## Summary

**Latest additions:** 26 new property-based tests for centrality metrics across 2 modules:
- 16 tests for centrality invariants
- 10 tests for centrality rankings

**Previously added:** 40 property-based tests across 4 modules:
- 9 tests for edge operations
- 10 tests for node operations  
- 10 tests for weight operations
- 11 tests for graph transformations

**Total property-based tests: 151+** (increased from 125+)

## Latest Test Modules (Centrality Coverage)

### 1. `test_centrality_invariants.py` (16 tests)

Tests fundamental mathematical properties and invariants for multilayer centrality metrics.

**Tests:**
1. `test_degree_centrality_non_negative` - Degree centrality values are always ≥ 0
2. `test_centrality_values_finite` - All centrality values are finite (no NaN/inf)
3. `test_participation_coefficient_bounded` - Participation coefficient in [0, 1]
4. `test_closeness_centrality_non_negative` - Closeness centrality is non-negative
5. `test_betweenness_centrality_non_negative` - Betweenness centrality is non-negative
6. `test_eigenvector_centrality_normalization` - L2 normalization produces unit norm
7. `test_lp_aggregated_centrality_properties` - Lp-aggregated centrality is valid
8. `test_degree_invariant_under_relabeling` - Degree multiset preserved under isomorphism
9. `test_betweenness_ranking_invariant` - Betweenness ranking preserved under relabeling
10. `test_layer_degree_sum_equals_overlapping` - Layer degrees sum to overlapping degree
11. `test_weighted_degree_greater_equal_unweighted` - Weighted ≥ unweighted (weights ≥ 1)
12. `test_information_centrality_properties` - Information centrality is valid
13. `test_collective_influence_properties` - Collective influence is non-negative
14. `test_harmonic_closeness_properties` - Harmonic closeness is non-negative
15. `test_compute_all_centralities_basic` - compute_all_centralities returns valid results
16. `test_compute_all_centralities_extended` - Extended mode includes more metrics

**Key Properties:**
- Non-negativity and finiteness
- Normalization correctness
- Isomorphism invariance
- Consistency across operations

### 2. `test_centrality_rankings.py` (10 tests)

Tests ranking stability, monotonicity, and scale invariance of centrality metrics.

**Tests:**
1. `test_star_network_hub_highest_degree` - Hub node has highest degree in star networks
2. `test_star_network_hub_highest_betweenness` - Hub has highest betweenness
3. `test_path_network_endpoints_lowest_centrality` - Endpoints have lower centrality
4. `test_normalized_centrality_scale_invariant` - Rankings invariant to weight scaling
5. `test_weighted_degree_scales_linearly` - Weighted degree scales linearly
6. `test_adding_edges_increases_total_degree` - Monotonicity property
7. `test_more_layers_increases_overlapping_degree` - More layers = higher overlap
8. `test_degree_ranking_stability` - Rankings stable across computations
9. `test_centrality_consistent_node_set` - All measures return same node set
10. `test_uniform_distribution_increases_participation` - Uniform edges increase participation

**Key Properties:**
- Network topology effects
- Scale invariance
- Monotonicity
- Ranking stability

## Previous Test Modules

### 3. `test_edge_operations_properties.py` (9 tests)

Tests fundamental invariants for edge manipulation in multilayer networks.

**Tests:**
1. `test_edge_addition_increases_edge_count` - Adding edges increases total count
2. `test_edge_removal_decreases_edge_count` - Removing edges decreases count
3. `test_edge_endpoints_are_nodes` - All edge endpoints must be valid nodes
4. `test_edge_weights_non_negative` - Default edge weights are non-negative
5. `test_edge_weight_preservation` - Explicitly set weights are preserved
6. `test_undirected_edge_symmetry` - Undirected networks have symmetric edges
7. `test_inter_layer_edge_validity` - Inter-layer edges connect different layers
8. `test_edge_addition_idempotence` - Adding same edges multiple times is idempotent
9. `test_edge_list_consistency` - Edge retrieval is consistent across calls

**Key Properties:**
- Monotonicity of edge counts
- Endpoint validity
- Weight preservation
- Symmetry in undirected graphs

### 4. `test_node_operations_properties.py` (10 tests)

Tests fundamental invariants for node manipulation in multilayer networks.

**Tests:**
1. `test_node_addition_increases_node_count` - Adding nodes increases total count
2. `test_node_uniqueness_within_layer` - Nodes within a layer are unique
3. `test_node_removal_consistency` - Removing nodes removes incident edges
4. `test_node_layer_assignment` - Nodes are correctly associated with layers
5. `test_same_node_different_layers` - Same node ID can exist in multiple layers
6. `test_node_count_non_negative` - Node count is always non-negative
7. `test_isolated_nodes_preserved` - Nodes without edges are preserved
8. `test_node_retrieval_consistency` - Node retrieval is consistent across calls
9. `test_node_degree_non_negative` - Node degree is always non-negative
10. `test_node_neighborhood_consistency` - Neighborhoods match edges

**Key Properties:**
- Monotonicity of node counts
- Layer-node relationships
- Degree constraints
- Consistency of graph structure

### 5. `test_weight_operations_properties.py` (10 tests)

Tests numerical properties of edge weights.

**Tests:**
1. `test_weight_assignment_preserved` - Assigned weights are preserved
2. `test_weight_scaling_linearity` - Scaling preserves weight ratios
3. `test_weight_sum_non_negative` - Sum of positive weights is positive
4. `test_weight_addition_commutative` - Weight addition is commutative
5. `test_weight_mean_bounds` - Mean weight bounded by min and max
6. `test_weight_comparison_transitivity` - Weight comparison is transitive
7. `test_uniform_weights_constant_mean` - Uniform weights have mean equal to value
8. `test_weight_variance_non_negative` - Variance is always non-negative
9. `test_weight_multiplication_identity` - Multiplying by 1 preserves weights
10. `test_weight_ordering_preserved` - Ordering of weights is preserved

**Key Properties:**
- Numerical stability
- Algebraic properties (commutativity, linearity)
- Statistical bounds
- Ordering preservation

### 6. `test_graph_transformation_properties.py` (11 tests)

Tests structural invariants under graph transformations.

**Tests:**
1. `test_complement_graph_edge_sum` - Graph + complement = complete graph
2. `test_subgraph_preserves_edges` - Subgraph edges are subset of original
3. `test_connected_components_partition` - Components partition node set
4. `test_layer_union_preserves_nodes` - Union preserves node set
5. `test_edge_reversal_preserves_connectivity` - Reversal preserves connectivity
6. `test_layer_intersection_subset` - Intersection is subset of each layer
7. `test_spanning_tree_connected` - Spanning tree is connected
8. `test_degree_sequence_sum_even` - Handshaking Lemma (sum = 2|E|)
9. `test_graph_union_commutative` - Union is commutative
10. `test_empty_layer_removal_idempotent` - Empty layer removal is idempotent
11. `test_bipartite_projection_preserves_nodes` - Projection preserves nodes

**Key Properties:**
- Graph complement properties
- Subgraph relationships
- Component structure
- Classical graph theorems (Handshaking Lemma)

## Running the Tests

### Run all new tests:
```bash
pytest tests/property/test_edge_operations_properties.py \
       tests/property/test_node_operations_properties.py \
       tests/property/test_weight_operations_properties.py \
       tests/property/test_graph_transformation_properties.py \
       -v
```

### Run all property tests:
```bash
pytest tests/property/ -v
```

### Run specific test category:
```bash
pytest tests/property/test_edge_operations_properties.py -v
```

## Test Framework

All tests use:
- **Hypothesis** for property-based testing
- **pytest** as the test runner
- **NetworkX** for graph operations
- **py3plex** multilayer network library

## Test Settings

- `deadline=None` - No time limit for slow convergence
- `max_examples=30-50` - Balance between thoroughness and speed
- `@pytest.mark.property` - Tagged for easy filtering

## Coverage

These tests expand coverage in:
- **Edge operations**: Basic graph manipulation
- **Node operations**: Node lifecycle and relationships
- **Weight operations**: Numerical properties
- **Graph transformations**: Structural invariants

## Mathematical Properties Verified

1. **Handshaking Lemma**: Σ deg(v) = 2|E|
2. **Subset relations**: Subgraph ⊆ Graph
3. **Partition property**: Components partition nodes
4. **Non-negativity**: Counts, weights ≥ 0
5. **Idempotence**: f(f(x)) = f(x) for certain operations
6. **Commutativity**: a + b = b + a for addition
7. **Linearity**: k(a + b) = ka + kb for scaling
8. **Transitivity**: a < b ∧ b < c ⟹ a < c

## Dependencies

- Python 3.8+
- pytest >= 7.0
- hypothesis >= 6.0
- networkx >= 2.5
- numpy >= 1.19.0
- scipy >= 1.5.0

## Contributing

When adding new tests:
1. Follow the existing pattern
2. Use meaningful test names
3. Document the property being tested
4. Add proper assumptions with `assume()`
5. Use appropriate settings for test count/timeout

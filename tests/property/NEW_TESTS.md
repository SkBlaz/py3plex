# New Property-Based Tests Added

This document describes the 40 new property-based tests added to expand test coverage for py3plex multilayer networks.

## Summary

Added **40 new property-based tests** across 4 new test modules:
- 9 tests for edge operations
- 10 tests for node operations  
- 10 tests for weight operations
- 11 tests for graph transformations

Total property-based tests: **125+** (increased from 85)

## New Test Modules

### 1. `test_edge_operations_properties.py`

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

### 2. `test_node_operations_properties.py`

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

### 3. `test_weight_operations_properties.py`

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

### 4. `test_graph_transformation_properties.py`

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

#!/usr/bin/env python3
"""
Property-based tests for DSL pattern matching module.

Tests invariants for:
- Pattern node and edge construction
- Pattern matching execution
- Pattern compilation and validation
"""

import pytest
from hypothesis import given, settings, assume, strategies as st

# Import DSL pattern matching module
try:
    from py3plex.dsl.patterns import (
        PatternNode,
        PatternEdge,
        PatternGraph,
        match_pattern,
        compile_pattern,
        PatternQueryBuilder,
    )
    from py3plex.core import multinet
    PATTERNS_AVAILABLE = True
except ImportError:
    PATTERNS_AVAILABLE = False
    pytest.skip("DSL patterns module not available", allow_module_level=True)


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_network(num_nodes=5, num_layers=2, seed=None):
    """Create a simple test multilayer network."""
    import numpy as np
    if seed is not None:
        np.random.seed(seed)
    
    network = multinet.multi_layer_network(directed=False)
    
    layers = [f'layer{i}' for i in range(num_layers)]
    node_names = [chr(ord('A') + i) for i in range(num_nodes)]
    
    # Add nodes
    nodes = []
    for name in node_names:
        for layer in layers:
            nodes.append({'source': name, 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges within layers
    edges = []
    for layer in layers:
        for i in range(len(node_names) - 1):
            edges.append({
                'source': node_names[i],
                'target': node_names[i + 1],
                'source_type': layer,
                'target_type': layer,
            })
    network.add_edges(edges)
    
    return network


# ============================================================================
# Property Tests: Pattern Node Construction
# ============================================================================

@pytest.mark.property
@given(
    var_name=st.text(
        min_size=1,
        max_size=15,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    )
)
def test_pattern_node_creation(var_name):
    """
    Property: PatternNode can be created with any valid variable name.
    
    Pattern nodes should accept any string as a variable name.
    """
    node = PatternNode(var=var_name)
    
    assert node.var == var_name
    assert isinstance(node.var, str)


@pytest.mark.property
@given(
    var_name=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    layer=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_pattern_node_with_layer_constraint(var_name, layer):
    """
    Property: PatternNode preserves layer constraints.
    
    A pattern node with a layer constraint should store it correctly.
    """
    from py3plex.dsl.patterns import LayerConstraint
    constraint = LayerConstraint.one(layer)
    node = PatternNode(var=var_name, layer_constraint=constraint)
    
    assert node.var == var_name
    assert node.layer_constraint is not None
    assert node.layer_constraint.kind == "one"
    assert node.layer_constraint.value == layer


# ============================================================================
# Property Tests: Pattern Edge Construction
# ============================================================================

@pytest.mark.property
@given(
    src_var=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    dst_var=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_pattern_edge_creation(src_var, dst_var):
    """
    Property: PatternEdge can be created with source and destination variables.
    
    Pattern edges should connect two pattern nodes.
    """
    assume(src_var != dst_var)  # Ensure distinct variables
    
    edge = PatternEdge(src=src_var, dst=dst_var)
    
    assert edge.src == src_var
    assert edge.dst == dst_var


@pytest.mark.property
@given(
    src_var=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    dst_var=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    directed=st.booleans()
)
def test_pattern_edge_directionality(src_var, dst_var, directed):
    """
    Property: PatternEdge preserves directionality flag.
    
    Pattern edges should correctly store whether they are directed.
    """
    assume(src_var != dst_var)
    
    edge = PatternEdge(src=src_var, dst=dst_var, directed=directed)
    
    assert edge.directed == directed


# ============================================================================
# Property Tests: Pattern Graph Construction
# ============================================================================

@pytest.mark.property
@given(
    num_nodes=st.integers(min_value=1, max_value=5)
)
def test_pattern_graph_node_count(num_nodes):
    """
    Property: PatternGraph preserves node count.
    
    A pattern graph with N nodes should maintain that count.
    """
    nodes = [PatternNode(var=f'n{i}') for i in range(num_nodes)]
    graph = PatternGraph(nodes=nodes, edges=[])
    
    assert len(graph.nodes) == num_nodes


@pytest.mark.property
@given(
    num_edges=st.integers(min_value=0, max_value=5)
)
def test_pattern_graph_edge_count(num_edges):
    """
    Property: PatternGraph preserves edge count.
    
    A pattern graph with M edges should maintain that count.
    """
    # Create enough nodes for the edges
    nodes = [PatternNode(var=f'n{i}') for i in range(num_edges + 1)]
    edges = [PatternEdge(src=f'n{i}', dst=f'n{i+1}') for i in range(num_edges)]
    
    graph = PatternGraph(nodes=nodes, edges=edges)
    
    assert len(graph.edges) == num_edges


# ============================================================================
# Property Tests: Pattern Query Builder
# ============================================================================

@pytest.mark.property
@given(
    var_name=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_pattern_query_builder_node_creation(var_name):
    """
    Property: PatternQueryBuilder can create pattern nodes.
    
    The builder should allow node creation with variable names.
    """
    builder = PatternQueryBuilder()
    node_builder = builder.node(var_name)
    
    # Should return a node builder
    assert node_builder is not None


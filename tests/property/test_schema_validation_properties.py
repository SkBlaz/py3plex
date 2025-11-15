#!/usr/bin/env python3
"""
Property-based tests for io.schema validation.

Tests invariants and correctness properties of schema validation,
including JSON serializability, referential integrity, and uniqueness constraints.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import schema module
try:
    from py3plex.io.schema import (
        Node, Layer, Edge, MultiLayerGraph, _is_json_serializable
    )
    from py3plex.io.exceptions import SchemaValidationError, ReferentialIntegrityError
    SCHEMA_AVAILABLE = True
except ImportError:
    SCHEMA_AVAILABLE = False
    pytest.skip("IO schema module not available", allow_module_level=True)


# ============================================================================
# Property Tests: JSON Serializability
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.text(max_size=20),
        st.none(),
        st.lists(st.integers(), max_size=5),
        st.dictionaries(st.text(max_size=10), st.integers(), max_size=5)
    )
)
def test_json_serializable_accepts_valid_types(value):
    """Test that _is_json_serializable accepts JSON-compatible types."""
    # All these types should be JSON-serializable
    assert _is_json_serializable(value), \
        f"Value {value} should be JSON-serializable"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(node_id=st.one_of(st.integers(), st.text(max_size=20)))
def test_node_creation_with_valid_id(node_id):
    """Test that Node can be created with any hashable ID."""
    node = Node(id=node_id, attributes={})
    
    # Node should store the ID
    assert node.id == node_id, "Node should store the provided ID"
    
    # Node should have empty attributes
    assert node.attributes == {}, "Node should have empty attributes dict"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    node_id=st.text(max_size=20),
    attr_value=st.one_of(st.integers(), st.text(max_size=10), st.floats(allow_nan=False, allow_infinity=False))
)
def test_node_accepts_json_serializable_attributes(node_id, attr_value):
    """Test that Node accepts JSON-serializable attributes."""
    node = Node(id=node_id, attributes={'key': attr_value})
    
    # Should successfully create node
    assert node.attributes['key'] == attr_value


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(layer_id=st.one_of(st.integers(), st.text(max_size=20)))
def test_layer_creation_with_valid_id(layer_id):
    """Test that Layer can be created with any hashable ID."""
    layer = Layer(id=layer_id, attributes={})
    
    # Layer should store the ID
    assert layer.id == layer_id, "Layer should store the provided ID"
    
    # Layer should have empty attributes
    assert layer.attributes == {}, "Layer should have empty attributes dict"


# ============================================================================
# Property Tests: Node/Layer Round-trip Serialization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    node_id=st.text(min_size=1, max_size=20),
    attr_key=st.text(min_size=1, max_size=10),
    attr_value=st.one_of(st.integers(), st.text(max_size=10))
)
def test_node_to_dict_from_dict_roundtrip(node_id, attr_key, attr_value):
    """Test that Node can be serialized and deserialized without loss."""
    # Create node with attributes
    original = Node(id=node_id, attributes={attr_key: attr_value})
    
    # Convert to dict and back
    node_dict = original.to_dict()
    restored = Node.from_dict(node_dict)
    
    # Should be identical
    assert restored.id == original.id, "Node ID should be preserved"
    assert restored.attributes == original.attributes, "Node attributes should be preserved"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    layer_id=st.text(min_size=1, max_size=20),
    attr_key=st.text(min_size=1, max_size=10),
    attr_value=st.one_of(st.integers(), st.text(max_size=10))
)
def test_layer_to_dict_from_dict_roundtrip(layer_id, attr_key, attr_value):
    """Test that Layer can be serialized and deserialized without loss."""
    # Create layer with attributes
    original = Layer(id=layer_id, attributes={attr_key: attr_value})
    
    # Convert to dict and back
    layer_dict = original.to_dict()
    restored = Layer.from_dict(layer_dict)
    
    # Should be identical
    assert restored.id == original.id, "Layer ID should be preserved"
    assert restored.attributes == original.attributes, "Layer attributes should be preserved"


# ============================================================================
# Property Tests: Edge Validation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    src=st.text(min_size=1, max_size=10),
    dst=st.text(min_size=1, max_size=10),
    src_layer=st.text(min_size=1, max_size=10),
    dst_layer=st.text(min_size=1, max_size=10),
    key=st.integers(min_value=0, max_value=5)
)
def test_edge_creation_valid(src, dst, src_layer, dst_layer, key):
    """Test that Edge can be created with valid parameters."""
    edge = Edge(
        src=src,
        dst=dst,
        src_layer=src_layer,
        dst_layer=dst_layer,
        key=key,
        attributes={}
    )
    
    # Edge should store all parameters
    assert edge.src == src
    assert edge.dst == dst
    assert edge.src_layer == src_layer
    assert edge.dst_layer == dst_layer
    assert edge.key == key


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    src=st.text(min_size=1, max_size=10),
    dst=st.text(min_size=1, max_size=10),
    layer=st.text(min_size=1, max_size=10),
    key=st.integers(min_value=0, max_value=5)
)
def test_edge_tuple_uniqueness(src, dst, layer, key):
    """Test that edge_tuple provides unique identifier."""
    edge1 = Edge(src=src, dst=dst, src_layer=layer, dst_layer=layer, key=key)
    edge2 = Edge(src=src, dst=dst, src_layer=layer, dst_layer=layer, key=key)
    
    # Same parameters should produce same tuple
    assert edge1.edge_tuple() == edge2.edge_tuple(), \
        "Edges with same parameters should have same tuple"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    src=st.text(min_size=1, max_size=10),
    dst=st.text(min_size=1, max_size=10),
    layer=st.text(min_size=1, max_size=10),
    key1=st.integers(min_value=0, max_value=5),
    key2=st.integers(min_value=0, max_value=5)
)
def test_edge_tuple_different_keys_unique(src, dst, layer, key1, key2):
    """Test that different keys produce different tuples."""
    assume(key1 != key2)
    
    edge1 = Edge(src=src, dst=dst, src_layer=layer, dst_layer=layer, key=key1)
    edge2 = Edge(src=src, dst=dst, src_layer=layer, dst_layer=layer, key=key2)
    
    # Different keys should produce different tuples
    assert edge1.edge_tuple() != edge2.edge_tuple(), \
        "Edges with different keys should have different tuples"


# ============================================================================
# Property Tests: MultiLayerGraph Validation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    num_nodes=st.integers(min_value=1, max_value=5),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_multilayer_graph_add_nodes_preserves_count(num_nodes, num_layers):
    """Test that adding nodes preserves node count."""
    graph = MultiLayerGraph()
    
    # Add layers first
    for i in range(num_layers):
        layer = Layer(id=f'layer{i}')
        graph.add_layer(layer)
    
    # Add nodes
    for i in range(num_nodes):
        node = Node(id=f'node{i}')
        graph.add_node(node)
    
    # Should have exactly num_nodes nodes
    assert len(graph.nodes) == num_nodes, \
        f"Should have {num_nodes} nodes, got {len(graph.nodes)}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    num_nodes=st.integers(min_value=1, max_value=5),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_multilayer_graph_add_layers_preserves_count(num_nodes, num_layers):
    """Test that adding layers preserves layer count."""
    graph = MultiLayerGraph()
    
    # Add nodes
    for i in range(num_nodes):
        node = Node(id=f'node{i}')
        graph.add_node(node)
    
    # Add layers
    for i in range(num_layers):
        layer = Layer(id=f'layer{i}')
        graph.add_layer(layer)
    
    # Should have exactly num_layers layers
    assert len(graph.layers) == num_layers, \
        f"Should have {num_layers} layers, got {len(graph.layers)}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(node_id=st.text(min_size=1, max_size=10))
def test_multilayer_graph_duplicate_node_raises_error(node_id):
    """Test that adding duplicate node raises SchemaValidationError."""
    graph = MultiLayerGraph()
    
    # Add node once
    node1 = Node(id=node_id)
    graph.add_node(node1)
    
    # Try to add again
    node2 = Node(id=node_id)
    with pytest.raises(SchemaValidationError):
        graph.add_node(node2)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(layer_id=st.text(min_size=1, max_size=10))
def test_multilayer_graph_duplicate_layer_raises_error(layer_id):
    """Test that adding duplicate layer raises SchemaValidationError."""
    graph = MultiLayerGraph()
    
    # Add layer once
    layer1 = Layer(id=layer_id)
    graph.add_layer(layer1)
    
    # Try to add again
    layer2 = Layer(id=layer_id)
    with pytest.raises(SchemaValidationError):
        graph.add_layer(layer2)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    node1=st.text(min_size=1, max_size=10),
    node2=st.text(min_size=1, max_size=10),
    layer=st.text(min_size=1, max_size=10)
)
def test_multilayer_graph_edge_requires_existing_nodes(node1, node2, layer):
    """Test that adding edge with non-existent nodes raises ReferentialIntegrityError."""
    assume(node1 != node2)
    
    graph = MultiLayerGraph()
    
    # Add only layer, no nodes
    layer_obj = Layer(id=layer)
    graph.add_layer(layer_obj)
    
    # Try to add edge without nodes
    edge = Edge(src=node1, dst=node2, src_layer=layer, dst_layer=layer)
    with pytest.raises(ReferentialIntegrityError):
        graph.add_edge(edge)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    node1=st.text(min_size=1, max_size=10),
    node2=st.text(min_size=1, max_size=10),
    layer=st.text(min_size=1, max_size=10)
)
def test_multilayer_graph_edge_requires_existing_layers(node1, node2, layer):
    """Test that adding edge with non-existent layers raises ReferentialIntegrityError."""
    assume(node1 != node2)
    
    graph = MultiLayerGraph()
    
    # Add only nodes, no layer
    node1_obj = Node(id=node1)
    node2_obj = Node(id=node2)
    graph.add_node(node1_obj)
    graph.add_node(node2_obj)
    
    # Try to add edge without layer
    edge = Edge(src=node1, dst=node2, src_layer=layer, dst_layer=layer)
    with pytest.raises(ReferentialIntegrityError):
        graph.add_edge(edge)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    node1=st.text(min_size=1, max_size=10),
    node2=st.text(min_size=1, max_size=10),
    layer=st.text(min_size=1, max_size=10),
    key=st.integers(min_value=0, max_value=3)
)
def test_multilayer_graph_duplicate_edge_raises_error(node1, node2, layer, key):
    """Test that adding duplicate edge raises SchemaValidationError."""
    assume(node1 != node2)
    
    graph = MultiLayerGraph()
    
    # Add nodes and layer
    node1_obj = Node(id=node1)
    node2_obj = Node(id=node2)
    layer_obj = Layer(id=layer)
    graph.add_node(node1_obj)
    graph.add_node(node2_obj)
    graph.add_layer(layer_obj)
    
    # Add edge once
    edge1 = Edge(src=node1, dst=node2, src_layer=layer, dst_layer=layer, key=key)
    graph.add_edge(edge1)
    
    # Try to add again
    edge2 = Edge(src=node1, dst=node2, src_layer=layer, dst_layer=layer, key=key)
    with pytest.raises(SchemaValidationError):
        graph.add_edge(edge2)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    num_nodes=st.integers(min_value=2, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3),
    num_edges=st.integers(min_value=1, max_value=5)
)
def test_multilayer_graph_to_dict_from_dict_roundtrip(num_nodes, num_layers, num_edges):
    """Test that MultiLayerGraph can be serialized and deserialized."""
    assume(num_edges <= num_nodes * (num_nodes - 1))
    
    graph = MultiLayerGraph()
    
    # Add nodes
    for i in range(num_nodes):
        node = Node(id=f'n{i}')
        graph.add_node(node)
    
    # Add layers
    for i in range(num_layers):
        layer = Layer(id=f'l{i}')
        graph.add_layer(layer)
    
    # Add edges (avoid duplicates)
    edge_count = 0
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if edge_count >= num_edges:
                break
            layer_idx = edge_count % num_layers
            edge = Edge(
                src=f'n{i}',
                dst=f'n{j}',
                src_layer=f'l{layer_idx}',
                dst_layer=f'l{layer_idx}'
            )
            graph.add_edge(edge)
            edge_count += 1
        if edge_count >= num_edges:
            break
    
    # Convert to dict and back
    graph_dict = graph.to_dict()
    restored = MultiLayerGraph.from_dict(graph_dict)
    
    # Should have same structure
    assert len(restored.nodes) == len(graph.nodes), "Node count should be preserved"
    assert len(restored.layers) == len(graph.layers), "Layer count should be preserved"
    assert len(restored.edges) == len(graph.edges), "Edge count should be preserved"


# ============================================================================
# Property Tests: Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    num_nodes=st.integers(min_value=2, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_multilayer_graph_edge_count_non_negative(num_nodes, num_layers):
    """Test that edge count is always non-negative."""
    graph = MultiLayerGraph()
    
    # Add nodes and layers
    for i in range(num_nodes):
        graph.add_node(Node(id=f'n{i}'))
    for i in range(num_layers):
        graph.add_layer(Layer(id=f'l{i}'))
    
    # Edge count should be 0 (no edges added)
    assert len(graph.edges) == 0, "Should have 0 edges initially"
    assert len(graph.edges) >= 0, "Edge count should be non-negative"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    num_nodes=st.integers(min_value=2, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_multilayer_graph_nodes_layers_non_negative(num_nodes, num_layers):
    """Test that node and layer counts are non-negative."""
    graph = MultiLayerGraph()
    
    # Add nodes
    for i in range(num_nodes):
        graph.add_node(Node(id=f'n{i}'))
    
    # Add layers
    for i in range(num_layers):
        graph.add_layer(Layer(id=f'l{i}'))
    
    # Counts should match
    assert len(graph.nodes) == num_nodes >= 0
    assert len(graph.layers) == num_layers >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])

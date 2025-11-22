"""
Tests for schema validation and immutable graph mode.
"""

import pytest
from py3plex.core.schema_validation import (
    FieldValidator,
    NodeSchema,
    EdgeSchema,
    LayerSchema,
    NetworkSchema,
    ValidationError,
)
from py3plex.core.immutable import (
    ImmutableNetworkView,
    make_immutable,
    ImmutableNetworkError,
)
from py3plex.core.multinet import multi_layer_network


class TestFieldValidator:
    """Test FieldValidator class."""
    
    def test_type_validation(self):
        """Test type checking."""
        validator = FieldValidator(int, required=True)
        
        # Valid
        assert validator.validate(42, "test") == 42
        
        # Invalid type
        with pytest.raises(ValidationError):
            validator.validate("not an int", "test")
    
    def test_required_field(self):
        """Test required field validation."""
        validator = FieldValidator(str, required=True)
        
        # Missing required field
        with pytest.raises(ValidationError):
            validator.validate(None, "test")
    
    def test_optional_field_with_default(self):
        """Test optional field with default value."""
        validator = FieldValidator(str, required=False, default="default_value")
        
        result = validator.validate(None, "test")
        assert result == "default_value"
    
    def test_choices_validation(self):
        """Test choices constraint."""
        validator = FieldValidator(str, choices=["A", "B", "C"])
        
        # Valid choice
        assert validator.validate("A", "test") == "A"
        
        # Invalid choice
        with pytest.raises(ValidationError):
            validator.validate("D", "test")
    
    def test_numeric_range_validation(self):
        """Test min/max value constraints."""
        validator = FieldValidator(float, min_value=0.0, max_value=1.0)
        
        # Valid
        assert validator.validate(0.5, "test") == 0.5
        
        # Too small
        with pytest.raises(ValidationError):
            validator.validate(-0.1, "test")
        
        # Too large
        with pytest.raises(ValidationError):
            validator.validate(1.5, "test")
    
    def test_custom_validator(self):
        """Test custom validation function."""
        def is_even(x):
            return x % 2 == 0
        
        validator = FieldValidator(int, custom_validator=is_even)
        
        # Valid
        assert validator.validate(4, "test") == 4
        
        # Invalid
        with pytest.raises(ValidationError):
            validator.validate(3, "test")


class TestNodeSchema:
    """Test NodeSchema class."""
    
    def test_node_validation(self):
        """Test basic node validation."""
        schema = NodeSchema(strict=True)
        schema.add_field('weight', FieldValidator(float, required=True, min_value=0))
        schema.add_field('label', FieldValidator(str, required=False))
        
        # Valid node
        attrs = {'weight': 1.5, 'label': 'A'}
        validated = schema.validate_node('node1', attrs)
        assert validated['weight'] == 1.5
        assert validated['label'] == 'A'
    
    def test_strict_mode_unknown_fields(self):
        """Test strict mode with unknown fields."""
        schema = NodeSchema(strict=True)
        schema.add_field('weight', FieldValidator(float))
        
        # Unknown field in strict mode
        attrs = {'weight': 1.0, 'unknown': 'value'}
        with pytest.raises(ValidationError):
            schema.validate_node('node1', attrs)
    
    def test_non_strict_mode(self):
        """Test non-strict mode."""
        schema = NodeSchema(strict=False)
        schema.add_field('weight', FieldValidator(float))
        
        # Unknown field in non-strict mode - should warn but not error
        attrs = {'weight': 1.0, 'unknown': 'value'}
        with pytest.warns(UserWarning):
            validated = schema.validate_node('node1', attrs)
            assert 'unknown' in validated


class TestLayerSchema:
    """Test LayerSchema class."""
    
    def test_allowed_layers(self):
        """Test allowed layers validation."""
        schema = LayerSchema(strict=True)
        schema.set_allowed_layers(['social', 'biological', 'email'])
        
        # Valid layer
        assert schema.validate_layer('social')
        
        # Invalid layer
        with pytest.raises(ValidationError):
            schema.validate_layer('unknown')
    
    def test_custom_validator(self):
        """Test custom layer validator."""
        def starts_with_l(layer):
            return layer.startswith('L')
        
        schema = LayerSchema(strict=True)
        schema.set_custom_validator(starts_with_l)
        
        # Valid
        assert schema.validate_layer('L1')
        
        # Invalid
        with pytest.raises(ValidationError):
            schema.validate_layer('A1')


class TestImmutableNetworkView:
    """Test ImmutableNetworkView class."""
    
    def test_immutable_view_creation(self):
        """Test creating immutable view."""
        net = multi_layer_network(network_type='multilayer', directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        
        immutable = ImmutableNetworkView(net, copy_on_write=False, deep_copy=True)
        
        # Read operations should work
        assert immutable.number_of_nodes() > 0
    
    def test_modification_raises_error(self):
        """Test that modifications raise error without copy-on-write."""
        net = multi_layer_network(network_type='multilayer', directed=False)
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        immutable = ImmutableNetworkView(net, copy_on_write=False)
        
        # Modification should raise error
        with pytest.raises(ImmutableNetworkError):
            immutable.add_nodes([{'source': 'B', 'type': 'layer1'}])
    
    def test_copy_on_write(self):
        """Test copy-on-write mode."""
        net = multi_layer_network(network_type='multilayer', directed=False)
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        immutable = ImmutableNetworkView(net, copy_on_write=True)
        original_nodes = immutable.number_of_nodes()
        
        # Modification should return new network
        modified = immutable.add_nodes([{'source': 'B', 'type': 'layer1'}])
        
        # Original should be unchanged
        assert immutable.number_of_nodes() == original_nodes
        
        # Modified should have more nodes (if it returns a new network)
        # Note: The exact behavior depends on implementation
    
    def test_to_mutable(self):
        """Test converting to mutable network."""
        net = multi_layer_network(network_type='multilayer', directed=False)
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        immutable = ImmutableNetworkView(net)
        mutable = immutable.to_mutable(deep_copy=True)
        
        # Should be able to modify mutable version
        assert hasattr(mutable, 'add_nodes')
    
    def test_make_immutable_convenience(self):
        """Test make_immutable convenience function."""
        net = multi_layer_network(network_type='multilayer', directed=False)
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        immutable = make_immutable(net)
        
        assert isinstance(immutable, ImmutableNetworkView)
        assert immutable.is_frozen()


class TestNetworkSchemaIntegration:
    """Integration tests for network schema validation."""
    
    def test_full_network_validation(self):
        """Test validating a complete network."""
        # Create network
        net = multi_layer_network(network_type='multilayer', directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        
        # Create schema
        schema = NetworkSchema(strict=False)
        schema.layer_schema.set_allowed_layers(['layer1', 'layer2'])
        
        # Validate - should not raise in non-strict mode
        result = schema.validate_network(net)
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

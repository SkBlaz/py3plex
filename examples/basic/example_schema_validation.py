"""
Example demonstrating schema validation for multilayer networks.

This example shows how to use NetworkSchema to validate node attributes,
edge attributes, and layer names with type-safe constraints.
"""

from py3plex.core.multinet import multi_layer_network
from py3plex.core.schema_validation import NetworkSchema, FieldValidator, ValidationError


def main():
    """Demonstrate schema validation."""
    print("=== Schema Validation Demo ===\n")
    
    # Create a schema with validation rules
    schema = NetworkSchema(strict=False)
    
    # Add node attribute validation
    schema.node_schema.add_field(
        'weight', 
        FieldValidator(float, required=True, min_value=0)
    )
    
    # Add layer name validation
    schema.layer_schema.set_allowed_layers(['social', 'biological'])
    
    print("Schema defined with rules:")
    print("  - Node 'weight' attribute: required, float, >= 0")
    print("  - Allowed layers: social, biological\n")
    
    # Create a test network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
    ])
    
    # Validate the network
    try:
        is_valid = schema.validate_network(net)
        if is_valid:
            print("✓ Network validation passed!")
        else:
            print("⚠ Network has validation warnings (see above)")
    except ValidationError as e:
        print(f"✗ Validation error: {e}")
    
    print("\nNote: Schema validation helps ensure data quality and")
    print("prevents errors in downstream analysis pipelines.\n")


if __name__ == "__main__":
    main()

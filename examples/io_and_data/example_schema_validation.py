"""
Validate multilayer networks with a schema.

Shows how to declare node and layer constraints, validate a small network, and
surface friendly errors. Prerequisite: py3plex installed; no optional extras.
"""

from __future__ import annotations

from py3plex.core.multinet import multi_layer_network
from py3plex.core.schema_validation import FieldValidator, NetworkSchema, ValidationError


def main() -> int:
    """Demonstrate schema validation."""
    print("=== Schema Validation Demo ===\n")

    schema = NetworkSchema(strict=False)
    schema.node_schema.add_field("weight", FieldValidator(float, required=True, min_value=0))
    schema.layer_schema.set_allowed_layers(["social", "biological"])

    print("Schema defined with rules:")
    print("  - Node 'weight' attribute: required, float, >= 0")
    print("  - Allowed layers: social, biological\n")

    net = multi_layer_network(network_type="multilayer", directed=False)
    net.add_nodes(
        [
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
            },
        ]
    )

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Graph attribute schema validation for multilayer networks.

Provides a pydantic-like schema mechanism for ensuring layers, node metadata,
and edge metadata follow consistent rules.

Features:
- Define schemas for node and edge attributes
- Validate layer structure and naming
- Type checking for metadata fields
- Custom validation rules

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
import warnings


class ValidationError(Exception):
    """Raised when schema validation fails."""
    pass


class FieldValidator:
    """Validator for individual field constraints.
    
    Example:
        >>> validator = FieldValidator(str, required=True, choices=['A', 'B', 'C'])
        >>> validator.validate('A')  # OK
        >>> validator.validate('D')  # Raises ValidationError
    """
    
    def __init__(
        self,
        field_type: Type,
        required: bool = False,
        choices: Optional[List[Any]] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        custom_validator: Optional[Callable] = None,
        default: Any = None,
    ):
        """Initialize field validator.
        
        Args:
            field_type: Expected type of the field (e.g., int, str, float)
            required: Whether the field is required
            choices: List of allowed values (if restricted)
            min_value: Minimum value for numeric fields
            max_value: Maximum value for numeric fields
            custom_validator: Custom validation function (value) -> bool
            default: Default value if field is missing
        """
        self.field_type = field_type
        self.required = required
        self.choices = choices
        self.min_value = min_value
        self.max_value = max_value
        self.custom_validator = custom_validator
        self.default = default
    
    def validate(self, value: Any, field_name: str = "field") -> Any:
        """Validate a value against this field's constraints.
        
        Args:
            value: Value to validate
            field_name: Name of the field (for error messages)
            
        Returns:
            Validated value (possibly with default applied)
            
        Raises:
            ValidationError: If validation fails
        """
        # Handle missing values
        if value is None:
            if self.required:
                raise ValidationError(f"Required field '{field_name}' is missing")
            return self.default
        
        # Type checking
        if not isinstance(value, self.field_type):
            raise ValidationError(
                f"Field '{field_name}' must be of type {self.field_type.__name__}, "
                f"got {type(value).__name__}"
            )
        
        # Choice validation
        if self.choices is not None and value not in self.choices:
            raise ValidationError(
                f"Field '{field_name}' must be one of {self.choices}, got {value}"
            )
        
        # Range validation for numeric types
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                raise ValidationError(
                    f"Field '{field_name}' must be >= {self.min_value}, got {value}"
                )
            if self.max_value is not None and value > self.max_value:
                raise ValidationError(
                    f"Field '{field_name}' must be <= {self.max_value}, got {value}"
                )
        
        # Custom validation
        if self.custom_validator is not None:
            if not self.custom_validator(value):
                raise ValidationError(
                    f"Field '{field_name}' failed custom validation"
                )
        
        return value


class NodeSchema:
    """Schema for node attributes in multilayer networks.
    
    Example:
        >>> schema = NodeSchema()
        >>> schema.add_field('weight', FieldValidator(float, required=True, min_value=0))
        >>> schema.add_field('label', FieldValidator(str))
        >>> schema.validate_node('node1', {'weight': 1.5, 'label': 'A'})
    """
    
    def __init__(self, strict: bool = True):
        """Initialize node schema.
        
        Args:
            strict: If True, raise errors on unknown fields; if False, warn only
        """
        self.fields: Dict[str, FieldValidator] = {}
        self.strict = strict
    
    def add_field(self, name: str, validator: FieldValidator) -> None:
        """Add a field validator to the schema.
        
        Args:
            name: Field name
            validator: FieldValidator instance
        """
        self.fields[name] = validator
    
    def validate_node(self, node_id: Any, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Validate node attributes against schema.
        
        Args:
            node_id: Node identifier (for error messages)
            attributes: Dictionary of node attributes
            
        Returns:
            Validated and normalized attributes
            
        Raises:
            ValidationError: If validation fails
        """
        validated = {}
        
        # Validate defined fields
        for field_name, validator in self.fields.items():
            value = attributes.get(field_name)
            validated[field_name] = validator.validate(value, field_name)
        
        # Handle unknown fields
        unknown_fields = set(attributes.keys()) - set(self.fields.keys())
        if unknown_fields:
            if self.strict:
                raise ValidationError(
                    f"Node {node_id} has unknown fields: {unknown_fields}"
                )
            else:
                warnings.warn(
                    f"Node {node_id} has unknown fields: {unknown_fields}. "
                    "These will be ignored.",
                    UserWarning
                )
                # Include unknown fields in validated dict if not strict
                for field in unknown_fields:
                    validated[field] = attributes[field]
        
        return validated


class EdgeSchema:
    """Schema for edge attributes in multilayer networks.
    
    Example:
        >>> schema = EdgeSchema()
        >>> schema.add_field('weight', FieldValidator(float, required=True, min_value=0))
        >>> schema.validate_edge(('A', 'B'), {'weight': 2.5})
    """
    
    def __init__(self, strict: bool = True):
        """Initialize edge schema.
        
        Args:
            strict: If True, raise errors on unknown fields; if False, warn only
        """
        self.fields: Dict[str, FieldValidator] = {}
        self.strict = strict
    
    def add_field(self, name: str, validator: FieldValidator) -> None:
        """Add a field validator to the schema.
        
        Args:
            name: Field name
            validator: FieldValidator instance
        """
        self.fields[name] = validator
    
    def validate_edge(self, edge: tuple, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Validate edge attributes against schema.
        
        Args:
            edge: Edge tuple (for error messages)
            attributes: Dictionary of edge attributes
            
        Returns:
            Validated and normalized attributes
            
        Raises:
            ValidationError: If validation fails
        """
        validated = {}
        
        # Validate defined fields
        for field_name, validator in self.fields.items():
            value = attributes.get(field_name)
            validated[field_name] = validator.validate(value, field_name)
        
        # Handle unknown fields
        unknown_fields = set(attributes.keys()) - set(self.fields.keys())
        if unknown_fields:
            if self.strict:
                raise ValidationError(
                    f"Edge {edge} has unknown fields: {unknown_fields}"
                )
            else:
                warnings.warn(
                    f"Edge {edge} has unknown fields: {unknown_fields}. "
                    "These will be ignored.",
                    UserWarning
                )
                # Include unknown fields if not strict
                for field in unknown_fields:
                    validated[field] = attributes[field]
        
        return validated


class LayerSchema:
    """Schema for layer structure and naming in multilayer networks.
    
    Example:
        >>> schema = LayerSchema()
        >>> schema.set_allowed_layers(['social', 'biological', 'email'])
        >>> schema.validate_layer('social')  # OK
        >>> schema.validate_layer('unknown')  # Raises ValidationError
    """
    
    def __init__(self, strict: bool = True):
        """Initialize layer schema.
        
        Args:
            strict: If True, raise errors on unknown layers; if False, warn only
        """
        self.allowed_layers: Optional[Set[str]] = None
        self.layer_validator: Optional[Callable] = None
        self.strict = strict
    
    def set_allowed_layers(self, layers: List[str]) -> None:
        """Set the list of allowed layer names.
        
        Args:
            layers: List of valid layer names
        """
        self.allowed_layers = set(layers)
    
    def set_custom_validator(self, validator: Callable[[str], bool]) -> None:
        """Set a custom validation function for layer names.
        
        Args:
            validator: Function that takes a layer name and returns True if valid
        """
        self.layer_validator = validator
    
    def validate_layer(self, layer: str) -> bool:
        """Validate a layer name.
        
        Args:
            layer: Layer name to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails and strict mode is enabled
        """
        # Check against allowed layers
        if self.allowed_layers is not None:
            if layer not in self.allowed_layers:
                msg = f"Layer '{layer}' not in allowed layers: {self.allowed_layers}"
                if self.strict:
                    raise ValidationError(msg)
                else:
                    warnings.warn(msg, UserWarning)
                    return False
        
        # Custom validation
        if self.layer_validator is not None:
            if not self.layer_validator(layer):
                msg = f"Layer '{layer}' failed custom validation"
                if self.strict:
                    raise ValidationError(msg)
                else:
                    warnings.warn(msg, UserWarning)
                    return False
        
        return True


class NetworkSchema:
    """Complete schema for multilayer network validation.
    
    Combines node, edge, and layer schemas for comprehensive validation.
    
    Example:
        >>> schema = NetworkSchema()
        >>> schema.node_schema.add_field('weight', FieldValidator(float, required=True))
        >>> schema.edge_schema.add_field('type', FieldValidator(str, required=True))
        >>> schema.layer_schema.set_allowed_layers(['A', 'B', 'C'])
        >>> schema.validate_network(network)
    """
    
    def __init__(self, strict: bool = True):
        """Initialize network schema.
        
        Args:
            strict: If True, raise errors on validation failures; if False, warn only
        """
        self.node_schema = NodeSchema(strict=strict)
        self.edge_schema = EdgeSchema(strict=strict)
        self.layer_schema = LayerSchema(strict=strict)
        self.strict = strict
    
    def validate_network(self, network: Any) -> bool:
        """Validate an entire multilayer network against the schema.
        
        Args:
            network: multi_layer_network instance to validate
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If validation fails and strict mode is enabled
        """
        if network.core_network is None:
            raise ValidationError("Network has no core_network to validate")
        
        errors = []
        
        # Validate nodes
        for node in network.core_network.nodes(data=True):
            node_id = node[0]
            attrs = node[1] if len(node) > 1 else {}
            
            # Validate layer if node is a tuple (node_id, layer)
            if isinstance(node_id, tuple) and len(node_id) >= 2:
                try:
                    self.layer_schema.validate_layer(node_id[1])
                except ValidationError as e:
                    errors.append(str(e))
            
            # Validate node attributes
            try:
                self.node_schema.validate_node(node_id, attrs)
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate edges
        for edge in network.core_network.edges(data=True):
            edge_tuple = (edge[0], edge[1])
            attrs = edge[2] if len(edge) > 2 else {}
            
            try:
                self.edge_schema.validate_edge(edge_tuple, attrs)
            except ValidationError as e:
                errors.append(str(e))
        
        # Report errors
        if errors:
            error_msg = "\n".join(errors)
            if self.strict:
                raise ValidationError(f"Network validation failed:\n{error_msg}")
            else:
                warnings.warn(
                    f"Network validation warnings:\n{error_msg}",
                    UserWarning
                )
                return False
        
        return True

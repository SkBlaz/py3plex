"""Type resolver for DSL queries.

Walks the AST and infers types for all expressions.
"""

from typing import Optional
from ..ast import (
    Query,
    SelectStmt,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    ComputeItem,
    LayerExpr,
)
from .schema import SchemaProvider, EntityRef
from .types import TypeEnvironment, AttrType


class TypeResolver:
    """Resolves types for DSL queries."""
    
    def __init__(self, schema: Optional[SchemaProvider] = None):
        """Initialize type resolver.
        
        Args:
            schema: Optional schema provider for looking up attribute types
        """
        self.schema = schema
        self.type_env = TypeEnvironment()
    
    def resolve(self, query: Query) -> TypeEnvironment:
        """Resolve types for a query.
        
        Args:
            query: Query AST
            
        Returns:
            Type environment with resolved types
        """
        if query.select:
            self._resolve_select(query.select)
        
        return self.type_env
    
    def _resolve_select(self, select: SelectStmt):
        """Resolve types in a SELECT statement."""
        # Resolve layers
        if select.layer_expr:
            self._resolve_layer_expr(select.layer_expr)
        
        # Resolve WHERE conditions
        if select.where:
            self._resolve_conditions(select.where)
        
        # Resolve COMPUTE items
        for compute in select.compute:
            self._resolve_compute(compute)
    
    def _resolve_layer_expr(self, layer_expr: LayerExpr):
        """Resolve layer expression."""
        for term in layer_expr.terms:
            self.type_env.add_layer(term.name)
    
    def _resolve_conditions(self, conditions: ConditionExpr):
        """Resolve types in conditions."""
        for atom in conditions.atoms:
            self._resolve_atom(atom)
    
    def _resolve_atom(self, atom: ConditionAtom):
        """Resolve types in a condition atom."""
        if atom.comparison:
            self._resolve_comparison(atom.comparison)
    
    def _resolve_comparison(self, comparison: Comparison):
        """Resolve types in a comparison."""
        # Try to infer type of the left side (attribute)
        if self.schema:
            entity_ref = EntityRef(entity_type="node", attribute=comparison.left)
            attr_type = self.schema.get_attribute_type(entity_ref, comparison.left)
            if attr_type:
                self.type_env.set_attribute_type(comparison.left, attr_type)
        
        # If no schema or type not found, use heuristics
        if comparison.left not in self.type_env.attribute_types:
            # Built-in attributes
            if comparison.left == "degree":
                self.type_env.set_attribute_type(comparison.left, AttrType.NUMERIC)
            elif comparison.left == "layer":
                self.type_env.set_attribute_type(comparison.left, AttrType.CATEGORICAL)
            else:
                # Try to infer from right side
                right_type = self._infer_literal_type(comparison.right)
                self.type_env.set_attribute_type(comparison.left, right_type)
    
    def _resolve_compute(self, compute: ComputeItem):
        """Resolve types for computed measures."""
        # Known measure types
        measure_types = {
            "degree": AttrType.NUMERIC,
            "degree_centrality": AttrType.NUMERIC,
            "betweenness_centrality": AttrType.NUMERIC,
            "betweenness": AttrType.NUMERIC,
            "closeness_centrality": AttrType.NUMERIC,
            "closeness": AttrType.NUMERIC,
            "eigenvector_centrality": AttrType.NUMERIC,
            "eigenvector": AttrType.NUMERIC,
            "pagerank": AttrType.NUMERIC,
            "clustering": AttrType.NUMERIC,
            "communities": AttrType.CATEGORICAL,
            "community": AttrType.CATEGORICAL,
        }
        
        result_name = compute.result_name
        measure_type = measure_types.get(compute.name, AttrType.UNKNOWN)
        self.type_env.set_computed_type(result_name, measure_type)
    
    def _infer_literal_type(self, value) -> AttrType:
        """Infer type from a literal value.
        
        Note: Does not distinguish between int and float - both are NUMERIC.
        This is intentional to simplify the type system and avoid false positives
        in type checking (e.g., comparing int with float is valid).
        """
        if isinstance(value, bool):
            return AttrType.BOOLEAN
        if isinstance(value, (int, float)):
            return AttrType.NUMERIC
        if isinstance(value, str):
            # Try to parse as number
            try:
                float(value)
                return AttrType.NUMERIC
            except ValueError:
                return AttrType.CATEGORICAL
        
        return AttrType.UNKNOWN

"""AST (Abstract Syntax Tree) definitions for DSL v2.

This module defines the core data structures that represent parsed DSL queries.
All query frontends (string DSL, builder API, dplyr-style) compile to these
AST nodes, which are then executed by the same engine.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class Target(Enum):
    """Query target - what to select from the network."""
    NODES = "nodes"
    EDGES = "edges"


class ExportTarget(Enum):
    """Export target for query results."""
    PANDAS = "pandas"
    NETWORKX = "networkx"
    ARROW = "arrow"


@dataclass
class ParamRef:
    """Reference to a query parameter.
    
    Parameters are placeholders in queries that are bound at execution time.
    
    Attributes:
        name: Parameter name (e.g., "k" for :k in DSL)
        type_hint: Optional type hint for validation
    """
    name: str
    type_hint: Optional[str] = None
    
    def __repr__(self) -> str:
        return f":{self.name}"


@dataclass
class LayerTerm:
    """A single layer reference in a layer expression.
    
    Attributes:
        name: Layer name (e.g., "social", "work")
    """
    name: str


@dataclass
class LayerExpr:
    """Layer expression with optional algebra operations.
    
    Supports:
        - Union: LAYER("a") + LAYER("b")
        - Difference: LAYER("a") - LAYER("b") 
        - Intersection: LAYER("a") & LAYER("b")
    
    Attributes:
        terms: List of layer terms
        ops: List of operators between terms ('+', '-', '&')
    """
    terms: List[LayerTerm] = field(default_factory=list)
    ops: List[str] = field(default_factory=list)
    
    def get_layer_names(self) -> List[str]:
        """Get all layer names referenced in this expression."""
        return [term.name for term in self.terms]


# Value type for comparisons and function arguments
Value = Union[str, float, int, ParamRef]


@dataclass
class Comparison:
    """A comparison expression.
    
    Attributes:
        left: Attribute name (e.g., "degree", "layer")
        op: Comparison operator ('>', '>=', '<', '<=', '=', '!=')
        right: Value to compare against
    """
    left: str
    op: str
    right: Value


@dataclass
class FunctionCall:
    """A function call in a condition.
    
    Attributes:
        name: Function name (e.g., "reachable_from")
        args: List of arguments
    """
    name: str
    args: List[Value] = field(default_factory=list)


@dataclass
class SpecialPredicate:
    """Special multilayer predicates.
    
    Supported kinds:
        - 'intralayer': Edges within the same layer
        - 'interlayer': Edges between specific layers
        - 'motif': Motif pattern matching
        - 'reachable_from': Cross-layer reachability
    
    Attributes:
        kind: Predicate type
        params: Additional parameters for the predicate
    """
    kind: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionAtom:
    """A single atomic condition.
    
    Exactly one of comparison, function, or special should be non-None.
    
    Attributes:
        comparison: Simple comparison (e.g., degree > 5)
        function: Function call (e.g., reachable_from("Alice"))
        special: Special predicate (e.g., intralayer)
    """
    comparison: Optional[Comparison] = None
    function: Optional[FunctionCall] = None
    special: Optional[SpecialPredicate] = None
    
    @property
    def is_comparison(self) -> bool:
        return self.comparison is not None
    
    @property
    def is_function(self) -> bool:
        return self.function is not None
    
    @property
    def is_special(self) -> bool:
        return self.special is not None


@dataclass
class ConditionExpr:
    """Compound condition expression.
    
    Represents conditions joined by logical operators (AND, OR).
    
    Attributes:
        atoms: List of condition atoms
        ops: List of logical operators ('AND', 'OR') between atoms
    """
    atoms: List[ConditionAtom] = field(default_factory=list)
    ops: List[str] = field(default_factory=list)


@dataclass
class ComputeItem:
    """A measure to compute.
    
    Attributes:
        name: Measure name (e.g., 'betweenness_centrality')
        alias: Optional alias for the result (e.g., 'bc')
    """
    name: str
    alias: Optional[str] = None
    
    @property
    def result_name(self) -> str:
        """Get the name to use in results (alias or original name)."""
        return self.alias if self.alias else self.name


@dataclass
class OrderItem:
    """Ordering specification.
    
    Attributes:
        key: Attribute or computed value to order by
        desc: True for descending order, False for ascending
    """
    key: str
    desc: bool = False


@dataclass
class SelectStmt:
    """A SELECT statement.
    
    Attributes:
        target: What to select (nodes or edges)
        layer_expr: Optional layer expression for filtering
        where: Optional WHERE conditions
        compute: List of measures to compute
        order_by: List of ordering specifications
        limit: Optional limit on results
        export: Optional export target
    """
    target: Target
    layer_expr: Optional[LayerExpr] = None
    where: Optional[ConditionExpr] = None
    compute: List[ComputeItem] = field(default_factory=list)
    order_by: List[OrderItem] = field(default_factory=list)
    limit: Optional[int] = None
    export: Optional[ExportTarget] = None


@dataclass
class Query:
    """Top-level query representation.
    
    Attributes:
        explain: If True, return execution plan instead of results
        select: The SELECT statement
        dsl_version: DSL version for compatibility
    """
    explain: bool
    select: SelectStmt
    dsl_version: str = "2.0"


@dataclass
class PlanStep:
    """A step in the execution plan.
    
    Attributes:
        description: Human-readable description of the step
        estimated_complexity: Estimated time complexity (e.g., "O(|V|)")
    """
    description: str
    estimated_complexity: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Execution plan for EXPLAIN queries.
    
    Attributes:
        steps: List of execution steps
        warnings: List of performance or correctness warnings
    """
    steps: List[PlanStep] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

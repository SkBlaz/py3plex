"""AST (Abstract Syntax Tree) definitions for simulation DSL.

This module defines the core data structures that represent parsed simulation
specifications. The simulation AST integrates with the query DSL AST for
initial conditions that use SELECT queries.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Re-use SelectStmt from query AST for INITIAL ... SELECT ...
from py3plex.dsl.ast import SelectStmt


@dataclass
class InitialSpec:
    """Specification for initial condition.

    Initial conditions can be:
    - A constant (scalar fraction, literal node id, etc.)
    - A query (SELECT statement for selecting initial nodes)

    Attributes:
        constant: Scalar value (e.g., 0.01 for 1% infected fraction)
        query: SelectStmt from query AST for query-based initialization
    """
    constant: Optional[Any] = None
    query: Optional[SelectStmt] = None

    def __post_init__(self):
        """Validate that exactly one of constant or query is set."""
        if self.constant is None and self.query is None:
            raise ValueError("InitialSpec must have either constant or query")
        if self.constant is not None and self.query is not None:
            raise ValueError("InitialSpec cannot have both constant and query")


@dataclass
class SimulationStmt:
    """A simulation specification statement.

    Represents a complete simulation configuration including:
    - Process to simulate (SIS, SIR, RANDOM_WALK, etc.)
    - Layer expression defining active layers
    - Coupling options for multilayer dynamics
    - Process parameters
    - Initial conditions
    - Simulation configuration (steps, replicates, seed)
    - Measures to collect
    - Export target

    Attributes:
        process_name: Name of the process (e.g., "SIS", "SIR", "RANDOM_WALK")
        layer_expr: Layer expression from query AST (optional)
        coupling: Coupling options (e.g., {"node_replicas": "strong"})
        params: Process parameters (e.g., {"beta": 0.3, "mu": 0.1})
        initial: Initial conditions mapping (e.g., {"infected": InitialSpec(...)})
        steps: Number of time steps to simulate
        measures: List of measure names to collect
        replicates: Number of simulation replicates (default 1)
        seed: Random seed for reproducibility (optional)
        export_target: Export format ("pandas", "arrow", "xarray")
    """
    process_name: str
    layer_expr: Optional[Any] = None  # LayerExpr from query AST
    coupling: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    initial: Dict[str, InitialSpec] = field(default_factory=dict)
    steps: int = 1
    measures: List[str] = field(default_factory=list)
    replicates: int = 1
    seed: Optional[int] = None
    export_target: Optional[str] = None


@dataclass
class Simulation:
    """Top-level simulation representation.

    Attributes:
        stmt: The simulation statement
        dsl_version: DSL version for compatibility
    """
    stmt: SimulationStmt
    dsl_version: str = "1.0"

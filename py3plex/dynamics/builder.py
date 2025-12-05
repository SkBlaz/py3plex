"""Python Builder API for simulation DSL.

This module provides a chainable, type-hinted builder API for constructing
simulation specifications. The builder API maps directly to the AST nodes.

Example:
    >>> from py3plex.dynamics import D, SIS, SIR, RandomWalk
    >>> from py3plex.dsl import Q, L
    >>>
    >>> sim = (
    ...     D.process(SIS(beta=0.3, mu=0.1))
    ...      .on_layers(L["contact"])
    ...      .initial(
    ...          infected=Q.nodes().where(layer="contact", degree__gt=5)
    ...      )
    ...      .steps(100)
    ...      .measure("prevalence", "incidence")
    ...      .replicates(20)
    ...      .seed(42)
    ... )
    >>>
    >>> result = sim.run(network)
    >>> df = result.to_pandas()
"""

from typing import Any, Union

from .ast import SimulationStmt, InitialSpec
from .result import SimulationResult
from .processes import ProcessSpec, get_process


def _create_process_spec(name_or_spec: Union[str, ProcessSpec],
                         **params) -> ProcessSpec:
    """Create a ProcessSpec from name or existing spec.

    Args:
        name_or_spec: Process name string or ProcessSpec instance
        **params: Parameter overrides

    Returns:
        ProcessSpec with updated parameters
    """
    if isinstance(name_or_spec, ProcessSpec):
        spec = name_or_spec
    else:
        spec = get_process(name_or_spec)

    # Create new spec with merged params
    merged_params = {**spec.params, **params}

    return ProcessSpec(
        name=spec.name,
        params=merged_params,
        state_space=spec.state_space,
        update_fn=spec.update_fn,
        required_initial=spec.required_initial,
    )


class SimulationBuilder:
    """Chainable simulation builder.

    Use D.process(SIS(...)) to create a builder, then chain methods
    to construct the simulation.
    """

    def __init__(self, process_spec: ProcessSpec):
        """Initialize builder with process specification.

        Args:
            process_spec: ProcessSpec defining the dynamics
        """
        self.process_spec = process_spec
        self._stmt = SimulationStmt(
            process_name=process_spec.name,
            layer_expr=None,
            coupling={},
            params=process_spec.params.copy(),
            initial={},
            steps=1,
            measures=[],
            replicates=1,
            seed=None,
            export_target=None,
        )

    def on_layers(self, layer_expr: Any) -> "SimulationBuilder":
        """Set layers to simulate on.

        Args:
            layer_expr: Layer expression (e.g., L["social"] + L["work"])

        Returns:
            Self for chaining
        """
        if hasattr(layer_expr, '_to_ast'):
            self._stmt.layer_expr = layer_expr._to_ast()
        else:
            self._stmt.layer_expr = layer_expr
        return self

    def coupling(self, **options) -> "SimulationBuilder":
        """Set coupling options for multilayer dynamics.

        Supported options:
        - node_replicas: "independent", "strong", or "weighted"

        Args:
            **options: Coupling options

        Returns:
            Self for chaining
        """
        self._stmt.coupling.update(options)
        return self

    def with_params(self, **params) -> "SimulationBuilder":
        """Override process parameters.

        Args:
            **params: Parameter overrides (e.g., beta=0.5)

        Returns:
            Self for chaining
        """
        self._stmt.params.update(params)
        return self

    def initial(self, **inits) -> "SimulationBuilder":
        """Set initial conditions.

        Values can be:
        - A scalar (fraction, node id, etc.)
        - A QueryBuilder (for SELECT-based initialization)

        Args:
            **inits: Initial condition specifications

        Returns:
            Self for chaining
        """
        for key, value in inits.items():
            if hasattr(value, 'to_ast'):
                # QueryBuilder from DSL
                query_ast = value.to_ast()
                init = InitialSpec(query=query_ast.select)
            else:
                init = InitialSpec(constant=value)
            self._stmt.initial[key] = init
        return self

    def steps(self, n: int) -> "SimulationBuilder":
        """Set number of simulation steps.

        Args:
            n: Number of time steps

        Returns:
            Self for chaining
        """
        self._stmt.steps = n
        return self

    def measure(self, *measures: str) -> "SimulationBuilder":
        """Add measures to collect during simulation.

        Args:
            *measures: Measure names (e.g., "prevalence", "incidence")

        Returns:
            Self for chaining
        """
        self._stmt.measures.extend(measures)
        return self

    def replicates(self, n: int) -> "SimulationBuilder":
        """Set number of simulation replicates.

        Args:
            n: Number of replicates

        Returns:
            Self for chaining
        """
        self._stmt.replicates = n
        return self

    def seed(self, seed: int) -> "SimulationBuilder":
        """Set random seed for reproducibility.

        Args:
            seed: Random seed value

        Returns:
            Self for chaining
        """
        self._stmt.seed = seed
        return self

    def to(self, export_target: str) -> "SimulationBuilder":
        """Set export target for results.

        Args:
            export_target: Export format ("pandas", "arrow", "xarray")

        Returns:
            Self for chaining
        """
        self._stmt.export_target = export_target
        return self

    def to_ast(self) -> SimulationStmt:
        """Export as AST SimulationStmt.

        Returns:
            SimulationStmt AST node
        """
        return self._stmt

    def to_dsl(self) -> str:
        """Export as DSL string.

        Returns:
            SIMULATE DSL string
        """
        from .serializer import sim_ast_to_dsl
        return sim_ast_to_dsl(self._stmt)

    def run(self, network: Any, backend: str = "numpy") -> SimulationResult:
        """Execute the simulation.

        Args:
            network: Multilayer network object
            backend: Execution backend ("numpy")

        Returns:
            SimulationResult with collected measures
        """
        from .executor import run_simulation

        result = run_simulation(network, self._stmt, backend=backend)

        # Apply export if specified
        if self._stmt.export_target:
            if self._stmt.export_target == "pandas":
                return result.to_pandas()
            elif self._stmt.export_target == "xarray":
                return result.to_xarray()

        return result

    def __repr__(self) -> str:
        return (f"SimulationBuilder(process={self._stmt.process_name}, "
                f"steps={self._stmt.steps}, replicates={self._stmt.replicates})")


class D:
    """Simulation factory for creating SimulationBuilder instances.

    Example:
        >>> D.process(SIS(beta=0.3, mu=0.1)).steps(100).run(network)
        >>> D.process("SIR").with_params(beta=0.2).steps(200).run(network)
    """

    @staticmethod
    def process(spec: Union[str, ProcessSpec], **params) -> SimulationBuilder:
        """Create a simulation builder for the given process.

        Args:
            spec: Process name or ProcessSpec instance
            **params: Optional parameter overrides

        Returns:
            SimulationBuilder for the process
        """
        process_spec = _create_process_spec(spec, **params)
        return SimulationBuilder(process_spec)

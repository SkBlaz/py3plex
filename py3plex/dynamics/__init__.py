"""Dynamics module for multilayer network simulations.

This module provides a declarative, composable framework for defining and running
dynamical processes on multilayer networks. It includes:

1. A Python builder API for simulation specifications
2. Pre-defined process specifications (SIS, SIR, Random Walk)
3. Multilayer-aware dynamics with coupling options
4. Results format designed for statistical analysis

Example Usage:
    >>> from py3plex.dynamics import D, SIS, SIR, RandomWalk
    >>> from py3plex.dsl import L
    >>>
    >>> # Simple SIS simulation
    >>> sim = (
    ...     D.process(SIS(beta=0.3, mu=0.1))
    ...      .initial(infected=0.01)  # 1% initially infected
    ...      .steps(100)
    ...      .measure("prevalence", "incidence")
    ...      .replicates(20)
    ...      .seed(42)
    ... )
    >>>
    >>> result = sim.run(network)
    >>> df = result.to_pandas()  # Tidy DataFrame
    >>>
    >>> # Multilayer SIR with layer coupling
    >>> sim = (
    ...     D.process(SIR(beta=0.2, gamma=0.05))
    ...      .on_layers(L["offline"] + L["online"])
    ...      .coupling(node_replicas="strong")
    ...      .initial(infected=0.01)
    ...      .steps(200)
    ...      .measure("prevalence", "prevalence_by_layer")
    ...      .replicates(10)
    ... )
    >>> result = sim.run(network)

The DSL also supports a SIMULATE syntax:
    SIMULATE SIS
    ON LAYER("contact")
    WITH beta=0.3, mu=0.1
    INITIAL infected = 0.01
    FOR 100 STEPS
    MEASURE prevalence, incidence
    REPLICATES 20
    SEED 42
"""

from .ast import (
    SimulationStmt,
    InitialSpec,
    Simulation,
)

from .builder import (
    D,
    SimulationBuilder,
)

from .processes import (
    ProcessSpec,
    SIS,
    SIR,
    RandomWalk,
    get_process,
    list_processes,
    register_process,
)

from .result import SimulationResult

from .executor import run_simulation

from .registry import measure_registry

from .errors import (
    DynamicsError,
    UnknownProcessError,
    MissingInitialConditionError,
    UnknownMeasureError,
    SimulationConfigError,
)

from .serializer import sim_ast_to_dsl

# Core abstractions for implementing custom dynamics
from .core import (
    DynamicsProcess,
    ContinuousTimeProcess,
    TemporalGraph,
    TemporalDynamicsProcess,
    DynamicsResult,
)

# Discrete-time models
from .models import (
    RandomWalkDynamics,
    MultiRandomWalkDynamics,
    SISDynamics,
    AdaptiveSISDynamics,
    TemporalRandomWalk,
)

# Continuous-time and compartmental models
from .compartmental import (
    SISContinuousTime,
    CompartmentalDynamics,
    SIRDynamics,
    SEIRDynamics,
)

# Config-based dynamics
from .config import build_dynamics_from_config

__all__ = [
    # AST
    "SimulationStmt",
    "InitialSpec",
    "Simulation",
    # Builder
    "D",
    "SimulationBuilder",
    # Processes
    "ProcessSpec",
    "SIS",
    "SIR",
    "RandomWalk",
    "get_process",
    "list_processes",
    "register_process",
    # Result
    "SimulationResult",
    # Executor
    "run_simulation",
    # Registry
    "measure_registry",
    # Errors
    "DynamicsError",
    "UnknownProcessError",
    "MissingInitialConditionError",
    "UnknownMeasureError",
    "SimulationConfigError",
    # Serializer
    "sim_ast_to_dsl",
    # Core abstractions (NEW)
    "DynamicsProcess",
    "ContinuousTimeProcess",
    "TemporalGraph",
    "TemporalDynamicsProcess",
    "DynamicsResult",
    # Discrete-time models (NEW)
    "RandomWalkDynamics",
    "MultiRandomWalkDynamics",
    "SISDynamics",
    "AdaptiveSISDynamics",
    "TemporalRandomWalk",
    # Continuous-time & compartmental (NEW)
    "SISContinuousTime",
    "CompartmentalDynamics",
    "SIRDynamics",
    "SEIRDynamics",
    # Config-based (NEW)
    "build_dynamics_from_config",
]

# Module version
DYNAMICS_VERSION = "1.0"

"""Process specifications for dynamics module.

This module defines process specifications (SIS, SIR, Random Walk, etc.)
that can be used with the simulation builder API.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np


@dataclass
class ProcessSpec:
    """Specification for a dynamical process.

    A ProcessSpec defines:
    - The process name
    - Default parameters
    - State space (possible states for nodes)
    - Update function factory

    Attributes:
        name: Process name (e.g., "SIS", "SIR", "RANDOM_WALK")
        params: Default parameters (e.g., {"beta": 0.3, "mu": 0.1})
        state_space: State space definition (e.g., {"node_state": ["S", "I"]})
        update_fn: Factory function that returns the update step function
        required_initial: List of required initial condition keys
    """
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    state_space: Dict[str, Any] = field(default_factory=dict)
    update_fn: Optional[Callable[..., Callable]] = None
    required_initial: List[str] = field(default_factory=list)

    def __call__(self, **params) -> "ProcessSpec":
        """Create a new ProcessSpec with overridden parameters.

        This allows SIS(beta=0.5) syntax.

        Args:
            **params: Parameter overrides

        Returns:
            New ProcessSpec with merged parameters
        """
        merged_params = {**self.params, **params}
        return ProcessSpec(
            name=self.name,
            params=merged_params,
            state_space=self.state_space,
            update_fn=self.update_fn,
            required_initial=self.required_initial,
        )


def sis_update_factory(params: Dict[str, Any], coupling: Dict[str, Any]) -> Callable:
    """Factory for SIS update function.

    Args:
        params: Process parameters (beta, mu)
        coupling: Coupling options for multilayer dynamics

    Returns:
        Update function that takes (graph, state, rng) and returns new_state
    """
    beta = params.get("beta", 0.3)
    mu = params.get("mu", 0.1)
    # Reserved for future multilayer coupling implementation
    # beta_cross = params.get("beta_cross", beta)  # Inter-layer transmission
    # node_replicas = coupling.get("node_replicas", "independent")

    def update_step(adj_matrix: np.ndarray, state: np.ndarray,
                    rng: np.random.Generator,
                    node_to_idx: Optional[Dict] = None,
                    layer_info: Optional[Dict] = None) -> np.ndarray:
        """Perform one SIS update step.

        Args:
            adj_matrix: Adjacency matrix (N x N)
            state: Current state array (N,) with 0=S, 1=I
            rng: Random number generator
            node_to_idx: Mapping from node to index (optional)
            layer_info: Layer information for multilayer dynamics (optional)

        Returns:
            New state array
        """
        new_state = state.copy()

        # Recovery: I -> S with probability mu
        infected = np.where(state == 1)[0]
        recovery_probs = rng.random(len(infected))
        recovered = infected[recovery_probs < mu]
        new_state[recovered] = 0

        # Infection: S -> I based on infected neighbors
        susceptible = np.where(state == 0)[0]
        for s in susceptible:
            # Get neighbors
            neighbors = np.where(adj_matrix[s] > 0)[0]
            infected_neighbors = np.sum(state[neighbors] == 1)

            if infected_neighbors > 0:
                # Calculate infection probability
                # p = 1 - (1 - beta)^k where k is number of infected neighbors
                infection_prob = 1.0 - (1.0 - beta) ** infected_neighbors
                if rng.random() < infection_prob:
                    new_state[s] = 1

        return new_state

    return update_step


def sir_update_factory(params: Dict[str, Any], coupling: Dict[str, Any]) -> Callable:
    """Factory for SIR update function.

    Args:
        params: Process parameters (beta, gamma)
        coupling: Coupling options for multilayer dynamics

    Returns:
        Update function that takes (graph, state, rng) and returns new_state
    """
    beta = params.get("beta", 0.2)
    gamma = params.get("gamma", 0.05)

    def update_step(adj_matrix: np.ndarray, state: np.ndarray,
                    rng: np.random.Generator,
                    node_to_idx: Optional[Dict] = None,
                    layer_info: Optional[Dict] = None) -> np.ndarray:
        """Perform one SIR update step.

        Args:
            adj_matrix: Adjacency matrix (N x N)
            state: Current state array (N,) with 0=S, 1=I, 2=R
            rng: Random number generator
            node_to_idx: Mapping from node to index (optional)
            layer_info: Layer information for multilayer dynamics (optional)

        Returns:
            New state array
        """
        new_state = state.copy()

        # Recovery: I -> R with probability gamma
        infected = np.where(state == 1)[0]
        recovery_probs = rng.random(len(infected))
        recovered = infected[recovery_probs < gamma]
        new_state[recovered] = 2

        # Infection: S -> I based on infected neighbors
        susceptible = np.where(state == 0)[0]
        for s in susceptible:
            neighbors = np.where(adj_matrix[s] > 0)[0]
            infected_neighbors = np.sum(state[neighbors] == 1)

            if infected_neighbors > 0:
                infection_prob = 1.0 - (1.0 - beta) ** infected_neighbors
                if rng.random() < infection_prob:
                    new_state[s] = 1

        return new_state

    return update_step


def random_walk_update_factory(params: Dict[str, Any], coupling: Dict[str, Any]) -> Callable:
    """Factory for random walk update function.

    Args:
        params: Process parameters (teleport)
        coupling: Coupling options for multilayer dynamics

    Returns:
        Update function that takes (graph, state, rng) and returns new_state
    """
    teleport = params.get("teleport", 0.05)

    def update_step(adj_matrix: np.ndarray, state: np.ndarray,
                    rng: np.random.Generator,
                    node_to_idx: Optional[Dict] = None,
                    layer_info: Optional[Dict] = None) -> np.ndarray:
        """Perform one random walk step.

        For random walks, state[i] = 1 means walker is at node i.
        Only one node should have state 1 at a time.

        Args:
            adj_matrix: Adjacency matrix (N x N)
            state: Current state array (N,) with 1 at current position
            rng: Random number generator
            node_to_idx: Mapping from node to index (optional)
            layer_info: Layer information for multilayer dynamics (optional)

        Returns:
            New state array with walker at new position
        """
        n = len(state)
        new_state = np.zeros(n, dtype=state.dtype)

        # Find current position
        current_pos = np.where(state == 1)[0]
        if len(current_pos) == 0:
            # No walker, start at random node
            new_state[rng.integers(0, n)] = 1
            return new_state

        current_pos = current_pos[0]

        # Teleport with probability
        if rng.random() < teleport:
            new_state[rng.integers(0, n)] = 1
            return new_state

        # Get neighbors
        neighbors = np.where(adj_matrix[current_pos] > 0)[0]
        if len(neighbors) == 0:
            # No neighbors, stay in place or teleport
            new_state[rng.integers(0, n)] = 1
        else:
            # Move to random neighbor
            new_pos = rng.choice(neighbors)
            new_state[new_pos] = 1

        return new_state

    return update_step


# Pre-defined process specifications
SIS = ProcessSpec(
    name="SIS",
    params={"beta": 0.3, "mu": 0.1},
    state_space={"node_state": ["S", "I"]},
    update_fn=sis_update_factory,
    required_initial=["infected"],
)

SIR = ProcessSpec(
    name="SIR",
    params={"beta": 0.2, "gamma": 0.05},
    state_space={"node_state": ["S", "I", "R"]},
    update_fn=sir_update_factory,
    required_initial=["infected"],
)

RandomWalk = ProcessSpec(
    name="RANDOM_WALK",
    params={"teleport": 0.05},
    state_space={"node_state": ["absent", "present"]},
    update_fn=random_walk_update_factory,
    required_initial=["start_node"],
)


# Process registry
_PROCESS_REGISTRY: Dict[str, ProcessSpec] = {
    "SIS": SIS,
    "SIR": SIR,
    "RANDOM_WALK": RandomWalk,
}


def get_process(name: str) -> ProcessSpec:
    """Get a process specification by name.

    Args:
        name: Process name (case-insensitive)

    Returns:
        ProcessSpec for the requested process

    Raises:
        UnknownProcessError: If process is not found
    """
    from .errors import UnknownProcessError

    name_upper = name.upper()
    if name_upper not in _PROCESS_REGISTRY:
        raise UnknownProcessError(name, list(_PROCESS_REGISTRY.keys()))
    return _PROCESS_REGISTRY[name_upper]


def list_processes() -> List[str]:
    """List all registered process names.

    Returns:
        List of process names
    """
    return list(_PROCESS_REGISTRY.keys())


def register_process(spec: ProcessSpec) -> None:
    """Register a custom process specification.

    Args:
        spec: ProcessSpec to register
    """
    _PROCESS_REGISTRY[spec.name.upper()] = spec

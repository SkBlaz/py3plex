"""Core abstractions for discrete and continuous-time dynamics on multilayer networks.

This module provides base classes for implementing dynamical processes that
complement the existing high-level DSL/builder API in py3plex.dynamics.

The classes here provide a traditional OOP interface for implementing custom
dynamics, while the existing ProcessSpec system provides a declarative approach.
Both approaches can coexist and reference each other.

Key Classes:
    - DynamicsProcess: Base class for discrete-time processes
    - ContinuousTimeProcess: Base class for continuous-time (Gillespie) processes
    - TemporalGraph: Wrapper for time-varying networks
    - TemporalDynamicsProcess: Discrete-time dynamics on temporal networks
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import networkx as nx
import numpy as np


class DynamicsProcess(ABC):
    """Base class for discrete-time dynamical processes on (multi)layer networks.
    
    This class provides the foundation for implementing synchronous discrete-time
    dynamics. Subclasses define the state representation, initialization logic,
    and step-by-step update rules.
    
    The process uses a dedicated RNG for reproducibility and can work with both
    NetworkX graphs and py3plex multilayer network objects.
    
    Attributes:
        graph: The network (NetworkX graph or py3plex multilayer structure)
        params: Model-specific parameters (e.g., infection rate, recovery rate)
        rng: Dedicated random number generator for reproducibility
        seed: Random seed used for initialization
    
    Example:
        >>> class MyProcess(DynamicsProcess):
        ...     def initialize_state(self, seed=None):
        ...         # Initialize node states
        ...         return {node: 0 for node in self.graph.nodes()}
        ...     
        ...     def step(self, state, t):
        ...         # Update logic
        ...         new_state = state.copy()
        ...         # ... perform updates ...
        ...         return new_state
        >>> 
        >>> G = nx.karate_club_graph()
        >>> process = MyProcess(G, seed=42, param1=0.5)
        >>> trajectory = process.run(steps=100)
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        """Initialize the dynamics process.
        
        Args:
            graph: NetworkX graph or py3plex multilayer network structure
            seed: Optional random seed for reproducibility
            **kwargs: Model-specific parameters stored in self.params
        """
        self.graph = graph
        self.params = kwargs
        self.seed = seed
        self.rng = np.random.default_rng(seed)
    
    def set_seed(self, seed: int) -> None:
        """Set or reset the random seed for the process.
        
        This method allows re-seeding the process without creating a new instance.
        
        Args:
            seed: New random seed
        """
        self.seed = seed
        self.rng = np.random.default_rng(seed)
    
    @abstractmethod
    def initialize_state(self, seed: Optional[int] = None) -> Any:
        """Construct and return the initial state for the process.
        
        The state representation is flexible and depends on the specific process:
        - For node-level processes: dict mapping node -> value
        - For multilayer: dict mapping (node, layer) -> value
        - For walkers: current position or list of positions
        
        Args:
            seed: Optional seed to override the instance seed
        
        Returns:
            Initial state in the format expected by step()
        """
        pass
    
    @abstractmethod
    def step(self, state: Any, t: int) -> Any:
        """Perform one synchronous update step.
        
        Given the state at time t, compute and return the state at time t+1.
        This should be a synchronous update over all nodes/entities.
        
        Args:
            state: Current state at time t
            t: Current time step (0-indexed)
        
        Returns:
            New state at time t+1
        """
        pass
    
    def run(
        self,
        steps: int,
        state: Optional[Any] = None,
        record: bool = True,
        callbacks: Optional[List[Callable[[Any, int], None]]] = None,
    ) -> Union[Any, 'DynamicsResult']:
        """Run the dynamics process for a specified number of steps.
        
        Args:
            steps: Number of discrete time steps to simulate
            state: Initial state (if None, calls initialize_state())
            record: If True, return DynamicsResult; if False, return final state only
            callbacks: Optional list of callback functions called after each step
                      with signature callback(state, t)
        
        Returns:
            If record=True: DynamicsResult wrapping the trajectory
            If record=False: final state only
        """
        if state is None:
            state = self.initialize_state()
        
        trajectory = [state] if record else None
        
        for t in range(steps):
            state = self.step(state, t)
            
            if record:
                trajectory.append(state)
            
            if callbacks:
                for callback in callbacks:
                    callback(state, t + 1)
        
        if record:
            metadata = {
                'steps': steps,
                'seed': self.seed,
                'params': self.params,
            }
            return DynamicsResult(trajectory, dynamics=self, metadata=metadata)
        else:
            return state


class ContinuousTimeProcess(ABC):
    """Base class for continuous-time stochastic processes using Gillespie algorithm.
    
    This class implements the kinetic Monte Carlo (Gillespie) approach for
    continuous-time dynamics on networks. The algorithm samples both the time
    increment and the next event according to their propensities (rates).
    
    Subclasses define:
    - State initialization
    - Propensity (rate) computation for all possible events
    - Event application logic
    
    Attributes:
        graph: The network (NetworkX graph or py3plex multilayer structure)
        params: Model-specific parameters
        rng: Dedicated random number generator
        current_time: Current simulation time (continuous)
        seed: Random seed used for initialization
    
    Example:
        >>> class MySISContinuous(ContinuousTimeProcess):
        ...     def initialize_state(self, seed=None):
        ...         # Initialize states
        ...         return {node: 'S' for node in self.graph.nodes()}
        ...     
        ...     def compute_propensities(self, state):
        ...         # Return dict of event -> rate
        ...         propensities = {}
        ...         for node in self.graph.nodes():
        ...             if state[node] == 'I':
        ...                 propensities[('recover', node)] = self.params['mu']
        ...             # ... etc
        ...         return propensities
        ...     
        ...     def apply_event(self, state, event_id):
        ...         event_type, node = event_id
        ...         new_state = state.copy()
        ...         if event_type == 'recover':
        ...             new_state[node] = 'S'
        ...         return new_state
        >>> 
        >>> G = nx.karate_club_graph()
        >>> process = MySISContinuous(G, seed=42, beta=0.5, mu=0.1)
        >>> trajectory = process.run(t_max=10.0)
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        """Initialize the continuous-time process.
        
        Args:
            graph: NetworkX graph or py3plex multilayer network structure
            seed: Optional random seed for reproducibility
            **kwargs: Model-specific parameters stored in self.params
        """
        self.graph = graph
        self.params = kwargs
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.current_time = 0.0
    
    def set_seed(self, seed: int) -> None:
        """Set or reset the random seed for the process.
        
        This method allows re-seeding the process without creating a new instance.
        
        Args:
            seed: New random seed
        """
        self.seed = seed
        self.rng = np.random.default_rng(seed)
    
    @abstractmethod
    def initialize_state(self, seed: Optional[int] = None) -> Any:
        """Construct and return the initial state for the process.
        
        Args:
            seed: Optional seed to override the instance seed
        
        Returns:
            Initial state in the format expected by compute_propensities()
        """
        pass
    
    @abstractmethod
    def compute_propensities(self, state: Any) -> Dict[Any, float]:
        """Compute event rates (propensities) for all possible events.
        
        Returns a mapping from event identifiers to non-negative rates.
        The event identifier can be any hashable object that uniquely
        identifies the event (e.g., tuple of ('infect', node_id)).
        
        Args:
            state: Current state
        
        Returns:
            Dictionary mapping event_id -> rate (non-negative float)
        """
        pass
    
    @abstractmethod
    def apply_event(self, state: Any, event_id: Any) -> Any:
        """Apply the chosen event to the current state.
        
        Args:
            state: Current state
            event_id: Identifier of the event to apply
        
        Returns:
            New state after applying the event
        """
        pass
    
    def step(self, state: Any) -> Tuple[Any, float, Any]:
        """Perform one Gillespie step.
        
        This method:
        1. Computes all propensities
        2. Samples time increment from exponential distribution
        3. Samples an event proportional to its rate
        4. Applies the event
        5. Updates current_time
        
        Args:
            state: Current state
        
        Returns:
            Tuple of (new_state, dt, event_id) where:
            - new_state: State after the event
            - dt: Time increment
            - event_id: The event that occurred
        """
        propensities = self.compute_propensities(state)
        
        if not propensities:
            # No events possible, simulation ends
            return state, float('inf'), None
        
        # Compute total rate
        events = list(propensities.keys())
        rates = np.array([propensities[e] for e in events])
        total_rate = rates.sum()
        
        if total_rate <= 0:
            # No events possible
            return state, float('inf'), None
        
        # Sample time increment
        dt = self.rng.exponential(1.0 / total_rate)
        
        # Sample event proportional to rate
        probs = rates / total_rate
        event_idx = self.rng.choice(len(events), p=probs)
        event_id = events[event_idx]
        
        # Apply event
        new_state = self.apply_event(state, event_id)
        
        # Update time
        self.current_time += dt
        
        return new_state, dt, event_id
    
    def run(
        self,
        t_max: float,
        state: Optional[Any] = None,
        record: bool = True,
        callbacks: Optional[List[Callable[[Any, float], None]]] = None,
    ) -> Union[Tuple[Any, List[float]], Tuple[Any, float]]:
        """Simulate until time >= t_max.
        
        Args:
            t_max: Maximum simulation time
            state: Initial state (if None, calls initialize_state())
            record: If True, return trajectory with times; if False, final state only
            callbacks: Optional list of callback functions called after each event
                      with signature callback(state, current_time)
        
        Returns:
            If record=True: tuple of (trajectory, times) where trajectory is list of states
            If record=False: tuple of (final_state, final_time)
        """
        if state is None:
            state = self.initialize_state()
        
        self.current_time = 0.0
        trajectory = [state] if record else None
        times = [0.0] if record else None
        
        while self.current_time < t_max:
            state, dt, event_id = self.step(state)
            
            if dt == float('inf'):
                # No more events possible
                break
            
            if record:
                trajectory.append(state)
                times.append(self.current_time)
            
            if callbacks:
                for callback in callbacks:
                    callback(state, self.current_time)
        
        if record:
            return trajectory, times
        else:
            return state, self.current_time


class TemporalGraph:
    """Wrapper for time-varying graphs.
    
    Represents a network that changes over time. Can be constructed from:
    - A list of snapshot graphs [G0, G1, ..., GT]
    - A callable function get_graph_at(t) that returns the graph at time t
    
    This abstraction allows dynamics to operate on networks where the structure
    itself evolves over time.
    
    Attributes:
        snapshots: Optional list of graph snapshots (one per time step)
        get_graph_fn: Optional callable that returns graph for given time
    
    Example:
        >>> # From snapshots
        >>> graphs = [nx.erdos_renyi_graph(10, 0.1, seed=t) for t in range(5)]
        >>> temporal = TemporalGraph(snapshots=graphs)
        >>> G_t2 = temporal.get_graph(2)
        >>> 
        >>> # From function
        >>> def get_graph(t):
        ...     p = 0.1 + 0.05 * t  # increasing density
        ...     return nx.erdos_renyi_graph(10, p, seed=t)
        >>> temporal = TemporalGraph(get_graph_fn=get_graph)
        >>> G_t3 = temporal.get_graph(3)
    """
    
    def __init__(
        self,
        snapshots: Optional[List[Any]] = None,
        get_graph_fn: Optional[Callable[[int], Any]] = None,
    ):
        """Initialize temporal graph.
        
        Must provide either snapshots or get_graph_fn, but not both.
        
        Args:
            snapshots: List of graph snapshots (one per time step)
            get_graph_fn: Callable that takes time step and returns graph
        
        Raises:
            ValueError: If neither or both arguments are provided
        """
        if (snapshots is None) == (get_graph_fn is None):
            raise ValueError("Must provide exactly one of snapshots or get_graph_fn")
        
        self.snapshots = snapshots
        self.get_graph_fn = get_graph_fn
    
    def get_graph(self, t: int) -> Any:
        """Get the graph at time step t.
        
        Args:
            t: Time step (0-indexed)
        
        Returns:
            Graph at time t
        
        Raises:
            IndexError: If t is out of bounds for snapshot list
        """
        if self.snapshots is not None:
            return self.snapshots[t]
        else:
            return self.get_graph_fn(t)
    
    def __len__(self) -> int:
        """Return number of snapshots if available.
        
        Returns:
            Number of snapshots, or 0 if using function-based approach
        """
        return len(self.snapshots) if self.snapshots is not None else 0


class TemporalDynamicsProcess(DynamicsProcess):
    """Base class for discrete-time dynamics on temporal networks.
    
    This class extends DynamicsProcess to handle time-varying networks.
    At each time step, the dynamics use the network structure from the
    corresponding temporal snapshot.
    
    The graph attribute is replaced with a TemporalGraph, and the step()
    method receives the appropriate snapshot for each time step.
    
    Attributes:
        graph: TemporalGraph instance
        params: Model-specific parameters
        rng: Dedicated random number generator
        seed: Random seed
    
    Example:
        >>> class TemporalSIS(TemporalDynamicsProcess):
        ...     def initialize_state(self, seed=None):
        ...         G0 = self.graph.get_graph(0)
        ...         return {node: 'S' for node in G0.nodes()}
        ...     
        ...     def step(self, state, t):
        ...         Gt = self.graph.get_graph(t)
        ...         # Perform SIS update using Gt structure
        ...         # ...
        ...         return new_state
    """
    
    def __init__(
        self,
        temporal_graph: TemporalGraph,
        seed: Optional[int] = None,
        **kwargs
    ):
        """Initialize temporal dynamics process.
        
        Args:
            temporal_graph: TemporalGraph instance
            seed: Optional random seed
            **kwargs: Model-specific parameters
        """
        # Store temporal graph as graph attribute for compatibility
        super().__init__(temporal_graph, seed=seed, **kwargs)
    
    @abstractmethod
    def step(self, state: Any, t: int) -> Any:
        """Perform one step using the graph at time t.
        
        Subclasses should call self.graph.get_graph(t) to get the
        appropriate network structure for this time step.
        
        Args:
            state: Current state
            t: Current time step (used to get the right graph snapshot)
        
        Returns:
            New state at time t+1
        """
        pass


class DynamicsResult:
    """Result container for OOP-style dynamics with measure extraction.
    
    This class wraps a trajectory (list of states) and provides convenient
    methods for extracting time series of various measures, matching the API
    described in the py3plex book.
    
    Attributes:
        trajectory: List of states over time
        dynamics: Reference to the dynamics object (optional, for measure computation)
        metadata: Optional dictionary of simulation metadata
    
    Example:
        >>> sir = SIRDynamics(G, beta=0.3, gamma=0.1)
        >>> sir.set_seed(42)
        >>> results = sir.run(steps=100)
        >>> prevalence = results.get_measure("prevalence")
        >>> state_counts = results.get_measure("state_counts")
    """
    
    def __init__(
        self,
        trajectory: List[Any],
        dynamics: Optional[DynamicsProcess] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize DynamicsResult.
        
        Args:
            trajectory: List of states over time
            dynamics: Optional reference to the dynamics object
            metadata: Optional metadata dictionary
        """
        self.trajectory = trajectory
        self.dynamics = dynamics
        self.metadata = metadata or {}
    
    def get_measure(self, measure_name: str) -> Any:
        """Extract a time series measure from the trajectory.
        
        Supported measures:
        - "prevalence": Fraction of nodes in infected state over time (for epidemic models)
        - "state_counts": Dictionary mapping state -> count array over time
        - "trajectory": Raw trajectory (list of states)
        - Custom measures if dynamics object provides a compute_measure method
        
        Args:
            measure_name: Name of the measure to extract
        
        Returns:
            Measure data (typically numpy array or dict of arrays)
        
        Raises:
            ValueError: If measure_name is unknown
        """
        if measure_name == "trajectory":
            return self.trajectory
        
        # Check if dynamics object has a compute_measure method
        if self.dynamics and hasattr(self.dynamics, 'compute_measure'):
            return self.dynamics.compute_measure(measure_name, self.trajectory)
        
        # Try built-in measures based on trajectory structure
        if not self.trajectory:
            raise ValueError("Empty trajectory, cannot compute measures")
        
        first_state = self.trajectory[0]
        
        # For compartmental models (dict of node -> state string)
        if isinstance(first_state, dict):
            if measure_name == "state_counts":
                return self._compute_state_counts()
            elif measure_name == "prevalence":
                return self._compute_prevalence()
            else:
                raise ValueError(
                    f"Unknown measure '{measure_name}'. "
                    f"Available: 'prevalence', 'state_counts', 'trajectory'"
                )
        
        # For other types, delegate to dynamics object if available
        if self.dynamics:
            raise ValueError(
                f"Measure '{measure_name}' not supported for this dynamics type. "
                f"Available: 'trajectory'"
            )
        
        raise ValueError(f"Unknown measure '{measure_name}'")
    
    def _compute_state_counts(self) -> Dict[str, np.ndarray]:
        """Compute counts of each state over time for compartmental models.
        
        Returns:
            Dictionary mapping state name -> array of counts
        """
        # Determine all possible states
        all_states = set()
        for state in self.trajectory:
            all_states.update(state.values())
        
        # Initialize count arrays
        state_counts = {s: np.zeros(len(self.trajectory), dtype=int) for s in all_states}
        
        # Count states at each time step
        for t, state in enumerate(self.trajectory):
            for node_state in state.values():
                state_counts[node_state][t] += 1
        
        return state_counts
    
    def _compute_prevalence(self) -> np.ndarray:
        """Compute prevalence (fraction infected) over time for epidemic models.
        
        Assumes states are 'S', 'I', 'R', 'E', etc. and counts 'I' as infected.
        
        Returns:
            Array of prevalence values over time
        """
        prevalence = np.zeros(len(self.trajectory))
        
        for t, state in enumerate(self.trajectory):
            total = len(state)
            infected = sum(1 for v in state.values() if v == 'I')
            prevalence[t] = infected / total if total > 0 else 0.0
        
        return prevalence
    
    def to_pandas(self):
        """Convert trajectory to pandas DataFrame.
        
        Returns:
            DataFrame with columns [t, node, state] or similar
        
        Raises:
            ImportError: If pandas is not available
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for to_pandas(). "
                "Install with: pip install pandas"
            )
        
        rows = []
        first_state = self.trajectory[0] if self.trajectory else None
        
        if isinstance(first_state, dict):
            # Compartmental model: expand node states
            for t, state in enumerate(self.trajectory):
                for node, node_state in state.items():
                    rows.append({"t": t, "node": node, "state": node_state})
            return pd.DataFrame(rows)
        
        # For other types, just return time series
        return pd.DataFrame({
            "t": list(range(len(self.trajectory))),
            "state": self.trajectory
        })
    
    def __len__(self) -> int:
        """Return length of trajectory."""
        return len(self.trajectory)
    
    def __getitem__(self, index: int) -> Any:
        """Get state at specific time step."""
        return self.trajectory[index]
    
    def __repr__(self) -> str:
        """String representation."""
        return f"DynamicsResult(steps={len(self.trajectory)}, metadata={self.metadata})"

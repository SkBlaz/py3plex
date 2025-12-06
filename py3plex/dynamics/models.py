"""Discrete-time dynamics models for multilayer networks.

This module implements specific discrete-time dynamical processes including:
- Random walks (single and multi-walker)
- Epidemic dynamics (SIS, Adaptive SIS)
- Compartmental models (SIR, SEIR)

These complement the existing high-level ProcessSpec system by providing
traditional OOP interfaces with full control over the dynamics.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np

from .core import DynamicsProcess, TemporalDynamicsProcess
from ._utils import (
    iter_multilayer_nodes,
    iter_multilayer_neighbors,
    count_infected_neighbors,
)


class RandomWalkDynamics(DynamicsProcess):
    """Single-walker discrete-time random walk on a (multi)layer network.
    
    The walker starts at a specified node and at each step either:
    - Stays in place with probability lazy_probability
    - Moves to a uniformly random neighbor with probability (1 - lazy_probability)
    
    For multilayer networks, inter-layer edges are treated as normal edges.
    
    Parameters (via kwargs):
        start_node: Starting node (or None for random start)
        lazy_probability: Probability of staying in place (default: 0.0)
    
    State representation:
        Current position (single node identifier)
    
    Example:
        >>> G = nx.karate_club_graph()
        >>> walk = RandomWalkDynamics(G, seed=42, start_node=0, lazy_probability=0.1)
        >>> trajectory = walk.run(steps=100)
        >>> counts = walk.visit_counts(trajectory)
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        super().__init__(graph, seed=seed, **kwargs)
        self.start_node = kwargs.get('start_node', None)
        self.lazy_probability = kwargs.get('lazy_probability', 0.0)
    
    def initialize_state(self, seed: Optional[int] = None) -> Any:
        """Initialize walker position.
        
        Args:
            seed: Optional seed override
        
        Returns:
            Starting node (current position)
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = self.rng
        
        if self.start_node is not None:
            return self.start_node
        else:
            # Random start - use index to avoid numpy type issues
            nodes = list(iter_multilayer_nodes(self.graph))
            idx = rng.integers(0, len(nodes))
            return nodes[idx]
    
    def step(self, state: Any, t: int) -> Any:
        """Perform one random walk step.
        
        Args:
            state: Current position
            t: Time step
        
        Returns:
            New position
        """
        current_pos = state
        
        # Lazy walk: stay in place with probability
        if self.rng.random() < self.lazy_probability:
            return current_pos
        
        # Get neighbors
        neighbors = list(iter_multilayer_neighbors(self.graph, current_pos))
        
        if not neighbors:
            # No neighbors, stay in place
            return current_pos
        
        # Move to random neighbor - use index to avoid numpy type issues
        idx = self.rng.integers(0, len(neighbors))
        return neighbors[idx]
    
    def visit_counts(self, trajectory: List[Any]) -> Dict[Any, int]:
        """Compute visit counts from a trajectory.
        
        Args:
            trajectory: List of positions from run()
        
        Returns:
            Dictionary mapping node -> visit count
        """
        counts = {}
        for position in trajectory:
            counts[position] = counts.get(position, 0) + 1
        return counts


class MultiRandomWalkDynamics(DynamicsProcess):
    """Multiple independent walkers with optional absorbing states.
    
    Simulates multiple walkers moving independently on the network. Walkers
    can be absorbed (stop moving) when they reach designated absorbing nodes.
    
    Parameters (via kwargs):
        n_walkers: Number of walkers (required)
        init_strategy: 'random' or list of starting positions (default: 'random')
        absorbing_nodes: Set of absorbing node identifiers (default: None)
        allow_coalescence: Whether multiple walkers can occupy same node (default: True)
        lazy_probability: Probability of staying in place (default: 0.0)
    
    State representation:
        List of walker positions (or None for absorbed walkers)
    
    Example:
        >>> G = nx.karate_club_graph()
        >>> walk = MultiRandomWalkDynamics(
        ...     G, seed=42, n_walkers=5, absorbing_nodes={0, 33}
        ... )
        >>> trajectory = walk.run(steps=100)
        >>> stats = walk.hitting_time_statistics(trajectory)
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        super().__init__(graph, seed=seed, **kwargs)
        self.n_walkers = kwargs.get('n_walkers')
        if self.n_walkers is None:
            raise ValueError("n_walkers parameter is required")
        
        self.init_strategy = kwargs.get('init_strategy', 'random')
        self.absorbing_nodes = kwargs.get('absorbing_nodes', set())
        if not isinstance(self.absorbing_nodes, set):
            self.absorbing_nodes = set(self.absorbing_nodes)
        
        self.allow_coalescence = kwargs.get('allow_coalescence', True)
        self.lazy_probability = kwargs.get('lazy_probability', 0.0)
    
    def initialize_state(self, seed: Optional[int] = None) -> List[Any]:
        """Initialize walker positions.
        
        Args:
            seed: Optional seed override
        
        Returns:
            List of starting positions for each walker
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = self.rng
        
        nodes = list(iter_multilayer_nodes(self.graph))
        
        if isinstance(self.init_strategy, list):
            # Explicit starting positions
            return list(self.init_strategy)
        elif self.init_strategy == 'random':
            # Random starting positions - use vectorized approach
            indices = rng.integers(0, len(nodes), size=self.n_walkers)
            return [nodes[i] for i in indices]
        else:
            raise ValueError(f"Unknown init_strategy: {self.init_strategy}")
    
    def step(self, state: List[Any], t: int) -> List[Any]:
        """Perform one step for all walkers.
        
        Args:
            state: List of current positions (None for absorbed walkers)
            t: Time step
        
        Returns:
            List of new positions
        """
        new_state = []
        
        for walker_pos in state:
            if walker_pos is None:
                # Walker already absorbed
                new_state.append(None)
                continue
            
            # Check if walker is on absorbing node
            if walker_pos in self.absorbing_nodes:
                # Absorb walker
                new_state.append(None)
                continue
            
            # Lazy walk
            if self.rng.random() < self.lazy_probability:
                new_state.append(walker_pos)
                continue
            
            # Get neighbors
            neighbors = list(iter_multilayer_neighbors(self.graph, walker_pos))
            
            if not neighbors:
                # No neighbors, stay
                new_state.append(walker_pos)
                continue
            
            # Move to random neighbor - use index to avoid numpy type issues
            idx = self.rng.integers(0, len(neighbors))
            next_pos = neighbors[idx]
            new_state.append(next_pos)
        
        return new_state
    
    def hitting_time_statistics(
        self, trajectory: List[List[Any]]
    ) -> Dict[str, Any]:
        """Compute hitting time statistics for absorbed walkers.
        
        Args:
            trajectory: List of states from run()
        
        Returns:
            Dictionary with:
            - 'hitting_times': List of hitting times for each walker (or None)
            - 'mean': Mean hitting time (excluding non-absorbed)
            - 'std': Standard deviation
            - 'absorbed_count': Number of absorbed walkers
        """
        n_walkers = len(trajectory[0])
        hitting_times = [None] * n_walkers
        
        # Track when each walker gets absorbed
        for t, state in enumerate(trajectory):
            for i, pos in enumerate(state):
                if pos is None and hitting_times[i] is None:
                    hitting_times[i] = t
        
        # Compute statistics
        valid_times = [t for t in hitting_times if t is not None]
        
        if valid_times:
            mean_time = np.mean(valid_times)
            std_time = np.std(valid_times)
        else:
            mean_time = None
            std_time = None
        
        return {
            'hitting_times': hitting_times,
            'mean': mean_time,
            'std': std_time,
            'absorbed_count': len(valid_times),
        }


class SISDynamics(DynamicsProcess):
    """Discrete-time SIS (Susceptible-Infected-Susceptible) epidemic model.
    
    Node states: 'S' (susceptible) or 'I' (infected)
    
    Update rules (synchronous):
    - Infected node recovers (I -> S) with probability mu
    - Susceptible node gets infected (S -> I) with probability 1 - (1 - beta)^k
      where k is the number of infected neighbors
    
    Parameters (via kwargs):
        beta: Infection probability per contact (default: 0.3)
        mu: Recovery probability (default: 0.1)
        initial_infected: Fraction or set of initially infected nodes (default: 0.01)
        backend: 'python', 'numpy', or 'torch' (default: 'python')
    
    State representation:
        Dictionary mapping node -> 'S' or 'I' (or 0/1 for vectorized backends)
    
    Example:
        >>> G = nx.karate_club_graph()
        >>> sis = SISDynamics(G, seed=42, beta=0.3, mu=0.1, initial_infected=0.1)
        >>> trajectory = sis.run(steps=100)
        >>> prevalence_series = sis.run_with_prevalence(steps=100)
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        super().__init__(graph, seed=seed, **kwargs)
        self.beta = kwargs.get('beta', 0.3)
        self.mu = kwargs.get('mu', 0.1)
        self.initial_infected = kwargs.get('initial_infected', 0.01)
        self.backend = kwargs.get('backend', 'python')
        
        # For vectorized backends
        self._adj_matrix = None
        self._node_to_idx = None
        self._idx_to_node = None
    
    def initialize_state(self, seed: Optional[int] = None) -> Any:
        """Initialize SIS state.
        
        Args:
            seed: Optional seed override
        
        Returns:
            State dictionary (or vector for numpy/torch backends)
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = self.rng
        
        nodes = list(iter_multilayer_nodes(self.graph))
        
        # Determine initially infected
        if isinstance(self.initial_infected, (int, float)):
            # Fraction - use index-based selection to avoid numpy type issues
            n_infected = int(len(nodes) * self.initial_infected)
            if n_infected > 0:
                selected_indices = rng.choice(len(nodes), size=n_infected, replace=False)
                infected_nodes = set(nodes[i] for i in selected_indices)
            else:
                infected_nodes = set()
        else:
            # Explicit set
            infected_nodes = set(self.initial_infected)
        
        if self.backend == 'python':
            # Dictionary state
            return {node: 'I' if node in infected_nodes else 'S' for node in nodes}
        else:
            # Vectorized state
            from ._utils import get_adjacency_matrix
            self._adj_matrix, self._node_to_idx = get_adjacency_matrix(self.graph)
            self._idx_to_node = {i: node for node, i in self._node_to_idx.items()}
            
            state = np.zeros(len(nodes), dtype=int)
            for node in infected_nodes:
                if node in self._node_to_idx:
                    state[self._node_to_idx[node]] = 1
            
            if self.backend == 'torch':
                import torch
                return torch.tensor(state, dtype=torch.int32)
            else:
                return state
    
    def step(self, state: Any, t: int) -> Any:
        """Perform one SIS step.
        
        Args:
            state: Current state
            t: Time step
        
        Returns:
            New state
        """
        if self.backend == 'python':
            return self._step_python(state, t)
        elif self.backend == 'numpy':
            return self._step_numpy(state, t)
        elif self.backend == 'torch':
            return self._step_torch(state, t)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    def _step_python(self, state: Dict[Any, str], t: int) -> Dict[Any, str]:
        """Python dict-based step."""
        new_state = {}
        
        for node in state:
            if state[node] == 'I':
                # Recovery
                if self.rng.random() < self.mu:
                    new_state[node] = 'S'
                else:
                    new_state[node] = 'I'
            else:  # 'S'
                # Count infected neighbors
                k = count_infected_neighbors(self.graph, node, state, infected_value='I')
                
                if k > 0:
                    # Infection probability
                    p_infect = 1.0 - (1.0 - self.beta) ** k
                    if self.rng.random() < p_infect:
                        new_state[node] = 'I'
                    else:
                        new_state[node] = 'S'
                else:
                    new_state[node] = 'S'
        
        return new_state
    
    def _step_numpy(self, state: np.ndarray, t: int) -> np.ndarray:
        """NumPy vectorized step."""
        new_state = state.copy()
        
        # Recovery: I -> S with probability mu
        infected = np.where(state == 1)[0]
        recovery_probs = self.rng.random(len(infected))
        recovered = infected[recovery_probs < self.mu]
        new_state[recovered] = 0
        
        # Infection: S -> I based on infected neighbors
        susceptible = np.where(state == 0)[0]
        for s in susceptible:
            # Count infected neighbors
            neighbors = np.where(self._adj_matrix[s] > 0)[0]
            k = np.sum(state[neighbors] == 1)
            
            if k > 0:
                p_infect = 1.0 - (1.0 - self.beta) ** k
                if self.rng.random() < p_infect:
                    new_state[s] = 1
        
        return new_state
    
    def _step_torch(self, state, t: int):
        """PyTorch GPU-accelerated step."""
        try:
            import torch
        except ImportError:
            raise ImportError(
                "PyTorch backend requires torch to be installed. "
                "Install with: pip install torch"
            )
        
        # Convert to numpy, perform step, convert back
        # (For simple SIS, full GPU acceleration is not worth the overhead)
        state_np = state.cpu().numpy()
        new_state_np = self._step_numpy(state_np, t)
        return torch.tensor(new_state_np, dtype=torch.int32, device=state.device)
    
    def prevalence(self, state: Any) -> float:
        """Compute prevalence (fraction of infected nodes).
        
        Args:
            state: Current state
        
        Returns:
            Prevalence in [0, 1]
        """
        if isinstance(state, dict):
            total = len(state)
            infected = sum(1 for v in state.values() if v == 'I')
        elif isinstance(state, np.ndarray):
            total = len(state)
            infected = np.sum(state == 1)
        else:  # torch
            total = len(state)
            infected = int((state == 1).sum())
        
        return infected / total if total > 0 else 0.0
    
    def run_with_prevalence(self, steps: int, **kwargs) -> List[float]:
        """Run simulation and return prevalence time series.
        
        Args:
            steps: Number of steps
            **kwargs: Additional arguments passed to run()
        
        Returns:
            List of prevalence values at each time step
        """
        trajectory = self.run(steps=steps, record=True, **kwargs)
        return [self.prevalence(state) for state in trajectory]


class AdaptiveSISDynamics(SISDynamics):
    """Adaptive SIS model with edge rewiring.
    
    Extends SIS dynamics with co-evolution: susceptible nodes rewire away
    from infected neighbors with probability w per time step.
    
    Parameters (via kwargs):
        beta: Infection probability (default: 0.3)
        mu: Recovery probability (default: 0.1)
        w: Rewiring probability for S-I edges (default: 0.05)
        initial_infected: Fraction or set of initially infected (default: 0.01)
    
    Note:
        Only works with NetworkX graphs (not multilayer networks) for edge manipulation.
        Backend is forced to 'python' since rewiring requires graph modification.
    
    Example:
        >>> G = nx.karate_club_graph()
        >>> adaptive = AdaptiveSISDynamics(G, seed=42, beta=0.3, mu=0.1, w=0.05)
        >>> trajectory = adaptive.run(steps=100)
        >>> edge_counts = adaptive.edge_type_counts(trajectory[-1])
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        # Force python backend for adaptive dynamics
        kwargs['backend'] = 'python'
        super().__init__(graph, seed=seed, **kwargs)
        
        self.w = kwargs.get('w', 0.05)
        
        # Verify we have a mutable NetworkX graph
        if not isinstance(graph, nx.Graph):
            raise TypeError(
                "AdaptiveSISDynamics requires a NetworkX graph for edge rewiring"
            )
    
    def step(self, state: Dict[Any, str], t: int) -> Dict[Any, str]:
        """Perform one adaptive SIS step.
        
        First performs standard SIS update, then performs rewiring.
        
        Args:
            state: Current state
            t: Time step
        
        Returns:
            New state
        """
        # Standard SIS update
        new_state = super()._step_python(state, t)
        
        # Rewiring step: for each S-I edge, rewire with probability w
        edges_to_rewire = []
        
        for u, v in list(self.graph.edges()):
            # Check if this is an S-I edge
            if (new_state[u] == 'S' and new_state[v] == 'I') or \
               (new_state[u] == 'I' and new_state[v] == 'S'):
                if self.rng.random() < self.w:
                    edges_to_rewire.append((u, v))
        
        # Perform rewiring
        for u, v in edges_to_rewire:
            # Identify susceptible node
            s_node = u if new_state[u] == 'S' else v
            i_node = v if new_state[u] == 'S' else u
            
            # Find susceptible nodes to rewire to
            susceptible_nodes = [
                node for node in self.graph.nodes()
                if new_state[node] == 'S' and node != s_node and node != i_node
                and not self.graph.has_edge(s_node, node)
            ]
            
            if susceptible_nodes:
                # Remove S-I edge
                self.graph.remove_edge(u, v)
                
                # Add S-S edge - use index to avoid numpy type issues
                idx = self.rng.integers(0, len(susceptible_nodes))
                target = susceptible_nodes[idx]
                self.graph.add_edge(s_node, target)
        
        return new_state
    
    def edge_type_counts(self, state: Dict[Any, str]) -> Dict[str, int]:
        """Count edges by type (S-S, S-I, I-I).
        
        Args:
            state: Current state
        
        Returns:
            Dictionary with keys 'S-S', 'S-I', 'I-I'
        """
        counts = {'S-S': 0, 'S-I': 0, 'I-I': 0}
        
        for u, v in self.graph.edges():
            u_state = state[u]
            v_state = state[v]
            
            if u_state == 'S' and v_state == 'S':
                counts['S-S'] += 1
            elif u_state == 'I' and v_state == 'I':
                counts['I-I'] += 1
            else:  # One S, one I
                counts['S-I'] += 1
        
        return counts


class TemporalRandomWalk(TemporalDynamicsProcess):
    """Random walk on a temporal network.
    
    The walker can only traverse edges that exist at each time step.
    
    Parameters (via kwargs):
        start_node: Starting node (or None for random start)
        lazy_probability: Probability of staying in place (default: 0.0)
    
    Example:
        >>> graphs = [nx.erdos_renyi_graph(10, 0.2, seed=t) for t in range(100)]
        >>> temporal = TemporalGraph(snapshots=graphs)
        >>> walk = TemporalRandomWalk(temporal, seed=42, start_node=0)
        >>> trajectory = walk.run(steps=50)
    """
    
    def __init__(
        self,
        temporal_graph,
        seed: Optional[int] = None,
        **kwargs
    ):
        super().__init__(temporal_graph, seed=seed, **kwargs)
        self.start_node = kwargs.get('start_node', None)
        self.lazy_probability = kwargs.get('lazy_probability', 0.0)
    
    def initialize_state(self, seed: Optional[int] = None) -> Any:
        """Initialize walker position."""
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = self.rng
        
        if self.start_node is not None:
            return self.start_node
        else:
            # Random start from initial graph - use index to avoid numpy type issues
            G0 = self.graph.get_graph(0)
            nodes = list(G0.nodes())
            idx = rng.integers(0, len(nodes))
            return nodes[idx]
    
    def step(self, state: Any, t: int) -> Any:
        """Perform one step using graph at time t."""
        current_pos = state
        
        # Get graph at current time
        Gt = self.graph.get_graph(t)
        
        # Lazy walk
        if self.rng.random() < self.lazy_probability:
            return current_pos
        
        # Get neighbors in current graph
        if current_pos not in Gt:
            # Node not in graph at this time, stay
            return current_pos
        
        neighbors = list(Gt.neighbors(current_pos))
        
        if not neighbors:
            return current_pos
        
        # Use index to avoid numpy type issues
        idx = self.rng.integers(0, len(neighbors))
        return neighbors[idx]

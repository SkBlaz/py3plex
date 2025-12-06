"""Continuous-time and compartmental dynamics models.

This module implements:
- Continuous-time SIS epidemic (Gillespie algorithm)
- Generic compartmental framework (SIR, SEIR, etc.)
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np

from .core import ContinuousTimeProcess, DynamicsProcess
from ._utils import (
    iter_multilayer_nodes,
    iter_multilayer_neighbors,
    count_infected_neighbors,
)


class SISContinuousTime(ContinuousTimeProcess):
    """Continuous-time SIS model using Gillespie algorithm.
    
    Events:
    - Infection: S + I -> I + I at rate beta per S-I contact
    - Recovery: I -> S at rate mu per infected node
    
    Parameters (via kwargs):
        beta: Infection rate (default: 0.5)
        mu: Recovery rate (default: 0.1)
        initial_infected: Fraction or set of initially infected (default: 0.01)
    
    State representation:
        Dictionary mapping node -> 'S' or 'I'
    
    Example:
        >>> G = nx.karate_club_graph()
        >>> sis = SISContinuousTime(G, seed=42, beta=0.5, mu=0.1)
        >>> trajectory, times = sis.run(t_max=10.0)
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        super().__init__(graph, seed=seed, **kwargs)
        self.beta = kwargs.get('beta', 0.5)
        self.mu = kwargs.get('mu', 0.1)
        self.initial_infected = kwargs.get('initial_infected', 0.01)
    
    def initialize_state(self, seed: Optional[int] = None) -> Dict[Any, str]:
        """Initialize SIS state.
        
        Args:
            seed: Optional seed override
        
        Returns:
            State dictionary mapping node -> 'S' or 'I'
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
            infected_nodes = set(self.initial_infected)
        
        return {node: 'I' if node in infected_nodes else 'S' for node in nodes}
    
    def compute_propensities(
        self, state: Dict[Any, str]
    ) -> Dict[Tuple[str, Any], float]:
        """Compute event propensities.
        
        Args:
            state: Current state
        
        Returns:
            Dictionary mapping event_id -> rate where:
            - ('infect', node): Infection of susceptible node
            - ('recover', node): Recovery of infected node
        """
        propensities = {}
        
        # Recovery events: I -> S
        for node, node_state in state.items():
            if node_state == 'I':
                propensities[('recover', node)] = self.mu
        
        # Infection events: S -> I
        for node, node_state in state.items():
            if node_state == 'S':
                # Count infected neighbors
                k = count_infected_neighbors(self.graph, node, state, infected_value='I')
                if k > 0:
                    # Rate proportional to number of infected neighbors
                    propensities[('infect', node)] = self.beta * k
        
        return propensities
    
    def apply_event(
        self, state: Dict[Any, str], event_id: Tuple[str, Any]
    ) -> Dict[Any, str]:
        """Apply event to state.
        
        Args:
            state: Current state
            event_id: Tuple of (event_type, node)
        
        Returns:
            New state after event
        """
        event_type, node = event_id
        new_state = state.copy()
        
        if event_type == 'infect':
            new_state[node] = 'I'
        elif event_type == 'recover':
            new_state[node] = 'S'
        
        return new_state
    
    def prevalence(self, state: Dict[Any, str]) -> float:
        """Compute prevalence (fraction infected).
        
        Args:
            state: Current state
        
        Returns:
            Prevalence in [0, 1]
        """
        total = len(state)
        infected = sum(1 for v in state.values() if v == 'I')
        return infected / total if total > 0 else 0.0


class CompartmentalDynamics(DynamicsProcess):
    """Generic compartmental model (SIR, SEIR, etc.) on multilayer networks.
    
    Provides a flexible framework for implementing compartmental models with
    arbitrary compartments and transition rules.
    
    Parameters (via kwargs):
        compartments: List of compartment names (e.g., ['S', 'I', 'R'])
        transition_rules: Dictionary defining transitions (see below)
        initial_fractions: Dictionary mapping compartment -> initial fraction
    
    Transition rules format:
        Dictionary mapping compartment -> transition function
        Transition function signature: (node, state, neighbors, rng, params) -> new_compartment
        
        Example for SIR:
        {
            'S': lambda node, state, neighbors, rng, params: 
                'I' if any infection logic else 'S',
            'I': lambda node, state, neighbors, rng, params:
                'R' if rng.random() < params['gamma'] else 'I',
            'R': lambda node, state, neighbors, rng, params: 'R'  # absorbing
        }
    
    State representation:
        Dictionary mapping node -> compartment (string)
    
    Example:
        >>> # See SIRDynamics for a concrete example
        >>> G = nx.karate_club_graph()
        >>> sir = SIRDynamics(G, seed=42, beta=0.3, gamma=0.1)
        >>> trajectory = sir.run(steps=100)
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        super().__init__(graph, seed=seed, **kwargs)
        
        self.compartments = kwargs.get('compartments', [])
        if not self.compartments:
            raise ValueError("Must specify compartments")
        
        self.transition_rules = kwargs.get('transition_rules', {})
        if not self.transition_rules:
            raise ValueError("Must specify transition_rules")
        
        self.initial_fractions = kwargs.get('initial_fractions', {})
    
    def initialize_state(self, seed: Optional[int] = None) -> Dict[Any, str]:
        """Initialize compartmental state.
        
        Args:
            seed: Optional seed override
        
        Returns:
            State dictionary mapping node -> compartment
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = self.rng
        
        nodes = list(iter_multilayer_nodes(self.graph))
        state = {}
        
        # Assign nodes to compartments based on fractions
        remaining_indices = list(range(len(nodes)))
        
        for compartment, fraction in self.initial_fractions.items():
            n = int(len(nodes) * fraction)
            if n > 0 and remaining_indices:
                # Use index-based selection to avoid numpy type issues
                selected_indices = rng.choice(
                    remaining_indices,
                    size=min(n, len(remaining_indices)),
                    replace=False
                )
                for idx in selected_indices:
                    state[nodes[idx]] = compartment
                    remaining_indices.remove(idx)
        
        # Assign remaining nodes to first compartment (typically 'S')
        default_compartment = self.compartments[0]
        for idx in remaining_indices:
            state[nodes[idx]] = default_compartment
        
        return state
    
    def step(self, state: Dict[Any, str], t: int) -> Dict[Any, str]:
        """Perform one synchronous compartmental update.
        
        Args:
            state: Current state
            t: Time step
        
        Returns:
            New state
        """
        new_state = {}
        
        for node in state:
            current_compartment = state[node]
            
            # Get transition rule for current compartment
            if current_compartment not in self.transition_rules:
                # No rule, stay in same compartment
                new_state[node] = current_compartment
                continue
            
            # Get neighbor information
            neighbors = list(iter_multilayer_neighbors(self.graph, node))
            neighbor_states = {n: state[n] for n in neighbors if n in state}
            
            # Count neighbors in each compartment
            neighbor_counts = {comp: 0 for comp in self.compartments}
            for neighbor, neighbor_state in neighbor_states.items():
                neighbor_counts[neighbor_state] += 1
            
            # Apply transition rule
            transition_fn = self.transition_rules[current_compartment]
            new_compartment = transition_fn(
                node, state, neighbor_counts, self.rng, self.params
            )
            
            new_state[node] = new_compartment
        
        return new_state
    
    def compartment_counts(self, state: Dict[Any, str]) -> Dict[str, int]:
        """Count nodes in each compartment.
        
        Args:
            state: Current state
        
        Returns:
            Dictionary mapping compartment -> count
        """
        counts = {comp: 0 for comp in self.compartments}
        for compartment in state.values():
            if compartment in counts:
                counts[compartment] += 1
        return counts


class SIRDynamics(CompartmentalDynamics):
    """Discrete-time SIR (Susceptible-Infected-Recovered) model.
    
    Node states: 'S', 'I', 'R'
    
    Update rules:
    - Infected node recovers (I -> R) with probability gamma
    - Susceptible node gets infected (S -> I) with probability 1 - (1 - beta)^k
      where k is the number of infected neighbors
    - Recovered nodes stay recovered (absorbing state)
    
    Parameters (via kwargs):
        beta: Infection probability per contact (default: 0.2)
        gamma: Recovery probability (default: 0.05)
        initial_infected: Fraction of initially infected (default: 0.01)
    
    Example:
        >>> G = nx.karate_club_graph()
        >>> sir = SIRDynamics(G, seed=42, beta=0.3, gamma=0.1)
        >>> trajectory = sir.run(steps=100)
        >>> counts = sir.compartment_counts(trajectory[-1])
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        self.beta = kwargs.get('beta', 0.2)
        self.gamma = kwargs.get('gamma', 0.05)
        initial_infected = kwargs.get('initial_infected', 0.01)
        
        # Define SIR transition rules
        def transition_S(node, state, neighbor_counts, rng, params):
            k = neighbor_counts['I']
            if k > 0:
                p_infect = 1.0 - (1.0 - params['beta']) ** k
                if rng.random() < p_infect:
                    return 'I'
            return 'S'
        
        def transition_I(node, state, neighbor_counts, rng, params):
            if rng.random() < params['gamma']:
                return 'R'
            return 'I'
        
        def transition_R(node, state, neighbor_counts, rng, params):
            return 'R'  # Absorbing state
        
        kwargs['compartments'] = ['S', 'I', 'R']
        kwargs['transition_rules'] = {
            'S': transition_S,
            'I': transition_I,
            'R': transition_R,
        }
        kwargs['initial_fractions'] = {
            'I': initial_infected,
            'S': 1.0 - initial_infected,
        }
        kwargs['beta'] = self.beta
        kwargs['gamma'] = self.gamma
        
        super().__init__(graph, seed=seed, **kwargs)


class SEIRDynamics(CompartmentalDynamics):
    """Discrete-time SEIR (Susceptible-Exposed-Infected-Recovered) model.
    
    Node states: 'S', 'E', 'I', 'R'
    
    Update rules:
    - Susceptible becomes exposed (S -> E) with probability 1 - (1 - beta)^k
    - Exposed becomes infected (E -> I) with probability sigma
    - Infected recovers (I -> R) with probability gamma
    - Recovered stays recovered (absorbing state)
    
    Parameters (via kwargs):
        beta: Infection probability per contact (default: 0.2)
        sigma: Rate of progression from exposed to infected (default: 0.2)
        gamma: Recovery probability (default: 0.05)
        initial_infected: Fraction of initially infected (default: 0.01)
    
    Example:
        >>> G = nx.karate_club_graph()
        >>> seir = SEIRDynamics(G, seed=42, beta=0.3, sigma=0.2, gamma=0.1)
        >>> trajectory = seir.run(steps=100)
        >>> counts = seir.compartment_counts(trajectory[-1])
    """
    
    def __init__(self, graph: Any, seed: Optional[int] = None, **kwargs):
        self.beta = kwargs.get('beta', 0.2)
        self.sigma = kwargs.get('sigma', 0.2)
        self.gamma = kwargs.get('gamma', 0.05)
        initial_infected = kwargs.get('initial_infected', 0.01)
        
        # Define SEIR transition rules
        def transition_S(node, state, neighbor_counts, rng, params):
            k = neighbor_counts['I']
            if k > 0:
                p_infect = 1.0 - (1.0 - params['beta']) ** k
                if rng.random() < p_infect:
                    return 'E'
            return 'S'
        
        def transition_E(node, state, neighbor_counts, rng, params):
            if rng.random() < params['sigma']:
                return 'I'
            return 'E'
        
        def transition_I(node, state, neighbor_counts, rng, params):
            if rng.random() < params['gamma']:
                return 'R'
            return 'I'
        
        def transition_R(node, state, neighbor_counts, rng, params):
            return 'R'  # Absorbing state
        
        kwargs['compartments'] = ['S', 'E', 'I', 'R']
        kwargs['transition_rules'] = {
            'S': transition_S,
            'E': transition_E,
            'I': transition_I,
            'R': transition_R,
        }
        kwargs['initial_fractions'] = {
            'I': initial_infected,
            'S': 1.0 - initial_infected,
        }
        kwargs['beta'] = self.beta
        kwargs['sigma'] = self.sigma
        kwargs['gamma'] = self.gamma
        
        super().__init__(graph, seed=seed, **kwargs)

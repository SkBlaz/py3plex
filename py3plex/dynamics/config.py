"""Configuration-based dynamics specification.

This module provides a simple way to define compartmental dynamics from
configuration dictionaries, allowing users to specify dynamics without
writing Python code.

Example config:
    {
        "type": "compartmental",
        "compartments": ["S", "I"],
        "parameters": {"beta": 0.3, "mu": 0.1},
        "rules": {
            "S": "infected_neighbors > 0 ? p=1-(1-beta)**infected_neighbors -> I : stay",
            "I": "p=mu -> S : stay"
        },
        "initial": {"I": 0.01}
    }
"""

import re
from typing import Any, Callable, Dict

from .compartmental import CompartmentalDynamics


def build_dynamics_from_config(graph: Any, config: dict) -> CompartmentalDynamics:
    """Build a CompartmentalDynamics from a configuration dictionary.
    
    The configuration should have:
    - type: "compartmental" (currently only compartmental supported)
    - compartments: List of compartment names (e.g., ["S", "I", "R"])
    - parameters: Dictionary of parameter values (e.g., {"beta": 0.3})
    - rules: Dictionary mapping compartment -> rule string
    - initial: Dictionary mapping compartment -> initial fraction
    
    Rule syntax (simplified):
        "condition ? p=probability -> target : default"
        - condition: e.g., "infected_neighbors > 0"
        - probability: expression using parameters
        - target: target compartment
        - default: "stay" to remain in current compartment
    
    Supported conditions:
        - "infected_neighbors > 0" (or other compartment names)
        - "exposed_neighbors > 0"
        - etc.
    
    Args:
        graph: NetworkX graph or py3plex multilayer network
        config: Configuration dictionary
    
    Returns:
        CompartmentalDynamics instance
    
    Raises:
        ValueError: For unsupported config format or parse errors
    
    Example:
        >>> config = {
        ...     "type": "compartmental",
        ...     "compartments": ["S", "I"],
        ...     "parameters": {"beta": 0.3, "mu": 0.1},
        ...     "rules": {
        ...         "S": "infected_neighbors > 0 ? p=1-(1-beta)**infected_neighbors -> I : stay",
        ...         "I": "p=mu -> S : stay"
        ...     },
        ...     "initial": {"I": 0.01}
        ... }
        >>> dynamics = build_dynamics_from_config(G, config)
        >>> trajectory = dynamics.run(steps=100)
    """
    config_type = config.get('type', 'compartmental')
    
    if config_type != 'compartmental':
        raise ValueError(f"Unsupported dynamics type: {config_type}")
    
    compartments = config.get('compartments', [])
    if not compartments:
        raise ValueError("Config must specify compartments")
    
    parameters = config.get('parameters', {})
    rules_config = config.get('rules', {})
    initial_fractions = config.get('initial', {})
    
    # Parse rules
    transition_rules = {}
    for compartment, rule_str in rules_config.items():
        transition_rules[compartment] = _parse_rule(rule_str, compartments, parameters)
    
    # Build dynamics
    return CompartmentalDynamics(
        graph,
        compartments=compartments,
        transition_rules=transition_rules,
        initial_fractions=initial_fractions,
        **parameters
    )


def _parse_rule(
    rule_str: str,
    compartments: list,
    parameters: dict
) -> Callable:
    """Parse a rule string into a transition function.
    
    Args:
        rule_str: Rule string (e.g., "p=mu -> S : stay")
        compartments: List of compartment names
        parameters: Parameter dictionary
    
    Returns:
        Transition function with signature:
        (node, state, neighbor_counts, rng, params) -> new_compartment
    """
    rule_str = rule_str.strip()
    
    # Check for conditional format: "condition ? action : default"
    if '?' in rule_str:
        parts = rule_str.split('?')
        condition_str = parts[0].strip()
        rest = parts[1].strip()
        
        if ':' in rest:
            action_str, default_str = rest.split(':')
            action_str = action_str.strip()
            default_str = default_str.strip()
        else:
            action_str = rest
            default_str = 'stay'
        
        # Parse condition
        condition_fn = _parse_condition(condition_str, compartments)
        
        # Parse action
        action_fn = _parse_action(action_str, compartments, parameters)
        
        # Parse default
        default_fn = _parse_action(default_str, compartments, parameters)
        
        def transition(node, state, neighbor_counts, rng, params):
            if condition_fn(neighbor_counts):
                return action_fn(node, state, neighbor_counts, rng, params)
            else:
                return default_fn(node, state, neighbor_counts, rng, params)
        
        return transition
    
    else:
        # Simple action without condition
        return _parse_action(rule_str, compartments, parameters)


def _parse_condition(condition_str: str, compartments: list) -> Callable:
    """Parse a condition string.
    
    Supports: "<compartment>_neighbors > 0" or similar
    
    Args:
        condition_str: Condition string
        compartments: List of compartment names
    
    Returns:
        Function that takes neighbor_counts and returns bool
    """
    condition_str = condition_str.strip()
    
    # Pattern: "<compartment>_neighbors <op> <value>"
    pattern = r'(\w+)_neighbors\s*([><=!]+)\s*(\d+)'
    match = re.match(pattern, condition_str)
    
    if match:
        compartment = match.group(1).upper()
        operator = match.group(2)
        value = int(match.group(3))
        
        # Map compartment name (e.g., "infected" -> "I")
        comp_map = {
            'infected': 'I',
            'susceptible': 'S',
            'exposed': 'E',
            'recovered': 'R',
        }
        compartment = comp_map.get(compartment.lower(), compartment.upper())
        
        if operator == '>':
            return lambda nc: nc.get(compartment, 0) > value
        elif operator == '>=':
            return lambda nc: nc.get(compartment, 0) >= value
        elif operator == '<':
            return lambda nc: nc.get(compartment, 0) < value
        elif operator == '<=':
            return lambda nc: nc.get(compartment, 0) <= value
        elif operator == '==' or operator == '=':
            return lambda nc: nc.get(compartment, 0) == value
        elif operator == '!=':
            return lambda nc: nc.get(compartment, 0) != value
    
    # Default: always true
    return lambda nc: True


def _parse_action(
    action_str: str,
    compartments: list,
    parameters: dict
) -> Callable:
    """Parse an action string.
    
    Formats:
    - "stay": stay in current compartment
    - "-> X": always transition to X
    - "p=expr -> X": transition to X with probability expr
    
    Note: This function should not receive strings with ':' - those should
    be handled at the _parse_rule level.
    
    Args:
        action_str: Action string (without ':' conditional syntax)
        compartments: List of compartment names
        parameters: Parameter dictionary
    
    Returns:
        Function that takes (node, state, neighbor_counts, rng, params) and returns compartment
    """
    action_str = action_str.strip()
    
    if action_str.lower() == 'stay':
        # Stay in current compartment
        return lambda node, state, nc, rng, params: state[node]
    
    # Check for probabilistic transition: "p=expr -> X"
    if 'p=' in action_str and '->' in action_str:
        # Split on -> to separate probability from target
        arrow_idx = action_str.index('->')
        prob_part = action_str[:arrow_idx].strip()
        target_part = action_str[arrow_idx+2:].strip()
        
        if not target_part:
            raise ValueError(f"Invalid action format: {action_str}")
        
        # Extract probability expression
        prob_expr = prob_part.split('p=')[1].strip()
        
        # Parse target compartment
        target = _parse_target(target_part, compartments)
        
        def transition(node, state, neighbor_counts, rng, params):
            # Evaluate probability expression
            prob = _evaluate_expression(prob_expr, neighbor_counts, params)
            
            if rng.random() < prob:
                return target
            else:
                return state[node]
        
        return transition
    
    # Simple deterministic transition: "-> X"
    if '->' in action_str:
        target_part = action_str.split('->')[1].strip()
        target = _parse_target(target_part, compartments)
        return lambda node, state, nc, rng, params: target
    
    # Default: stay
    return lambda node, state, nc, rng, params: state[node]


def _parse_target(target_str: str, compartments: list) -> str:
    """Parse target compartment.
    
    Args:
        target_str: Target compartment string
        compartments: List of valid compartments
    
    Returns:
        Compartment name
    """
    target = target_str.strip().upper()
    
    # Map common names to compartments
    comp_map = {
        'INFECTED': 'I',
        'SUSCEPTIBLE': 'S',
        'EXPOSED': 'E',
        'RECOVERED': 'R',
    }
    
    return comp_map.get(target, target)


def _evaluate_expression(
    expr: str,
    neighbor_counts: dict,
    params: dict
) -> float:
    """Safely evaluate a simple arithmetic expression.
    
    Supports:
    - Parameter names (e.g., "beta", "mu")
    - Neighbor counts (e.g., "infected_neighbors")
    - Basic arithmetic: +, -, *, /, **, ()
    - Functions: exp, log (not implemented for safety)
    
    Args:
        expr: Expression string
        neighbor_counts: Dictionary of neighbor counts
        params: Parameter dictionary
    
    Returns:
        Evaluated float value
    
    Note:
        This is a simplified safe evaluator. For production use,
        consider using a proper expression parser library.
    """
    # Replace parameter names with values
    safe_expr = expr
    
    # Replace neighbor count references
    # e.g., "infected_neighbors" -> value
    comp_map = {
        'infected_neighbors': neighbor_counts.get('I', 0),
        'susceptible_neighbors': neighbor_counts.get('S', 0),
        'exposed_neighbors': neighbor_counts.get('E', 0),
        'recovered_neighbors': neighbor_counts.get('R', 0),
    }
    
    for name, value in comp_map.items():
        safe_expr = safe_expr.replace(name, str(value))
    
    # Replace parameter names
    for param_name, param_value in params.items():
        safe_expr = safe_expr.replace(param_name, str(param_value))
    
    # Validate expression only contains safe characters
    # Allow scientific notation produced by float stringification (e.g., "1e-06").
    allowed_chars = set('0123456789.+-*/() eE')
    if not all(c in allowed_chars for c in safe_expr):
        raise ValueError(f"Unsafe expression: {expr}")
    
    try:
        # Evaluate using Python's eval with very restricted namespace
        # Only allow basic arithmetic operations
        allowed_names = {
            '__builtins__': {},
            # Allow only safe math operations
        }
        result = eval(safe_expr, allowed_names, {})
        return float(result)
    except (SyntaxError, ValueError, NameError, TypeError) as e:
        raise ValueError(f"Failed to evaluate expression '{expr}': {e}")
    except Exception as e:
        # Catch any other exceptions for safety
        raise ValueError(f"Unsafe or invalid expression '{expr}': {e}")

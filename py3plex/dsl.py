"""SQL-like DSL for Multilayer Network Queries.

This module provides a Domain-Specific Language (DSL) for querying and analyzing
multilayer networks using SQL-like syntax. The DSL supports filtering nodes and edges
based on various network properties and computing analytical measures.

Example Usage:
    >>> from py3plex.core import multinet
    >>> from py3plex.dsl import execute_query
    >>> 
    >>> # Create a multilayer network
    >>> network = multinet.multi_layer_network()
    >>> # ... add nodes and edges ...
    >>> 
    >>> # Query nodes with high degree in a specific layer
    >>> result = execute_query(network, 'SELECT nodes WHERE layer="transport" AND degree > 5')
    >>> 
    >>> # Compute centrality for filtered nodes
    >>> result = execute_query(network, 'SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality')

Supported Operations:
    - SELECT: Choose what to select (nodes, edges)
    - WHERE: Filter by conditions (layer, degree, centrality, etc.)
    - AND/OR/NOT: Logical operators for combining conditions
    - COMPUTE: Calculate network measures (degree, centrality, etc.)
    - Comparison operators: >, <, =, >=, <=, !=

See examples/network_analysis/example_dsl_queries.py for more examples.
"""

import re
import networkx as nx
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from py3plex.logging_config import get_logger

logger = get_logger(__name__)


class DSLSyntaxError(Exception):
    """Exception raised for DSL syntax errors."""
    pass


class DSLExecutionError(Exception):
    """Exception raised for DSL execution errors."""
    pass


def _tokenize_query(query: str) -> List[str]:
    """Tokenize a DSL query into components.
    
    Args:
        query: DSL query string
        
    Returns:
        List of tokens
        
    Examples:
        >>> _tokenize_query('SELECT nodes WHERE layer="transport"')
        ['SELECT', 'nodes', 'WHERE', 'layer', '=', 'transport']
    """
    # Replace quoted strings with placeholders to preserve them
    string_pattern = r'"[^"]*"|\'[^\']*\''
    strings = re.findall(string_pattern, query)
    placeholders = {}
    
    for i, s in enumerate(strings):
        placeholder = f"__STRING_{i}__"
        placeholders[placeholder] = s.strip('"\'')
        query = query.replace(s, placeholder, 1)
    
    # Define token patterns
    patterns = [
        r'>=|<=|!=|>|<|=',  # Comparison operators
        r'\bAND\b|\bOR\b|\bNOT\b',  # Logical operators
        r'\bSELECT\b|\bWHERE\b|\bCOMPUTE\b',  # Keywords
        r'\bnodes\b|\bedges\b',  # Selection targets
        r'__STRING_\d+__|[a-zA-Z_][a-zA-Z0-9_]*',  # Identifiers and placeholders
        r'\d+\.?\d*',  # Numbers
    ]
    
    combined_pattern = '|'.join(f'({p})' for p in patterns)
    tokens = []
    
    for match in re.finditer(combined_pattern, query, re.IGNORECASE):
        token = match.group(0)
        # Replace placeholders back with actual strings
        if token.startswith('__STRING_'):
            token = placeholders[token]
        tokens.append(token)
    
    return tokens


def _parse_condition(tokens: List[str], start_idx: int) -> Tuple[Dict[str, Any], int]:
    """Parse a single condition from tokens.
    
    Args:
        tokens: List of tokens
        start_idx: Starting index in tokens
        
    Returns:
        Tuple of (condition_dict, next_index)
        
    Raises:
        DSLSyntaxError: If condition syntax is invalid
    """
    if start_idx >= len(tokens):
        raise DSLSyntaxError("Unexpected end of query while parsing condition")
    
    # Handle NOT operator
    is_negated = False
    idx = start_idx
    if idx < len(tokens) and tokens[idx].upper() == 'NOT':
        is_negated = True
        idx += 1
    
    if idx >= len(tokens):
        raise DSLSyntaxError("Expected attribute after NOT")
    
    attribute = tokens[idx]
    idx += 1
    
    if idx >= len(tokens):
        raise DSLSyntaxError(f"Expected operator after attribute '{attribute}'")
    
    operator = tokens[idx]
    idx += 1
    
    if idx >= len(tokens):
        raise DSLSyntaxError(f"Expected value after operator '{operator}'")
    
    value = tokens[idx]
    idx += 1
    
    # Convert value to appropriate type
    try:
        if '.' in value:
            value = float(value)
        else:
            try:
                value = int(value)
            except ValueError:
                pass  # Keep as string
    except ValueError:
        pass  # Keep as string
    
    condition = {
        'attribute': attribute,
        'operator': operator,
        'value': value,
        'negated': is_negated
    }
    
    return condition, idx


def _parse_where_clause(tokens: List[str], where_idx: int) -> List[Dict[str, Any]]:
    """Parse WHERE clause into a list of conditions.
    
    Args:
        tokens: List of tokens
        where_idx: Index of WHERE keyword
        
    Returns:
        List of condition dictionaries with logical operators
        
    Raises:
        DSLSyntaxError: If WHERE clause syntax is invalid
    """
    conditions = []
    idx = where_idx + 1
    
    while idx < len(tokens):
        token = tokens[idx]
        
        # Stop at COMPUTE keyword
        if token.upper() == 'COMPUTE':
            break
        
        # Handle logical operators
        if token.upper() in ['AND', 'OR']:
            if not conditions:
                raise DSLSyntaxError(f"Unexpected '{token}' at start of WHERE clause")
            conditions[-1]['logical_op'] = token.upper()
            idx += 1
            continue
        
        # Parse condition
        condition, next_idx = _parse_condition(tokens, idx)
        conditions.append(condition)
        idx = next_idx
    
    return conditions


def _evaluate_condition(node_or_edge: Any, condition: Dict[str, Any], 
                        network: Any, context: Dict[str, Any]) -> bool:
    """Evaluate a single condition against a node or edge.
    
    Args:
        node_or_edge: Node tuple (node_id, layer) or edge tuple
        condition: Condition dictionary
        network: Multilayer network object
        context: Context dictionary with computed values
        
    Returns:
        Boolean result of condition evaluation
    """
    attribute = condition['attribute']
    operator = condition['operator']
    expected_value = condition['value']
    is_negated = condition.get('negated', False)
    
    # Extract node attributes
    if isinstance(node_or_edge, tuple) and len(node_or_edge) >= 2:
        node_id, layer = node_or_edge[0], node_or_edge[1]
    else:
        # For edges
        return False
    
    # Get actual value based on attribute
    actual_value = None
    
    if attribute == 'layer':
        actual_value = str(layer)
    
    elif attribute == 'degree':
        # Get degree from NetworkX
        if hasattr(network, 'core_network') and network.core_network:
            actual_value = network.core_network.degree(node_or_edge)
        else:
            actual_value = 0
    
    elif attribute in ['betweenness', 'betweenness_centrality']:
        # Use cached centrality if available
        if 'betweenness_centrality' in context:
            actual_value = context['betweenness_centrality'].get(node_or_edge, 0)
        else:
            actual_value = 0
    
    elif attribute in ['closeness', 'closeness_centrality']:
        if 'closeness_centrality' in context:
            actual_value = context['closeness_centrality'].get(node_or_edge, 0)
        else:
            actual_value = 0
    
    elif attribute in ['eigenvector', 'eigenvector_centrality']:
        if 'eigenvector_centrality' in context:
            actual_value = context['eigenvector_centrality'].get(node_or_edge, 0)
        else:
            actual_value = 0
    
    else:
        # Try to get from node attributes
        if hasattr(network, 'core_network') and network.core_network:
            node_data = network.core_network.nodes.get(node_or_edge, {})
            actual_value = node_data.get(attribute)
        else:
            actual_value = None
    
    # Evaluate comparison
    if actual_value is None:
        result = False
    elif operator == '=':
        result = str(actual_value) == str(expected_value)
    elif operator == '!=':
        result = str(actual_value) != str(expected_value)
    elif operator == '>':
        try:
            result = float(actual_value) > float(expected_value)
        except (ValueError, TypeError):
            result = False
    elif operator == '<':
        try:
            result = float(actual_value) < float(expected_value)
        except (ValueError, TypeError):
            result = False
    elif operator == '>=':
        try:
            result = float(actual_value) >= float(expected_value)
        except (ValueError, TypeError):
            result = False
    elif operator == '<=':
        try:
            result = float(actual_value) <= float(expected_value)
        except (ValueError, TypeError):
            result = False
    else:
        raise DSLSyntaxError(f"Unknown operator: {operator}")
    
    # Apply negation if needed
    if is_negated:
        result = not result
    
    return result


def _evaluate_conditions(node_or_edge: Any, conditions: List[Dict[str, Any]], 
                         network: Any, context: Dict[str, Any]) -> bool:
    """Evaluate all conditions with logical operators.
    
    Args:
        node_or_edge: Node or edge to evaluate
        conditions: List of conditions with logical operators
        network: Multilayer network object
        context: Context dictionary
        
    Returns:
        Boolean result of all conditions
    """
    if not conditions:
        return True
    
    result = _evaluate_condition(node_or_edge, conditions[0], network, context)
    
    for condition in conditions[1:]:
        logical_op = conditions[conditions.index(condition) - 1].get('logical_op', 'AND')
        current_result = _evaluate_condition(node_or_edge, condition, network, context)
        
        if logical_op == 'AND':
            result = result and current_result
        elif logical_op == 'OR':
            result = result or current_result
    
    return result


def _compute_measure(network: Any, measure: str, nodes: Optional[List] = None) -> Dict[Any, float]:
    """Compute a network measure for nodes.
    
    Args:
        network: Multilayer network object
        measure: Name of measure to compute (e.g., 'degree', 'betweenness_centrality')
        nodes: Optional list of nodes to compute for (None = all nodes)
        
    Returns:
        Dictionary mapping nodes to measure values
        
    Raises:
        DSLExecutionError: If measure cannot be computed
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise DSLExecutionError("Network has no core_network to compute measures on")
    
    G = network.core_network
    
    # Create subgraph if nodes are specified
    if nodes is not None:
        G = G.subgraph(nodes).copy()
    
    # Map measure names to NetworkX functions
    measure_map = {
        'degree': lambda g: dict(g.degree()),
        'degree_centrality': nx.degree_centrality,
        'betweenness_centrality': nx.betweenness_centrality,
        'closeness_centrality': nx.closeness_centrality,
        'eigenvector_centrality': lambda g: nx.eigenvector_centrality(g, max_iter=1000),
        'pagerank': nx.pagerank,
        'clustering': nx.clustering,
        'betweenness': nx.betweenness_centrality,
        'closeness': nx.closeness_centrality,
        'eigenvector': lambda g: nx.eigenvector_centrality(g, max_iter=1000),
    }
    
    if measure not in measure_map:
        raise DSLExecutionError(f"Unknown measure: {measure}. Supported measures: {list(measure_map.keys())}")
    
    try:
        func = measure_map[measure]
        result = func(G)
        return result
    except Exception as e:
        raise DSLExecutionError(f"Error computing {measure}: {str(e)}")


def execute_query(network: Any, query: str) -> Dict[str, Any]:
    """Execute a DSL query on a multilayer network.
    
    Args:
        network: Multilayer network object (multi_layer_network instance)
        query: DSL query string
        
    Returns:
        Dictionary containing:
            - 'nodes' or 'edges': List of selected items
            - 'computed': Dictionary of computed measures (if COMPUTE used)
            - 'query': Original query string
            
    Raises:
        DSLSyntaxError: If query syntax is invalid
        DSLExecutionError: If query cannot be executed
        
    Examples:
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network()
        >>> net.add_nodes([{'source': 'A', 'type': 'transport'}])
        >>> net.add_nodes([{'source': 'B', 'type': 'transport'}])
        >>> net.add_nodes([{'source': 'C', 'type': 'social'}])
        >>> net.add_edges([
        ...     {'source': 'A', 'target': 'B', 'source_type': 'transport', 'target_type': 'transport'},
        ...     {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'}
        ... ])
        >>> 
        >>> # Select all nodes in "transport" layer
        >>> result = execute_query(net, 'SELECT nodes WHERE layer="transport"')
        >>> result['count'] >= 0
        True
        >>> 
        >>> # Select high-degree nodes and compute centrality
        >>> result = execute_query(net, 'SELECT nodes WHERE degree > 0 COMPUTE betweenness_centrality')
        >>> 'computed' in result
        True
        >>> 
        >>> # Complex query with multiple conditions
        >>> result = execute_query(net, 'SELECT nodes WHERE layer="social" AND degree >= 0')
        >>> result['count'] >= 0
        True
    """
    logger.info(f"Executing DSL query: {query}")
    
    # Tokenize query
    tokens = _tokenize_query(query)
    
    if not tokens:
        raise DSLSyntaxError("Empty query")
    
    # Parse SELECT clause
    if tokens[0].upper() != 'SELECT':
        raise DSLSyntaxError("Query must start with SELECT")
    
    if len(tokens) < 2:
        raise DSLSyntaxError("SELECT requires a target (nodes or edges)")
    
    target = tokens[1].lower()
    if target not in ['nodes', 'edges']:
        raise DSLSyntaxError(f"Invalid SELECT target: {target}. Must be 'nodes' or 'edges'")
    
    # Find WHERE and COMPUTE clauses
    where_idx = None
    compute_idx = None
    
    for i, token in enumerate(tokens):
        if token.upper() == 'WHERE':
            where_idx = i
        elif token.upper() == 'COMPUTE':
            compute_idx = i
    
    # Parse WHERE conditions
    conditions = []
    if where_idx is not None:
        conditions = _parse_where_clause(tokens, where_idx)
    
    # Parse COMPUTE measures
    measures = []
    if compute_idx is not None:
        measures = tokens[compute_idx + 1:]
    
    # Execute query
    result = {
        'query': query,
        'target': target,
    }
    
    # Get all nodes or edges
    if target == 'nodes':
        if not hasattr(network, 'core_network') or network.core_network is None:
            all_items = []
        else:
            all_items = list(network.get_nodes())
    else:
        if not hasattr(network, 'core_network') or network.core_network is None:
            all_items = []
        else:
            all_items = list(network.get_edges())
    
    # Pre-compute centrality measures if needed in conditions
    context = {}
    for condition in conditions:
        attr = condition['attribute']
        if attr in ['betweenness', 'betweenness_centrality', 'closeness', 'closeness_centrality',
                   'eigenvector', 'eigenvector_centrality']:
            measure_name = attr if '_centrality' in attr else f"{attr}_centrality"
            if measure_name not in context:
                try:
                    context[measure_name] = _compute_measure(network, measure_name)
                except DSLExecutionError:
                    logger.warning(f"Could not pre-compute {measure_name}")
    
    # Filter items based on conditions
    if conditions:
        filtered_items = [
            item for item in all_items
            if _evaluate_conditions(item, conditions, network, context)
        ]
    else:
        filtered_items = all_items
    
    result[target] = filtered_items
    result['count'] = len(filtered_items)
    
    # Compute measures if requested
    if measures and target == 'nodes':
        result['computed'] = {}
        for measure in measures:
            try:
                computed_values = _compute_measure(network, measure, filtered_items)
                result['computed'][measure] = computed_values
            except DSLExecutionError as e:
                logger.error(f"Error computing {measure}: {e}")
                result['computed'][measure] = {}
    
    logger.info(f"Query returned {result['count']} {target}")
    return result


def format_result(result: Dict[str, Any], limit: int = 10) -> str:
    """Format query result as human-readable string.
    
    Args:
        result: Result dictionary from execute_query
        limit: Maximum number of items to display
        
    Returns:
        Formatted string representation
    """
    output = []
    output.append(f"Query: {result['query']}")
    output.append(f"Target: {result['target']}")
    output.append(f"Count: {result['count']}")
    output.append("")
    
    if result['count'] > 0:
        target = result['target']
        items = result[target][:limit]
        
        output.append(f"{target.capitalize()} (showing {len(items)} of {result['count']}):")
        for item in items:
            output.append(f"  {item}")
        
        if result['count'] > limit:
            output.append(f"  ... and {result['count'] - limit} more")
    
    if 'computed' in result and result['computed']:
        output.append("")
        output.append("Computed measures:")
        for measure, values in result['computed'].items():
            output.append(f"  {measure}:")
            sorted_values = sorted(values.items(), key=lambda x: x[1], reverse=True)[:limit]
            for node, value in sorted_values:
                output.append(f"    {node}: {value:.4f}")
            if len(values) > limit:
                output.append(f"    ... and {len(values) - limit} more")
    
    return "\n".join(output)


# Convenience functions for common queries

def select_nodes_by_layer(network: Any, layer: str) -> List[Any]:
    """Select all nodes in a specific layer.
    
    Args:
        network: Multilayer network object
        layer: Layer identifier
        
    Returns:
        List of nodes in the specified layer
    """
    result = execute_query(network, f'SELECT nodes WHERE layer="{layer}"')
    return result['nodes']


def select_high_degree_nodes(network: Any, min_degree: int, layer: Optional[str] = None) -> List[Any]:
    """Select nodes with degree greater than threshold.
    
    Args:
        network: Multilayer network object
        min_degree: Minimum degree threshold (exclusive - nodes must have degree > min_degree)
        layer: Optional layer to filter by
        
    Returns:
        List of nodes with degree > min_degree
    """
    if layer:
        query = f'SELECT nodes WHERE layer="{layer}" AND degree > {min_degree}'
    else:
        query = f'SELECT nodes WHERE degree > {min_degree}'
    
    result = execute_query(network, query)
    return result['nodes']


def compute_centrality_for_layer(network: Any, layer: str, 
                                 centrality: str = 'betweenness_centrality') -> Dict[Any, float]:
    """Compute centrality for all nodes in a layer.
    
    Args:
        network: Multilayer network object
        layer: Layer identifier
        centrality: Centrality measure name
        
    Returns:
        Dictionary mapping nodes to centrality values
    """
    result = execute_query(network, 
                          f'SELECT nodes WHERE layer="{layer}" COMPUTE {centrality}')
    return result['computed'].get(centrality, {})

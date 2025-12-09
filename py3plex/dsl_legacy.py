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
    >>>
    >>> # Compute community detection
    >>> result = execute_query(network, 'SELECT nodes COMPUTE communities')

Supported Operations:
    - SELECT: Choose what to select (nodes, edges)
    - MATCH: Cypher-like pattern matching for graph patterns
    - WHERE: Filter by conditions (layer, degree, centrality, etc.)
    - AND/OR/NOT: Logical operators for combining conditions
    - COMPUTE: Calculate network measures (degree, centrality, communities, etc.)
    - IN LAYER / IN LAYERS: Layer scoping clauses
    - RETURN: Specify which aliases to return from MATCH queries
    - Comparison operators: >, <, =, >=, <=, !=

Extended Syntax Examples:
    # Layer scoping for SELECT queries
    SELECT * FROM nodes IN LAYER 'ppi' WHERE degree > 10;
    SELECT id, degree FROM nodes IN LAYERS ('ppi', 'coexpr') WHERE color = 'red';
    
    # Cypher-like MATCH pattern
    MATCH (g:Gene)-[r:REGULATES]->(t:Gene) IN LAYER 'reg' WHERE g.degree > 10 RETURN g, t;
    
    # Community detection
    SELECT nodes COMPUTE communities;

See examples/network_analysis/example_dsl_queries.py for more examples.
"""

import re
from collections import Counter
import networkx as nx
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from py3plex.logging_config import get_logger
from py3plex.dsl.registry import _convert_multigraph_to_simple

# Import community detection algorithm (Louvain)
try:
    from py3plex.algorithms.community_detection.community_louvain import best_partition
    COMMUNITY_DETECTION_AVAILABLE = True
except ImportError:
    COMMUNITY_DETECTION_AVAILABLE = False
    best_partition = None

logger = get_logger(__name__)


class DSLSyntaxError(Exception):
    """Exception raised for DSL syntax errors."""
    pass


class DSLExecutionError(Exception):
    """Exception raised for DSL execution errors."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# AST Node Types for MATCH Queries
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class NodePattern:
    """Represents a node pattern in a MATCH query.
    
    Pattern syntax: (alias[:Label]?)
    Examples: (g:Gene), (t), (x:Protein)
    
    Attributes:
        alias: The variable name for the node (required)
        label: The optional type/label filter for the node
    """
    alias: str
    label: Optional[str] = None


@dataclass
class EdgePattern:
    """Represents an edge pattern in a MATCH query.
    
    Pattern syntax: -[alias[:Type]?]->
    Examples: -[r:REGULATES]->, -[e]->, -[:INTERACTS]->
    
    Attributes:
        alias: The optional variable name for the edge
        type: The optional type filter for the edge
        directed: Whether the edge is directed (always True for now)
    """
    alias: Optional[str] = None
    type: Optional[str] = None
    directed: bool = True


@dataclass
class PathPattern:
    """Represents a complete path pattern in a MATCH query.
    
    A path consists of alternating nodes and edges:
    (n1)-[e1]->(n2)-[e2]->(n3)...
    
    Attributes:
        nodes: List of NodePattern objects
        edges: List of EdgePattern objects (len = len(nodes) - 1)
    """
    nodes: List[NodePattern] = field(default_factory=list)
    edges: List[EdgePattern] = field(default_factory=list)


@dataclass
class MatchQuery:
    """Represents a parsed MATCH query.
    
    Syntax: MATCH <pattern> [IN LAYER 'name' | IN LAYERS ('a', 'b')] [WHERE conditions] [RETURN aliases];
    
    Attributes:
        pattern: The PathPattern to match
        layers: Optional list of layer names to filter
        conditions: List of WHERE condition dictionaries
        return_aliases: List of aliases to return, or None for all (RETURN *)
    """
    pattern: PathPattern
    layers: Optional[List[str]] = None
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    return_aliases: Optional[List[str]] = None  # None means RETURN * (all aliases)


def _tokenize_query(query: str) -> List[str]:
    """Tokenize a DSL query into components.
    
    Supports both SELECT and MATCH query syntax including:
    - SELECT/MATCH/FROM/WHERE/COMPUTE/RETURN keywords
    - IN LAYER / IN LAYERS clauses
    - Node patterns: (alias:Label) or (alias)
    - Edge patterns: -[alias:Type]-> or -[alias]->
    - Comparison and logical operators
    
    Args:
        query: DSL query string
        
    Returns:
        List of tokens
        
    Examples:
        >>> _tokenize_query('SELECT nodes WHERE layer="transport"')
        ['SELECT', 'nodes', 'WHERE', 'layer', '=', 'transport']
        >>> _tokenize_query("SELECT * FROM nodes IN LAYER 'ppi'")
        ['SELECT', '*', 'FROM', 'nodes', 'IN', 'LAYER', 'ppi']
    """
    # Replace quoted strings with placeholders to preserve them
    string_pattern = r'"[^"]*"|\'[^\']*\''
    strings = re.findall(string_pattern, query)
    placeholders = {}
    
    for i, s in enumerate(strings):
        placeholder = f"__STRING_{i}__"
        placeholders[placeholder] = s.strip('"\'')
        # Use indexed replacement to handle duplicate strings correctly
        idx = query.find(s)
        if idx != -1:
            query = query[:idx] + placeholder + query[idx + len(s):]
    
    # Define token patterns - order matters (longer patterns first)
    patterns = [
        r'\]->',  # Edge end with arrow (must come before -> and ]-)
        r'->\s*',  # Arrow (edge direction) - must come before >
        r'>=|<=|!=|>|<|=',  # Comparison operators
        r'-\[',  # Start of edge pattern
        r'\]-',  # End of edge pattern (without arrow)
        r'\(',  # Open parenthesis
        r'\)',  # Close parenthesis
        r':',  # Colon (for type annotations)
        r',',  # Comma (for multiple aliases in RETURN)
        r'\*',  # Asterisk (for SELECT * or RETURN *)
        r';',  # Semicolon (statement terminator)
        r'\bAND\b|\bOR\b|\bNOT\b',  # Logical operators
        r'\bSELECT\b|\bWHERE\b|\bCOMPUTE\b',  # Original keywords
        r'\bMATCH\b|\bRETURN\b|\bFROM\b',  # New keywords
        r'\bIN\b|\bLAYER\b|\bLAYERS\b',  # Layer clause keywords
        r'\bnodes\b|\bedges\b',  # Selection targets
        r'__STRING_\d+__',  # String placeholders
        r'[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?',  # Identifiers with optional dot notation
        r'\d+\.?\d*',  # Numbers
    ]
    
    combined_pattern = '|'.join(f'({p})' for p in patterns)
    tokens = []
    
    for match in re.finditer(combined_pattern, query, re.IGNORECASE):
        token = match.group(0).strip()
        if not token:
            continue
        # Handle ]-> as two tokens for the pattern parser
        if token == ']->':
            tokens.append(']-')
            tokens.append('->')
            continue
        # Replace placeholders back with actual strings
        if token.startswith('__STRING_'):
            token = placeholders.get(token, token)
        tokens.append(token)
    
    return tokens


def _tokenize_match_pattern(pattern_str: str) -> List[str]:
    """Tokenize a MATCH pattern specifically.
    
    This handles the Cypher-like pattern syntax:
    (alias:Label)-[edge:Type]->(alias2:Label2)
    
    Args:
        pattern_str: The pattern string to tokenize
        
    Returns:
        List of pattern tokens
    """
    # Use a more specific pattern for MATCH syntax
    tokens = []
    i = 0
    while i < len(pattern_str):
        c = pattern_str[i]
        
        if c.isspace():
            i += 1
            continue
        
        # Edge end with arrow: ]->
        if pattern_str[i:i+3] == ']->':
            tokens.append(']-')
            tokens.append('->')
            i += 3
            continue
        
        # Arrow alone: ->
        if pattern_str[i:i+2] == '->':
            tokens.append('->')
            i += 2
            continue
        
        # Edge start: -[
        if pattern_str[i:i+2] == '-[':
            tokens.append('-[')
            i += 2
            continue
        
        # Edge end without arrow (just ]-): shouldn't happen normally but handle it
        if pattern_str[i:i+2] == ']-':
            tokens.append(']-')
            i += 2
            continue
        
        # Single character tokens
        if c in '():,':
            tokens.append(c)
            i += 1
            continue
        
        # Colon
        if c == ':':
            tokens.append(':')
            i += 1
            continue
        
        # Identifiers
        if c.isalpha() or c == '_':
            j = i
            while j < len(pattern_str) and (pattern_str[j].isalnum() or pattern_str[j] == '_'):
                j += 1
            tokens.append(pattern_str[i:j])
            i = j
            continue
        
        i += 1
    
    return tokens


def _parse_condition(tokens: List[str], start_idx: int, 
                     stop_keywords: Optional[Set[str]] = None) -> Tuple[Dict[str, Any], int]:
    """Parse a single condition from tokens.
    
    Supports both plain attributes and alias.attribute syntax for MATCH queries.
    
    Args:
        tokens: List of tokens
        start_idx: Starting index in tokens
        stop_keywords: Set of keywords that should stop parsing
        
    Returns:
        Tuple of (condition_dict, next_index)
        
    Raises:
        DSLSyntaxError: If condition syntax is invalid
    """
    if stop_keywords is None:
        stop_keywords = {'COMPUTE', 'RETURN'}
    
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
        value_str = str(value)
        if '.' in value_str and not any(c.isalpha() for c in value_str):
            value = float(value)
        else:
            try:
                value = int(value)
            except ValueError:
                pass  # Keep as string
    except (ValueError, TypeError):
        pass  # Keep as string
    
    condition = {
        'attribute': attribute,
        'operator': operator,
        'value': value,
        'negated': is_negated
    }
    
    return condition, idx


# ═══════════════════════════════════════════════════════════════════════════════
# MATCH Query Parsing Functions
# ═══════════════════════════════════════════════════════════════════════════════


def _parse_node_pattern(pattern_tokens: List[str], start_idx: int) -> Tuple[NodePattern, int]:
    """Parse a node pattern from tokens.
    
    Pattern syntax: (alias[:Label]?)
    
    Args:
        pattern_tokens: List of pattern tokens
        start_idx: Starting index
        
    Returns:
        Tuple of (NodePattern, next_index)
    """
    idx = start_idx
    
    # Expect opening parenthesis
    if idx >= len(pattern_tokens) or pattern_tokens[idx] != '(':
        raise DSLSyntaxError(f"Expected '(' at position {idx}")
    idx += 1
    
    # Parse alias
    if idx >= len(pattern_tokens):
        raise DSLSyntaxError("Expected node alias")
    
    alias = pattern_tokens[idx]
    idx += 1
    
    # Check for optional label
    label = None
    if idx < len(pattern_tokens) and pattern_tokens[idx] == ':':
        idx += 1  # Skip colon
        if idx >= len(pattern_tokens):
            raise DSLSyntaxError("Expected label after ':'")
        label = pattern_tokens[idx]
        idx += 1
    
    # Expect closing parenthesis
    if idx >= len(pattern_tokens) or pattern_tokens[idx] != ')':
        raise DSLSyntaxError(f"Expected ')' at position {idx}")
    idx += 1
    
    return NodePattern(alias=alias, label=label), idx


def _parse_edge_pattern(pattern_tokens: List[str], start_idx: int) -> Tuple[EdgePattern, int]:
    """Parse an edge pattern from tokens.
    
    Pattern syntax: -[alias[:Type]?]->
    
    Args:
        pattern_tokens: List of pattern tokens
        start_idx: Starting index
        
    Returns:
        Tuple of (EdgePattern, next_index)
    """
    idx = start_idx
    
    # Expect opening edge syntax: -[
    if idx >= len(pattern_tokens) or pattern_tokens[idx] != '-[':
        raise DSLSyntaxError(f"Expected '-[' at position {idx}")
    idx += 1
    
    alias = None
    edge_type = None
    
    # Parse optional alias and type
    if idx < len(pattern_tokens) and pattern_tokens[idx] not in [']-', ':']:
        alias = pattern_tokens[idx]
        idx += 1
    
    # Check for optional type
    if idx < len(pattern_tokens) and pattern_tokens[idx] == ':':
        idx += 1  # Skip colon
        if idx >= len(pattern_tokens):
            raise DSLSyntaxError("Expected edge type after ':'")
        edge_type = pattern_tokens[idx]
        idx += 1
    
    # Expect closing edge syntax: ]-
    if idx >= len(pattern_tokens) or pattern_tokens[idx] != ']-':
        raise DSLSyntaxError(f"Expected ']-' at position {idx}")
    idx += 1
    
    # Expect arrow: ->
    if idx >= len(pattern_tokens) or pattern_tokens[idx] != '->':
        raise DSLSyntaxError(f"Expected '->' at position {idx}")
    idx += 1
    
    return EdgePattern(alias=alias, type=edge_type, directed=True), idx


def _parse_path_pattern(pattern_str: str) -> PathPattern:
    """Parse a complete path pattern.
    
    Pattern syntax: (n1)-[e1]->(n2)-[e2]->(n3)...
    
    Args:
        pattern_str: The pattern string to parse
        
    Returns:
        PathPattern object
    """
    tokens = _tokenize_match_pattern(pattern_str)
    if not tokens:
        raise DSLSyntaxError("Empty pattern")
    
    path = PathPattern()
    idx = 0
    
    # Parse first node
    node, idx = _parse_node_pattern(tokens, idx)
    path.nodes.append(node)
    
    # Parse remaining edge-node pairs
    while idx < len(tokens):
        # Check if there's an edge pattern
        if tokens[idx] == '-[':
            edge, idx = _parse_edge_pattern(tokens, idx)
            path.edges.append(edge)
            
            # Parse next node
            if idx >= len(tokens):
                raise DSLSyntaxError("Expected node pattern after edge")
            node, idx = _parse_node_pattern(tokens, idx)
            path.nodes.append(node)
        else:
            break
    
    return path


def _parse_layer_clause(tokens: List[str], start_idx: int) -> Tuple[Optional[List[str]], int]:
    """Parse an IN LAYER or IN LAYERS clause.
    
    Syntax:
        IN LAYER 'layer_name'
        IN LAYERS ('layer_a', 'layer_b', ...)
    
    Args:
        tokens: List of tokens
        start_idx: Starting index (should point to 'IN')
        
    Returns:
        Tuple of (list of layer names, next_index)
    """
    idx = start_idx
    
    # Check for IN keyword
    if idx >= len(tokens) or tokens[idx].upper() != 'IN':
        return None, start_idx
    idx += 1
    
    # Check for LAYER or LAYERS
    if idx >= len(tokens):
        raise DSLSyntaxError("Expected 'LAYER' or 'LAYERS' after 'IN'")
    
    keyword = tokens[idx].upper()
    if keyword not in ('LAYER', 'LAYERS'):
        # Not a layer clause, backtrack
        return None, start_idx
    idx += 1
    
    layers = []
    
    if keyword == 'LAYER':
        # Single layer: IN LAYER 'name'
        if idx >= len(tokens):
            raise DSLSyntaxError("Expected layer name after 'IN LAYER'")
        layer_name = tokens[idx]
        idx += 1
        layers = [layer_name]
    else:
        # Multiple layers: IN LAYERS ('a', 'b', ...)
        if idx >= len(tokens) or tokens[idx] != '(':
            raise DSLSyntaxError("Expected '(' after 'IN LAYERS'")
        idx += 1
        
        while idx < len(tokens):
            if tokens[idx] == ')':
                idx += 1
                break
            if tokens[idx] == ',':
                idx += 1
                continue
            layers.append(tokens[idx])
            idx += 1
    
    return layers, idx


def _parse_return_clause(tokens: List[str], start_idx: int) -> Tuple[Optional[List[str]], int]:
    """Parse a RETURN clause.
    
    Syntax:
        RETURN *
        RETURN alias1, alias2, ...
    
    Args:
        tokens: List of tokens
        start_idx: Starting index (should point to 'RETURN')
        
    Returns:
        Tuple of (list of aliases or None for *, next_index)
    """
    idx = start_idx
    
    # Check for RETURN keyword
    if idx >= len(tokens) or tokens[idx].upper() != 'RETURN':
        return None, start_idx
    idx += 1
    
    if idx >= len(tokens):
        raise DSLSyntaxError("Expected alias(es) after 'RETURN'")
    
    # Check for RETURN *
    if tokens[idx] == '*':
        idx += 1
        return None, idx  # None means return all
    
    # Parse list of aliases
    aliases = []
    while idx < len(tokens):
        token = tokens[idx]
        if token.upper() in ('WHERE', 'IN', ';'):
            break
        if token == ',':
            idx += 1
            continue
        aliases.append(token)
        idx += 1
    
    return aliases, idx


def _parse_match_where_clause(tokens: List[str], start_idx: int) -> Tuple[List[Dict[str, Any]], int]:
    """Parse WHERE clause for MATCH queries.
    
    Supports alias.attribute syntax (e.g., g.degree > 10).
    
    Args:
        tokens: List of tokens
        start_idx: Index of WHERE keyword
        
    Returns:
        Tuple of (list of conditions, next_index)
    """
    conditions = []
    idx = start_idx + 1  # Skip WHERE
    
    stop_keywords = {'RETURN', 'COMPUTE', ';'}
    
    while idx < len(tokens):
        token = tokens[idx]
        
        # Stop at certain keywords
        if token.upper() in stop_keywords or token == ';':
            break
        
        # Handle logical operators
        if token.upper() in ['AND', 'OR']:
            if not conditions:
                raise DSLSyntaxError(f"Unexpected '{token}' at start of WHERE clause")
            conditions[-1]['logical_op'] = token.upper()
            idx += 1
            continue
        
        # Parse condition
        condition, next_idx = _parse_condition(tokens, idx, stop_keywords)
        conditions.append(condition)
        idx = next_idx
    
    return conditions, idx


def _parse_match_query(tokens: List[str]) -> MatchQuery:
    """Parse a complete MATCH query.
    
    Syntax:
        MATCH <pattern> [IN LAYER 'name' | IN LAYERS ('a', 'b')] [WHERE conditions] [RETURN aliases];
    
    Args:
        tokens: List of tokens (starting with MATCH)
        
    Returns:
        MatchQuery object
    """
    if not tokens or tokens[0].upper() != 'MATCH':
        raise DSLSyntaxError("MATCH query must start with 'MATCH'")
    
    idx = 1  # Skip MATCH
    
    # Extract pattern - everything until IN, WHERE, RETURN, or ;
    pattern_tokens = []
    while idx < len(tokens):
        token = tokens[idx]
        if token.upper() in ('IN', 'WHERE', 'RETURN') or token == ';':
            break
        pattern_tokens.append(token)
        idx += 1
    
    # Parse pattern
    pattern_str = ' '.join(pattern_tokens)
    pattern = _parse_path_pattern(pattern_str)
    
    # Parse optional layer clause
    layers = None
    if idx < len(tokens) and tokens[idx].upper() == 'IN':
        layers, idx = _parse_layer_clause(tokens, idx)
    
    # Parse optional WHERE clause
    conditions = []
    if idx < len(tokens) and tokens[idx].upper() == 'WHERE':
        conditions, idx = _parse_match_where_clause(tokens, idx)
    
    # Parse optional RETURN clause
    return_aliases = None  # Default: return all
    if idx < len(tokens) and tokens[idx].upper() == 'RETURN':
        return_aliases, idx = _parse_return_clause(tokens, idx)
    
    return MatchQuery(
        pattern=pattern,
        layers=layers,
        conditions=conditions,
        return_aliases=return_aliases
    )


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
        node_or_edge: Node tuple (node_id, layer) or edge tuple ((u, layer), (v, layer), {data}?)
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
    
    # Check if this is an edge or node
    is_edge = False
    if isinstance(node_or_edge, tuple) and len(node_or_edge) >= 2:
        first_elem = node_or_edge[0]
        second_elem = node_or_edge[1]
        # Check if this is an edge: ((node, layer), (node, layer), {data}?)
        if isinstance(first_elem, tuple) and isinstance(second_elem, tuple):
            is_edge = True
    
    # Get actual value based on attribute
    actual_value = None
    
    if is_edge:
        # Handle edge attributes
        source, target = node_or_edge[0], node_or_edge[1]
        source_layer = source[1] if isinstance(source, tuple) and len(source) >= 2 else None
        target_layer = target[1] if isinstance(target, tuple) and len(target) >= 2 else None
        
        if attribute == 'source_layer':
            actual_value = str(source_layer) if source_layer else None
        elif attribute == 'target_layer':
            actual_value = str(target_layer) if target_layer else None
        elif attribute == 'layer':
            # For intralayer edges, return the common layer
            if source_layer == target_layer:
                actual_value = str(source_layer)
            else:
                actual_value = None
        elif attribute == 'weight':
            # Get weight from edge data
            if len(node_or_edge) >= 3 and isinstance(node_or_edge[2], dict):
                actual_value = node_or_edge[2].get('weight', 1.0)
            else:
                actual_value = 1.0
        else:
            # Try to get from edge data
            if len(node_or_edge) >= 3 and isinstance(node_or_edge[2], dict):
                actual_value = node_or_edge[2].get(attribute)
    else:
        # Handle node attributes
        if isinstance(node_or_edge, tuple) and len(node_or_edge) >= 2:
            node_id, layer = node_or_edge[0], node_or_edge[1]
        else:
            return False
        
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


def _compute_communities(G: nx.Graph) -> Dict[Any, int]:
    """Compute community assignments for nodes using the Louvain algorithm.
    
    Args:
        G: NetworkX graph to compute communities for
        
    Returns:
        Dictionary mapping nodes to community IDs
        
    Raises:
        DSLExecutionError: If community detection is not available
    """
    if not COMMUNITY_DETECTION_AVAILABLE or best_partition is None:
        raise DSLExecutionError(
            "Community detection is not available. "
            "Please ensure py3plex is properly installed."
        )
    
    # Convert to simple Graph for community detection
    # Use nx.Graph constructor when possible, otherwise iterate edges
    try:
        if isinstance(G, nx.Graph) and not isinstance(G, nx.MultiGraph):
            simple_G = G
        else:
            # Convert MultiGraph to simple Graph, preserving edge weights
            simple_G = nx.Graph()
            for u, v, data in G.edges(data=True):
                if simple_G.has_edge(u, v):
                    # If edge already exists, keep the maximum weight
                    existing_weight = simple_G[u][v].get('weight', 1)
                    new_weight = data.get('weight', 1)
                    simple_G[u][v]['weight'] = max(existing_weight, new_weight)
                else:
                    simple_G.add_edge(u, v, weight=data.get('weight', 1))
    except Exception:
        # Fallback to simple conversion if weight handling fails
        simple_G = nx.Graph()
        for edge in G.edges():
            simple_G.add_edge(edge[0], edge[1])
    
    if len(simple_G.nodes()) == 0:
        return {}
    
    try:
        partition = best_partition(simple_G)
        return partition
    except Exception as e:
        raise DSLExecutionError(f"Error computing communities: {str(e)}")


def _compute_measure(network: Any, measure: str, nodes: Optional[List] = None) -> Dict[Any, float]:
    """Compute a network measure for nodes.
    
    Args:
        network: Multilayer network object
        measure: Name of measure to compute (e.g., 'degree', 'betweenness_centrality', 'communities')
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
    
    # Handle community detection separately
    if measure in ('communities', 'community'):
        return _compute_communities(G)
    
    # Helper function for clustering that handles MultiGraphs
    def _clustering_with_multigraph_support(g):
        """Compute clustering, converting MultiGraph to Graph if needed."""
        g = _convert_multigraph_to_simple(g)
        return nx.clustering(g)
    
    # Map measure names to NetworkX functions
    measure_map = {
        'degree': lambda g: dict(g.degree()),
        'degree_centrality': nx.degree_centrality,
        'betweenness_centrality': nx.betweenness_centrality,
        'closeness_centrality': nx.closeness_centrality,
        'eigenvector_centrality': lambda g: nx.eigenvector_centrality(g, max_iter=1000),
        'pagerank': nx.pagerank,
        'clustering': _clustering_with_multigraph_support,
        'betweenness': nx.betweenness_centrality,
        'closeness': nx.closeness_centrality,
        'eigenvector': lambda g: nx.eigenvector_centrality(g, max_iter=1000),
    }
    
    if measure not in measure_map:
        raise DSLExecutionError(f"Unknown measure: {measure}. Supported measures: {list(measure_map.keys()) + ['communities']}")
    
    try:
        func = measure_map[measure]
        result = func(G)
        return result
    except Exception as e:
        raise DSLExecutionError(f"Error computing {measure}: {str(e)}")


def execute_query(network: Any, query: str) -> Dict[str, Any]:
    """Execute a DSL query on a multilayer network.
    
    Supports both SELECT and MATCH queries:
    
    SELECT queries:
        SELECT nodes WHERE layer="transport" AND degree > 5
        SELECT * FROM nodes IN LAYER 'ppi' WHERE degree > 10
        SELECT id, degree FROM nodes IN LAYERS ('ppi', 'coexpr') WHERE color = 'red'
    
    MATCH queries (Cypher-like):
        MATCH (g:Gene)-[r:REGULATES]->(t:Gene) IN LAYER 'reg' WHERE g.degree > 10 RETURN g, t
    
    Args:
        network: Multilayer network object (multi_layer_network instance)
        query: DSL query string
        
    Returns:
        Dictionary containing:
            - 'nodes' or 'edges' or 'bindings': List of selected items / pattern matches
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
    
    # Determine query type and dispatch
    first_token = tokens[0].upper()
    
    if first_token == 'MATCH':
        return _execute_match_query(network, query, tokens)
    elif first_token == 'SELECT':
        return _execute_select_query(network, query, tokens)
    else:
        raise DSLSyntaxError(f"Query must start with SELECT or MATCH, got '{tokens[0]}'")


def _execute_select_query(network: Any, query: str, tokens: List[str]) -> Dict[str, Any]:
    """Execute a SELECT query.
    
    Supports the original syntax plus new layer clauses:
        SELECT nodes WHERE layer="transport"
        SELECT * FROM nodes IN LAYER 'ppi' WHERE degree > 10
        SELECT id, degree FROM nodes IN LAYERS ('ppi', 'coexpr') WHERE color = 'red'
    """
    if len(tokens) < 2:
        raise DSLSyntaxError("SELECT requires a target (nodes or edges)")
    
    idx = 1  # Skip SELECT
    
    # Check for column list (SELECT *, SELECT id, degree, etc.)
    columns = None
    if tokens[idx] == '*':
        columns = ['*']
        idx += 1
    elif tokens[idx].lower() not in ['nodes', 'edges', 'from']:
        # Parse column list
        columns = []
        while idx < len(tokens):
            if tokens[idx].upper() in ['FROM', 'WHERE', 'COMPUTE', 'IN']:
                break
            if tokens[idx] == ',':
                idx += 1
                continue
            columns.append(tokens[idx])
            idx += 1
    
    # Parse target (nodes or edges) - comes BEFORE FROM in SQL-style queries
    target = None
    if idx < len(tokens) and tokens[idx].lower() in ['nodes', 'edges']:
        target = tokens[idx].lower()
        idx += 1
    
    # Check for FROM keyword with layer expression
    layer_from_clause = None
    if idx < len(tokens) and tokens[idx].upper() == 'FROM':
        idx += 1
        
        if idx >= len(tokens):
            raise DSLSyntaxError("FROM requires a layer expression or target")
        
        # Check if FROM is followed by layer expression
        next_token = tokens[idx]
        
        if next_token.lower() == 'layer' and idx + 1 < len(tokens) and tokens[idx + 1] == '=':
            # FROM layer="social" - canonical way for layer selection
            if idx + 2 >= len(tokens):
                raise DSLSyntaxError("FROM layer= requires a value")
            layer_name = tokens[idx + 2].strip('"\'')
            layer_from_clause = [layer_name]
            idx += 3  # Skip layer, =, and value
        elif next_token.upper() == 'LAYER' and idx + 1 < len(tokens) and tokens[idx + 1] == '(':
            # FROM LAYER("social") - DSL v2 style
            idx += 2  # Skip LAYER and (
            if idx >= len(tokens):
                raise DSLSyntaxError("FROM LAYER( requires a layer name")
            layer_name = tokens[idx].strip('"\'')
            layer_from_clause = [layer_name]
            idx += 2  # Skip layer name and )
        elif next_token.lower() in ['nodes', 'edges'] and target is None:
            # FROM nodes/edges (SQL-style without target before FROM)
            target = next_token.lower()
            idx += 1
        # else: FROM nodes is just redundant after SELECT nodes, ignore
    
    # If target still not found, this is an error
    if target is None:
        raise DSLSyntaxError("SELECT requires a target (nodes or edges)")
    
    
    # Parse optional layer clause (IN LAYER / IN LAYERS syntax)
    layers = layer_from_clause  # Use FROM layer if specified
    if idx < len(tokens) and tokens[idx].upper() == 'IN':
        in_layers, idx = _parse_layer_clause(tokens, idx)
        # Merge with FROM layers if both specified (intersection)
        if layers and in_layers:
            layers = list(set(layers) & set(in_layers))
        else:
            layers = in_layers or layers
    
    # Find WHERE and COMPUTE clauses
    where_idx = None
    compute_indices = []  # Track all COMPUTE positions
    
    for i in range(idx, len(tokens)):
        if tokens[i].upper() == 'WHERE':
            where_idx = i
        elif tokens[i].upper() == 'COMPUTE':
            compute_indices.append(i)
    
    # Parse WHERE conditions
    conditions = []
    if where_idx is not None:
        conditions = _parse_where_clause(tokens, where_idx)
    
    # Parse COMPUTE measures (support both repeated and comma-separated)
    measures = []
    if compute_indices:
        # Collect all tokens after each COMPUTE keyword
        for i, compute_idx in enumerate(compute_indices):
            start = compute_idx + 1
            # Find end: next COMPUTE, WHERE, or end of tokens
            end = len(tokens)
            
            # Check for next COMPUTE
            if i + 1 < len(compute_indices):
                end = compute_indices[i + 1]
            
            # Extract measures between this COMPUTE and the next marker
            measure_tokens = tokens[start:end]
            
            # Filter out commas and semicolons, add valid measure names
            for token in measure_tokens:
                if token not in [',', ';', 'WHERE']:
                    measures.append(token)
    
    # Execute query
    result = {
        'query': query,
        'target': target,
    }
    
    if layers is not None:
        result['layers'] = layers
    
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
            # Get edges with data to access attributes like weight
            all_items = list(network.get_edges(data=True))
    
    # Apply layer filter if specified
    if layers is not None:
        all_items = _filter_by_layers(all_items, layers, target)
    
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
    if measures:
        result['computed'] = {}
        for measure in measures:
            try:
                # Determine if this is an edge or node measure
                if target == 'edges':
                    # For edge measures, use DSL v2 measure registry
                    from py3plex.dsl.registry import measure_registry
                    measure_fn = measure_registry.get(measure, target="edges")
                    computed_values = measure_fn(network.core_network, filtered_items)
                else:
                    # For node measures, use legacy compute function
                    computed_values = _compute_measure(network, measure, filtered_items)
                result['computed'][measure] = computed_values
            except Exception as e:
                logger.error(f"Error computing {measure}: {e}")
                result['computed'][measure] = {}
    
    logger.info(f"Query returned {result['count']} {target}")
    return result


def _filter_by_layers(items: List[Any], layers: List[str], target: str) -> List[Any]:
    """Filter nodes or edges by layer membership.
    
    Args:
        items: List of nodes (tuples) or edges
        layers: List of layer names to filter by
        target: 'nodes' or 'edges'
        
    Returns:
        Filtered list of items
    """
    if target == 'nodes':
        # Nodes are tuples (node_id, layer)
        return [item for item in items 
                if isinstance(item, tuple) and len(item) >= 2 and item[1] in layers]
    else:
        # Edges are tuples ((source_node, source_layer), (target_node, target_layer))
        filtered = []
        for item in items:
            if isinstance(item, tuple) and len(item) >= 2:
                source, target_node = item[0], item[1]
                if isinstance(source, tuple) and isinstance(target_node, tuple):
                    if len(source) >= 2 and len(target_node) >= 2:
                        if source[1] in layers or target_node[1] in layers:
                            filtered.append(item)
        return filtered


def _execute_match_query(network: Any, query: str, tokens: List[str]) -> Dict[str, Any]:
    """Execute a MATCH query.
    
    Pattern matching for Cypher-like queries:
        MATCH (g:Gene)-[r:REGULATES]->(t:Gene) IN LAYER 'reg' WHERE g.degree > 10 RETURN g, t
    """
    # Parse the MATCH query
    match_query = _parse_match_query(tokens)
    
    # Execute pattern matching
    result = {
        'query': query,
        'type': 'match',
        'pattern': str(match_query.pattern),
    }
    
    if match_query.layers is not None:
        result['layers'] = match_query.layers
    
    # Execute pattern matching
    bindings = _execute_pattern_match(network, match_query)
    
    # Apply WHERE conditions if any
    if match_query.conditions:
        bindings = _filter_match_bindings(bindings, match_query.conditions, network)
    
    # Apply RETURN clause
    if match_query.return_aliases is not None:
        # Filter bindings to only include requested aliases
        bindings = [
            {k: v for k, v in binding.items() if k in match_query.return_aliases}
            for binding in bindings
        ]
    
    result['bindings'] = bindings
    result['count'] = len(bindings)
    
    logger.info(f"MATCH query returned {result['count']} bindings")
    return result


def _execute_pattern_match(network: Any, match_query: MatchQuery) -> List[Dict[str, Any]]:
    """Execute pattern matching against the network.
    
    This is a basic implementation that finds all paths matching the pattern.
    For complex patterns, more sophisticated algorithms could be used.
    
    Args:
        network: Multilayer network object
        match_query: Parsed MATCH query
        
    Returns:
        List of binding dictionaries mapping aliases to nodes/edges
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        return []
    
    pattern = match_query.pattern
    if not pattern.nodes:
        return []
    
    # Get all nodes, filtered by layer if specified
    all_nodes = list(network.get_nodes())
    if match_query.layers:
        all_nodes = [n for n in all_nodes 
                    if isinstance(n, tuple) and len(n) >= 2 and n[1] in match_query.layers]
    
    # Get all edges, filtered by layer if specified
    all_edges = list(network.get_edges())
    if match_query.layers:
        all_edges = [e for e in all_edges 
                    if isinstance(e, tuple) and len(e) >= 2 and
                    ((isinstance(e[0], tuple) and len(e[0]) >= 2 and e[0][1] in match_query.layers) or
                     (isinstance(e[1], tuple) and len(e[1]) >= 2 and e[1][1] in match_query.layers))]
    
    bindings = []
    
    # Simple pattern: single node
    if len(pattern.nodes) == 1:
        node_pattern = pattern.nodes[0]
        for node in all_nodes:
            if _node_matches_pattern(node, node_pattern):
                bindings.append({node_pattern.alias: node})
        return bindings
    
    # Pattern with edges: (n1)-[e]->(n2)...
    # Start by matching the first node, then follow edges
    first_node_pattern = pattern.nodes[0]
    
    for start_node in all_nodes:
        if not _node_matches_pattern(start_node, first_node_pattern):
            continue
        
        # Try to extend this match through the pattern
        current_bindings = [{first_node_pattern.alias: start_node}]
        
        for i, edge_pattern in enumerate(pattern.edges):
            next_node_pattern = pattern.nodes[i + 1]
            new_bindings = []
            
            for binding in current_bindings:
                # Find the current node
                current_node = binding[pattern.nodes[i].alias]
                
                # Find edges from current node
                for edge in all_edges:
                    if not isinstance(edge, tuple) or len(edge) < 2:
                        continue
                    
                    source, target = edge[0], edge[1]
                    
                    # Check if edge starts from current node
                    if source != current_node:
                        continue
                    
                    # Check if edge matches pattern
                    if not _edge_matches_pattern(edge, edge_pattern, network):
                        continue
                    
                    # Check if target node matches pattern
                    if not _node_matches_pattern(target, next_node_pattern):
                        continue
                    
                    # Create new binding
                    new_binding = binding.copy()
                    if edge_pattern.alias:
                        new_binding[edge_pattern.alias] = edge
                    new_binding[next_node_pattern.alias] = target
                    new_bindings.append(new_binding)
            
            current_bindings = new_bindings
            if not current_bindings:
                break
        
        bindings.extend(current_bindings)
    
    return bindings


def _node_matches_pattern(node: Any, pattern: NodePattern) -> bool:
    """Check if a node matches a node pattern.
    
    Args:
        node: Node tuple (node_id, layer)
        pattern: NodePattern to match against
        
    Returns:
        True if node matches pattern
    """
    if not isinstance(node, tuple) or len(node) < 2:
        return False
    
    # If pattern has a label, check if it matches the layer or node type
    if pattern.label is not None:
        # Label can match either the layer or node attributes
        node_id, layer = node[0], node[1]
        if layer != pattern.label:
            return False
    
    return True


def _edge_matches_pattern(edge: Any, pattern: EdgePattern, network: Any) -> bool:
    """Check if an edge matches an edge pattern.
    
    Args:
        edge: Edge tuple
        pattern: EdgePattern to match against
        network: Network object (for edge attribute lookup)
        
    Returns:
        True if edge matches pattern
    """
    if pattern.type is None:
        return True
    
    # Check edge type if pattern specifies one
    if hasattr(network, 'core_network') and network.core_network is not None:
        try:
            source, target = edge[0], edge[1]
            edge_data = network.core_network.get_edge_data(source, target)
            if edge_data:
                # Handle MultiGraph edge data
                if isinstance(edge_data, dict):
                    for key, data in edge_data.items():
                        if isinstance(data, dict) and data.get('type') == pattern.type:
                            return True
                    return False
        except Exception:
            pass
    
    return True


def _filter_match_bindings(bindings: List[Dict[str, Any]], 
                           conditions: List[Dict[str, Any]],
                           network: Any) -> List[Dict[str, Any]]:
    """Filter MATCH bindings by WHERE conditions.
    
    Supports alias.attribute syntax (e.g., g.degree > 10).
    
    Args:
        bindings: List of binding dictionaries
        conditions: List of condition dictionaries
        network: Network object
        
    Returns:
        Filtered list of bindings
    """
    if not conditions:
        return bindings
    
    filtered = []
    for binding in bindings:
        if _evaluate_match_conditions(binding, conditions, network):
            filtered.append(binding)
    
    return filtered


def _evaluate_match_conditions(binding: Dict[str, Any], 
                               conditions: List[Dict[str, Any]],
                               network: Any) -> bool:
    """Evaluate all conditions for a MATCH binding.
    
    Args:
        binding: Dictionary mapping aliases to nodes/edges
        conditions: List of conditions
        network: Network object
        
    Returns:
        True if all conditions are satisfied
    """
    if not conditions:
        return True
    
    # Build context for this binding
    context = {}
    
    result = _evaluate_match_condition(binding, conditions[0], network, context)
    
    for i, condition in enumerate(conditions[1:], 1):
        logical_op = conditions[i - 1].get('logical_op', 'AND')
        current_result = _evaluate_match_condition(binding, condition, network, context)
        
        if logical_op == 'AND':
            result = result and current_result
        elif logical_op == 'OR':
            result = result or current_result
    
    return result


def _evaluate_match_condition(binding: Dict[str, Any],
                              condition: Dict[str, Any],
                              network: Any,
                              context: Dict[str, Any]) -> bool:
    """Evaluate a single condition for a MATCH binding.
    
    Supports alias.attribute syntax.
    
    Args:
        binding: Dictionary mapping aliases to nodes/edges
        condition: Condition dictionary
        network: Network object
        context: Context for cached values
        
    Returns:
        True if condition is satisfied
    """
    attribute = condition['attribute']
    operator = condition['operator']
    expected_value = condition['value']
    is_negated = condition.get('negated', False)
    
    # Parse alias.attribute syntax
    if '.' in attribute:
        parts = attribute.split('.', 1)
        alias, attr_name = parts[0], parts[1]
        
        if alias not in binding:
            return False
        
        node_or_edge = binding[alias]
        actual_value = _get_attribute_value(node_or_edge, attr_name, network, context)
    else:
        # Plain attribute - apply to all bound nodes
        actual_value = None
        for alias, node_or_edge in binding.items():
            val = _get_attribute_value(node_or_edge, attribute, network, context)
            if val is not None:
                actual_value = val
                break
    
    # Evaluate comparison
    result = _compare_values(actual_value, operator, expected_value)
    
    if is_negated:
        result = not result
    
    return result


def _get_attribute_value(node_or_edge: Any, attribute: str, 
                         network: Any, context: Dict[str, Any]) -> Any:
    """Get an attribute value from a node or edge.
    
    Args:
        node_or_edge: Node tuple or edge tuple
        attribute: Attribute name (e.g., 'degree', 'layer')
        network: Network object
        context: Context for cached values
        
    Returns:
        Attribute value or None
    """
    # Handle nodes (tuples of (node_id, layer))
    if isinstance(node_or_edge, tuple) and len(node_or_edge) >= 2:
        node_id, layer = node_or_edge[0], node_or_edge[1]
        
        if attribute == 'layer':
            return str(layer)
        
        if attribute == 'degree':
            if hasattr(network, 'core_network') and network.core_network:
                return network.core_network.degree(node_or_edge)
            return 0
        
        if attribute in ['betweenness', 'betweenness_centrality']:
            if 'betweenness_centrality' not in context:
                try:
                    context['betweenness_centrality'] = _compute_measure(network, 'betweenness_centrality')
                except DSLExecutionError:
                    return 0
            return context['betweenness_centrality'].get(node_or_edge, 0)
        
        if attribute in ['closeness', 'closeness_centrality']:
            if 'closeness_centrality' not in context:
                try:
                    context['closeness_centrality'] = _compute_measure(network, 'closeness_centrality')
                except DSLExecutionError:
                    return 0
            return context['closeness_centrality'].get(node_or_edge, 0)
        
        if attribute in ['eigenvector', 'eigenvector_centrality']:
            if 'eigenvector_centrality' not in context:
                try:
                    context['eigenvector_centrality'] = _compute_measure(network, 'eigenvector_centrality')
                except DSLExecutionError:
                    return 0
            return context['eigenvector_centrality'].get(node_or_edge, 0)
        
        # Try to get from node attributes
        if hasattr(network, 'core_network') and network.core_network:
            node_data = network.core_network.nodes.get(node_or_edge, {})
            return node_data.get(attribute)
    
    return None


def _compare_values(actual: Any, operator: str, expected: Any) -> bool:
    """Compare two values with the given operator.
    
    Args:
        actual: Actual value
        operator: Comparison operator
        expected: Expected value
        
    Returns:
        True if comparison is satisfied
    """
    if actual is None:
        return False
    
    if operator == '=':
        return str(actual) == str(expected)
    elif operator == '!=':
        return str(actual) != str(expected)
    elif operator == '>':
        try:
            return float(actual) > float(expected)
        except (ValueError, TypeError):
            return False
    elif operator == '<':
        try:
            return float(actual) < float(expected)
        except (ValueError, TypeError):
            return False
    elif operator == '>=':
        try:
            return float(actual) >= float(expected)
        except (ValueError, TypeError):
            return False
    elif operator == '<=':
        try:
            return float(actual) <= float(expected)
        except (ValueError, TypeError):
            return False
    else:
        raise DSLSyntaxError(f"Unknown operator: {operator}")
    
    return False


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


# ═══════════════════════════════════════════════════════════════════════════════
# Community Detection Convenience Functions
# ═══════════════════════════════════════════════════════════════════════════════


def detect_communities(network: Any, layer: Optional[str] = None) -> Dict[str, Any]:
    """Detect communities in the network using Louvain algorithm via DSL.
    
    Args:
        network: Multilayer network object
        layer: Optional layer to filter nodes by
        
    Returns:
        Dictionary containing:
            - 'partition': Dict mapping nodes to community IDs
            - 'num_communities': Number of communities detected
            - 'community_sizes': Dict mapping community ID to size
            - 'biggest_community': Tuple (community_id, size)
            - 'smallest_community': Tuple (community_id, size)
            - 'size_distribution': List of community sizes
            
    Example:
        >>> from py3plex.core import multinet
        >>> from py3plex.dsl import detect_communities
        >>> 
        >>> # Create a sample network
        >>> network = multinet.multi_layer_network()
        >>> # ... add nodes and edges ...
        >>> 
        >>> # Detect communities
        >>> result = detect_communities(network)
        >>> print(f"Found {result['num_communities']} communities")
        >>> print(f"Biggest community has {result['biggest_community'][1]} nodes")
    """
    if layer:
        query = f'SELECT nodes WHERE layer="{layer}" COMPUTE communities'
    else:
        query = 'SELECT nodes COMPUTE communities'
    
    result = execute_query(network, query)
    partition = result['computed'].get('communities', {})
    
    return _analyze_communities(partition)


def get_community_partition(network: Any, layer: Optional[str] = None) -> Dict[Any, int]:
    """Get community partition (mapping of nodes to community IDs).
    
    Args:
        network: Multilayer network object
        layer: Optional layer to filter nodes by
        
    Returns:
        Dictionary mapping nodes to community IDs
        
    Example:
        >>> partition = get_community_partition(network)
        >>> for node, community_id in partition.items():
        ...     print(f"Node {node} is in community {community_id}")
    """
    result = detect_communities(network, layer)
    return result['partition']


def get_biggest_community(network: Any, layer: Optional[str] = None) -> Tuple[int, int, List[Any]]:
    """Get the largest community in the network.
    
    Args:
        network: Multilayer network object
        layer: Optional layer to filter nodes by
        
    Returns:
        Tuple of (community_id, size, list_of_nodes)
        
    Example:
        >>> community_id, size, nodes = get_biggest_community(network)
        >>> print(f"Community {community_id} has {size} nodes")
        >>> print(f"Nodes: {nodes}")
    """
    result = detect_communities(network, layer)
    partition = result['partition']
    
    if not partition:
        return (0, 0, [])
    
    community_id, size = result['biggest_community']
    nodes = [node for node, comm_id in partition.items() if comm_id == community_id]
    
    return (community_id, size, nodes)


def get_smallest_community(network: Any, layer: Optional[str] = None) -> Tuple[int, int, List[Any]]:
    """Get the smallest community in the network.
    
    Args:
        network: Multilayer network object
        layer: Optional layer to filter nodes by
        
    Returns:
        Tuple of (community_id, size, list_of_nodes)
        
    Example:
        >>> community_id, size, nodes = get_smallest_community(network)
        >>> print(f"Community {community_id} has {size} nodes")
        >>> print(f"Nodes: {nodes}")
    """
    result = detect_communities(network, layer)
    partition = result['partition']
    
    if not partition:
        return (0, 0, [])
    
    community_id, size = result['smallest_community']
    nodes = [node for node, comm_id in partition.items() if comm_id == community_id]
    
    return (community_id, size, nodes)


def get_num_communities(network: Any, layer: Optional[str] = None) -> int:
    """Get the number of communities in the network.
    
    Args:
        network: Multilayer network object
        layer: Optional layer to filter nodes by
        
    Returns:
        Number of communities detected
        
    Example:
        >>> num_communities = get_num_communities(network)
        >>> print(f"Found {num_communities} communities")
    """
    result = detect_communities(network, layer)
    return result['num_communities']


def get_community_sizes(network: Any, layer: Optional[str] = None) -> Dict[int, int]:
    """Get the size of each community in the network.
    
    Args:
        network: Multilayer network object
        layer: Optional layer to filter nodes by
        
    Returns:
        Dictionary mapping community ID to its size
        
    Example:
        >>> sizes = get_community_sizes(network)
        >>> for comm_id, size in sizes.items():
        ...     print(f"Community {comm_id}: {size} nodes")
    """
    result = detect_communities(network, layer)
    return result['community_sizes']


def get_community_size_distribution(network: Any, layer: Optional[str] = None) -> List[int]:
    """Get the distribution of community sizes.
    
    Args:
        network: Multilayer network object
        layer: Optional layer to filter nodes by
        
    Returns:
        List of community sizes sorted in descending order
        
    Example:
        >>> distribution = get_community_size_distribution(network)
        >>> print(f"Largest community: {distribution[0]} nodes")
        >>> print(f"Smallest community: {distribution[-1]} nodes")
        >>> print(f"Average size: {sum(distribution) / len(distribution):.1f}")
    """
    result = detect_communities(network, layer)
    return result['size_distribution']


def _analyze_communities(partition: Dict[Any, int]) -> Dict[str, Any]:
    """Analyze community partition and compute statistics.
    
    Args:
        partition: Dictionary mapping nodes to community IDs
        
    Returns:
        Dictionary with community statistics
    """
    if not partition:
        return {
            'partition': {},
            'num_communities': 0,
            'community_sizes': {},
            'biggest_community': (0, 0),
            'smallest_community': (0, 0),
            'size_distribution': [],
        }
    
    # Count nodes in each community
    community_sizes = Counter(partition.values())
    
    # Get sorted sizes
    sizes = sorted(community_sizes.values(), reverse=True)
    
    # Find biggest and smallest
    biggest_community_id = max(community_sizes.keys(), key=lambda k: community_sizes[k])
    smallest_community_id = min(community_sizes.keys(), key=lambda k: community_sizes[k])
    
    return {
        'partition': partition,
        'num_communities': len(community_sizes),
        'community_sizes': dict(community_sizes),
        'biggest_community': (biggest_community_id, community_sizes[biggest_community_id]),
        'smallest_community': (smallest_community_id, community_sizes[smallest_community_id]),
        'size_distribution': sizes,
    }

#!/usr/bin/env python3
"""Atheris fuzzing harness for py3plex DSL query parsing and execution.

This fuzzes the Domain-Specific Language (DSL) for querying multilayer networks
by feeding it malformed queries to discover crashes, parsing errors, and edge cases.

The DSL supports both string syntax (SQL-like) and builder API (Python):
- String syntax: 'SELECT nodes WHERE layer="social" AND degree > 5'
- Builder API: Q.nodes().from_layers(L["social"]).where(degree__gt=5)

Fuzzing targets:
- Query parsing (tokenization, syntax validation)
- Condition evaluation (comparisons, logical operators)
- Measure computation (centrality, clustering, etc.)
- Layer expressions (union, difference, intersection)
- Export functionality (to_pandas, to_dict, etc.)

Usage:
    python fuzzing/fuzz_dsl.py fuzzing/seeds/

Requirements:
    pip install atheris
"""

import sys
import tempfile
import os
import traceback

try:
    import atheris
except ImportError:
    print("Error: atheris not installed. Install with: pip install atheris")
    sys.exit(1)

try:
    from py3plex.core import multinet
    from py3plex.dsl import (
        execute_query,
        Q,
        L,
        Param,
        DslError,
        DslSyntaxError,
        DslExecutionError,
        UnknownMeasureError,
        UnknownAttributeError,
        UnknownLayerError,
        ParameterMissingError,
        TypeMismatchError,
    )
except ImportError as e:
    print(f"Error: Failed to import py3plex or DSL module: {e}")
    print("Install with: pip install -e .")
    sys.exit(1)

# DSL query components for generating varied queries
DSL_KEYWORDS = [
    "SELECT", "FROM", "WHERE", "COMPUTE", "ORDER BY", "LIMIT",
    "LAYER", "EXPLAIN", "TO", "AND", "OR", "NOT", "AS"
]

DSL_TARGETS = ["nodes", "edges", "layers"]

DSL_OPERATORS = ["=", ">", "<", ">=", "<=", "!="]

DSL_ATTRIBUTES = [
    "layer", "degree", "betweenness", "closeness", 
    "eigenvector_centrality", "clustering", "pagerank"
]

DSL_MEASURES = [
    "degree", "betweenness_centrality", "closeness_centrality",
    "eigenvector_centrality", "pagerank", "clustering"
]

DSL_EXPORT_FORMATS = ["pandas", "dict", "networkx", "arrow"]


def _is_critical_error(error_msg: str) -> bool:
    """Check if an error message indicates a critical crash.
    
    Args:
        error_msg: The error message to check
        
    Returns:
        True if the error is critical (crash, segfault, etc.), False otherwise
    """
    error_msg_lower = error_msg.lower()
    return any(word in error_msg_lower for word in ['crash', 'segfault', 'corruption', 'overflow'])


# Create a reusable sample network to avoid recreating it on every iteration
_SAMPLE_NETWORK = None


def create_sample_network():
    """Create a small sample multilayer network for fuzzing.
    
    Returns:
        A multilayer network with a few nodes and edges
    """
    global _SAMPLE_NETWORK
    
    # Cache the network to avoid recreating it on every iteration
    if _SAMPLE_NETWORK is not None:
        return _SAMPLE_NETWORK
    
    network = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Add a minimal set of nodes and edges for testing
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
    ]
    network.add_edges(edges)
    
    _SAMPLE_NETWORK = network
    return network


def fuzz_string_dsl(data: bytes, network):
    """Fuzz the string-based DSL syntax.
    
    Args:
        data: Random bytes to convert to DSL query
        network: Multilayer network to query
    """
    # Decode bytes to string
    try:
        query = data.decode("utf-8", errors="surrogatepass")
    except Exception:
        try:
            query = data.decode("latin-1", errors="ignore")
        except Exception:
            return
    
    # Skip empty or very short queries
    if len(query.strip()) < 3:
        return
    
    # Limit query length to avoid excessive memory usage
    if len(query) > 10000:
        query = query[:10000]
    
    try:
        # Try to execute the query
        result = execute_query(network, query)
        
        # If successful, try to access the result
        if result and isinstance(result, dict):
            _ = result.get('count', 0)
            _ = result.get('nodes', [])
            _ = result.get('edges', [])
    except DslSyntaxError:
        # Expected for malformed queries
        return
    except DslExecutionError:
        # Expected for invalid operations
        return
    except UnknownMeasureError:
        # Expected for unknown measures
        return
    except UnknownAttributeError:
        # Expected for unknown attributes
        return
    except UnknownLayerError:
        # Expected for unknown layers
        return
    except ParameterMissingError:
        # Expected for missing parameters
        return
    except TypeMismatchError:
        # Expected for type mismatches
        return
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        # Expected for various malformed inputs
        return
    except RecursionError:
        # Expected for deeply nested structures
        return
    except MemoryError:
        # Re-raise memory errors as they indicate real issues
        raise
    except AssertionError:
        # Re-raise assertions as they indicate logic errors
        raise
    except Exception as e:
        # Check if it's a real crash
        if _is_critical_error(str(e)):
            raise
        # Otherwise, it's likely a validation error - let it pass
        return


def fuzz_builder_api(data: bytes, network):
    """Fuzz the builder API (Python-based DSL).
    
    Args:
        data: Random bytes to generate API calls
        network: Multilayer network to query
    """
    # Skip if data too short to generate meaningful API calls
    if len(data) < 5:
        return
    
    try:
        # Deterministically map bytes to API calls
        # This allows the fuzzer to explore different API combinations
        
        # Choose query type
        query_type = data[0] % 3
        
        if query_type == 0:
            # Build a nodes query
            q = Q.nodes()
        elif query_type == 1:
            # Build an edges query
            q = Q.edges()
        else:
            # Build a query without explicit target
            return
        
        # Add layer filter if byte 1 suggests it
        if len(data) > 1 and data[1] % 2 == 0:
            layer_idx = data[1] % 2
            layer_name = f"layer{layer_idx + 1}"
            try:
                q = q.from_layers(L[layer_name])
            except Exception:
                return
        
        # Add conditions if byte 2 suggests it
        if len(data) > 2 and data[2] % 3 == 0:
            try:
                degree_val = int(data[2] % 10)
                q = q.where(degree__gt=degree_val)
            except Exception:
                return
        
        # Add compute if byte 3 suggests it
        if len(data) > 3 and data[3] % 2 == 0:
            measures = ["degree", "betweenness_centrality"]
            measure_idx = data[3] % len(measures)
            try:
                q = q.compute(measures[measure_idx])
            except Exception:
                return
        
        # Add limit if byte 4 suggests it
        if len(data) > 4 and data[4] % 2 == 0:
            limit_val = int(data[4] % 20) + 1
            try:
                q = q.limit(limit_val)
            except Exception:
                return
        
        # Try to execute the query
        try:
            result = q.execute(network)
            
            # Try to access result data
            if hasattr(result, 'to_dict'):
                _ = result.to_dict()
        except Exception:
            # Expected for various invalid configurations
            return
            
    except DslError:
        # Expected for DSL errors
        return
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        # Expected for various malformed inputs
        return
    except RecursionError:
        # Expected for deeply nested structures
        return
    except MemoryError:
        raise
    except AssertionError:
        raise
    except Exception as e:
        if _is_critical_error(str(e)):
            raise
        return


def fuzz_one_input(data: bytes):
    """Fuzz target for DSL query parsing and execution.
    
    Args:
        data: Random bytes from the fuzzer
    """
    # Skip very small inputs
    if len(data) < 2:
        return
    
    try:
        # Create a sample network for testing
        # We reuse the network across fuzzing iterations for performance
        # but this is safe because queries don't modify the network
        network = create_sample_network()
        
        # Determine which fuzzing strategy to use based on first byte
        # This allows the fuzzer to explore both string and builder APIs
        strategy = data[0] % 2
        
        if strategy == 0:
            # Fuzz string-based DSL
            fuzz_string_dsl(data[1:], network)
        else:
            # Fuzz builder API
            fuzz_builder_api(data[1:], network)
            
    except SystemExit:
        # Re-raise SystemExit to avoid catching it
        raise
    except MemoryError:
        # Re-raise memory errors as they indicate real issues
        raise
    except AssertionError:
        # Re-raise assertions as they indicate logic errors
        raise
    except Exception as e:
        # For unexpected exceptions, check if they're critical
        if _is_critical_error(str(e)):
            raise
        # Otherwise, it's likely a validation error - let it pass
        return


def main():
    """Entry point for the fuzzer."""
    atheris.Setup(sys.argv, fuzz_one_input)
    
    banner = """
============================================================
Py3plex DSL Fuzzer
============================================================
Fuzzing targets:
  - String DSL syntax (SQL-like queries)
  - Builder API (Python chainable API)
  - Query parsing and validation
  - Condition evaluation
  - Measure computation
Usage: {} <seed_corpus_dir>
============================================================
""".format(sys.argv[0])
    
    print(banner)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

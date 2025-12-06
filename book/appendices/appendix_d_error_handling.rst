Appendix D: Error Handling and Exception Hierarchy
===================================================

This appendix documents py3plex's exception classes and error handling conventions.

Exception Hierarchy
-------------------

py3plex defines a hierarchy of exceptions for different error categories:

.. code-block:: text

    Py3plexException (base)
    ├── ValidationError
    │   ├── InvalidNetworkError
    │   ├── InvalidLayerError
    │   └── InvalidNodeError
    ├── IOError
    │   ├── FileFormatError
    │   ├── FileNotFoundError
    │   └── SerializationError
    ├── DSLError
    │   ├── QuerySyntaxError
    │   ├── QueryExecutionError
    │   └── UnsupportedFeatureError
    ├── AlgorithmError
    │   ├── ConvergenceError
    │   └── InsufficientDataError
    └── ConfigurationError

Base Exception
--------------

.. code-block:: python

    class Py3plexException(Exception):
        """Base exception for all py3plex errors."""
        pass

All py3plex exceptions inherit from this base class, allowing users to catch any library error:

.. code-block:: python

    from py3plex.exceptions import Py3plexException
    
    try:
        result = some_py3plex_operation()
    except Py3plexException as e:
        print(f"py3plex error: {e}")

Validation Errors
-----------------

InvalidNetworkError
~~~~~~~~~~~~~~~~~~~

Raised when a network is in an invalid state:

.. code-block:: python

    from py3plex.exceptions import InvalidNetworkError
    
    # Example: Empty network
    if network.number_of_nodes() == 0:
        raise InvalidNetworkError("Cannot compute metrics on empty network")

**Common causes:**

* Empty network (no nodes or edges)
* Disconnected graph when algorithm requires connected
* Directed graph when undirected expected (or vice versa)

InvalidLayerError
~~~~~~~~~~~~~~~~~

Raised when referencing a nonexistent layer:

.. code-block:: python

    from py3plex.exceptions import InvalidLayerError
    
    if layer_name not in network.get_layers():
        raise InvalidLayerError(f"Layer '{layer_name}' does not exist")

**Common causes:**

* Typo in layer name
* Layer removed after reference created
* Case sensitivity mismatch

InvalidNodeError
~~~~~~~~~~~~~~~~

Raised when referencing a nonexistent node:

.. code-block:: python

    from py3plex.exceptions import InvalidNodeError
    
    if node not in network.core_network:
        raise InvalidNodeError(f"Node {node} not found in network")

I/O Errors
----------

FileFormatError
~~~~~~~~~~~~~~~

Raised when file format is invalid or unsupported:

.. code-block:: python

    from py3plex.exceptions import FileFormatError
    
    try:
        network.load_network("data.xyz", input_type="xyz")
    except FileFormatError as e:
        print(f"Unsupported format: {e}")

**Common causes:**

* Unrecognized file extension
* Malformed file content
* Missing required fields in CSV/JSON

SerializationError
~~~~~~~~~~~~~~~~~~

Raised during read/write operations:

.. code-block:: python

    from py3plex.exceptions import SerializationError
    
    try:
        write(network, "output.arrow")
    except SerializationError as e:
        print(f"Failed to serialize: {e}")

DSL Errors
----------

QuerySyntaxError
~~~~~~~~~~~~~~~~

Raised for invalid DSL query syntax:

.. code-block:: python

    from py3plex.dsl import execute_query
    from py3plex.exceptions import QuerySyntaxError
    
    try:
        result = execute_query(network, 'SELECT nodes WHRE degree > 5')  # Typo
    except QuerySyntaxError as e:
        print(f"Query syntax error: {e}")
        # Suggestion: "Did you mean 'WHERE'?"

**Common causes:**

* Typos in keywords (WHRE instead of WHERE)
* Missing quotes around layer names
* Invalid comparison operators

QueryExecutionError
~~~~~~~~~~~~~~~~~~~

Raised when query execution fails:

.. code-block:: python

    from py3plex.exceptions import QueryExecutionError
    
    try:
        result = execute_query(network, 'SELECT nodes COMPUTE nonexistent_measure')
    except QueryExecutionError as e:
        print(f"Query execution failed: {e}")

**Common causes:**

* Referencing nonexistent measures
* Applying measure to unsuitable graph (e.g., eigenvector centrality on disconnected graph)
* Resource limits exceeded

UnsupportedFeatureError
~~~~~~~~~~~~~~~~~~~~~~~

Raised when using experimental or unimplemented features:

.. code-block:: python

    from py3plex.exceptions import UnsupportedFeatureError
    
    try:
        result = Q.edges().where(weight__gt=0.5).execute(network)
    except UnsupportedFeatureError as e:
        print(f"Feature not yet supported: {e}")

Algorithm Errors
----------------

ConvergenceError
~~~~~~~~~~~~~~~~

Raised when iterative algorithms fail to converge:

.. code-block:: python

    from py3plex.exceptions import ConvergenceError
    
    try:
        centrality = compute_eigenvector_centrality(network, max_iter=100)
    except ConvergenceError as e:
        print(f"Algorithm did not converge: {e}")

InsufficientDataError
~~~~~~~~~~~~~~~~~~~~~

Raised when there's not enough data for analysis:

.. code-block:: python

    from py3plex.exceptions import InsufficientDataError
    
    if network.number_of_nodes() < 3:
        raise InsufficientDataError("Need at least 3 nodes for community detection")

Configuration Errors
--------------------

ConfigurationError
~~~~~~~~~~~~~~~~~~

Raised for invalid configuration or parameters:

.. code-block:: python

    from py3plex.exceptions import ConfigurationError
    
    if beta <= 0 or gamma <= 0:
        raise ConfigurationError("SIR parameters beta and gamma must be positive")

Error Handling Best Practices
------------------------------

Catch Specific Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~

Prefer catching specific exceptions over generic ones:

.. code-block:: python

    # Good: Specific exception handling
    from py3plex.exceptions import InvalidLayerError
    
    try:
        result = Q.nodes().from_layers(L["social"]).execute(network)
    except InvalidLayerError:
        print("Layer 'social' not found. Available layers:", network.get_layers())
    
    # Avoid: Generic exception (too broad)
    try:
        result = Q.nodes().from_layers(L["social"]).execute(network)
    except Exception as e:  # Too generic
        print(f"Something went wrong: {e}")

Provide Context
~~~~~~~~~~~~~~~

Include helpful context in error messages:

.. code-block:: python

    # Good: Helpful context
    if layer_name not in network.get_layers():
        available = ", ".join(network.get_layers())
        raise InvalidLayerError(
            f"Layer '{layer_name}' not found. Available layers: {available}"
        )
    
    # Less helpful
    if layer_name not in network.get_layers():
        raise InvalidLayerError(f"Invalid layer")

Validation at Entry Points
~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate inputs early:

.. code-block:: python

    def compute_centrality(network, measure='degree'):
        """Compute node centrality."""
        # Validate early
        if network.number_of_nodes() == 0:
            raise InvalidNetworkError("Cannot compute centrality on empty network")
        
        if measure not in ['degree', 'betweenness', 'closeness']:
            raise ValueError(f"Unknown measure: {measure}")
        
        # Proceed with computation
        ...

Clean Resource Cleanup
~~~~~~~~~~~~~~~~~~~~~~

Use context managers for resources:

.. code-block:: python

    # Good: Automatic cleanup
    from py3plex.io import read
    
    try:
        graph = read('network.arrow')
        # Process graph
    except IOError as e:
        print(f"Failed to read file: {e}")
    finally:
        # Resources automatically cleaned up

Error Messages Guidelines
-------------------------

1. **Be specific:** State what went wrong and why
2. **Suggest fixes:** Offer alternatives when possible
3. **Include context:** Show relevant values (layer names, node counts, etc.)
4. **Be concise:** One sentence explanation, then details if needed

**Examples:**

.. code-block:: python

    # Good error message
    raise InvalidLayerError(
        f"Layer 'socail' not found. Did you mean 'social'? "
        f"Available layers: {', '.join(network.get_layers())}"
    )
    
    # Good error message
    raise InsufficientDataError(
        f"Community detection requires at least 3 nodes, but network has only "
        f"{network.number_of_nodes()}"
    )
    
    # Less helpful
    raise InvalidLayerError("Layer error")  # Too vague

Logging
-------

py3plex uses Python's logging module:

.. code-block:: python

    import logging
    
    # Configure logging level
    logging.basicConfig(level=logging.INFO)
    
    # py3plex will log warnings and errors
    network.load_network("data.edgelist")  # Logs any warnings

Available log levels:

* ``DEBUG`` — Detailed information for debugging
* ``INFO`` — General information
* ``WARNING`` — Recoverable issues
* ``ERROR`` — Serious problems
* ``CRITICAL`` — Fatal errors

Summary
-------

**Exception hierarchy:**

* Base: ``Py3plexException``
* Categories: Validation, I/O, DSL, Algorithm, Configuration

**Best practices:**

1. Catch specific exceptions
2. Provide helpful context in messages
3. Validate early
4. Suggest fixes when possible
5. Use logging for non-fatal issues

**Example usage:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.exceptions import InvalidLayerError, Py3plexException
    
    try:
        network = multinet.multi_layer_network()
        network.load_network("data.edgelist")
        
        result = Q.nodes().from_layers(L["social"]).execute(network)
        
    except InvalidLayerError as e:
        print(f"Layer not found: {e}")
    except Py3plexException as e:
        print(f"py3plex error: {e}")

[For error recovery strategies in workflows → Chapter 10]

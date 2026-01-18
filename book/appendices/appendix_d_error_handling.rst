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

**See also:** :ref:`advanced-dsl-chapter` for error recovery strategies in workflows

Pedagogical Error Messages (DSL v2)
------------------------------------

Py3plex DSL v2 implements Rust-style pedagogical error messages that help users understand and fix issues quickly. Errors include:

1. **What the user likely intended**
2. **Why the operation failed**
3. **1-2 corrected query examples**
4. **Common pitfall notes (when applicable)**

Error Philosophy
~~~~~~~~~~~~~~~~

**Guidance over Obscurity:**

Traditional error messages say "what went wrong". Py3plex errors explain "what to do about it".

.. code-block:: text

    # Traditional error (not helpful)
    Error: Invalid syntax
    
    # Pedagogical error (helpful)
    DslSyntaxError: Cannot call .where() after .end_grouping()
    
    💭 You probably wanted to: Filter nodes before grouping
    
    ❌ Why this failed: After .end_grouping(), the query context 
       returns to ungrouped state. The .where() clause filters the 
       entire result, not individual groups.
    
    ✅ Corrected examples:
      1. Q.nodes().where(degree__gt=3).per_layer().top_k(5)
      2. Q.nodes().per_layer().filter_within_groups(degree__gt=3)
    
    ⚠️  Common pitfall: Grouping operations (.per_layer(), .group_by())
       create a new context. Apply filters before grouping for clarity.

**Core Principles:**

* **Actionable**: Always suggest a fix, never just complain
* **Contextual**: Explain *why* in terms of DSL/multilayer semantics
* **Educational**: Help users understand the underlying concepts
* **Concise**: Keep examples short and focused

Enhanced DSL Error Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**DslSyntaxError** — Enhanced with pedagogical context

Raised for invalid DSL syntax or query structure:

.. code-block:: python

    from py3plex.dsl.errors import DslSyntaxError
    
    # Example: Invalid method chaining
    try:
        Q.nodes().execute(net).where(degree__gt=3)  # Execute too early
    except DslSyntaxError as e:
        print(e)
    # Output:
    # DslSyntaxError: Cannot call .where() on QueryResult
    #
    # 💭 You probably wanted to: Filter before executing
    #
    # ❌ Why this failed: .execute() returns a QueryResult object,
    #    which is immutable. Query building methods like .where()
    #    must be called before .execute().
    #
    # ✅ Corrected examples:
    #   1. Q.nodes().where(degree__gt=3).execute(net)
    #   2. result = Q.nodes().execute(net); df = result.to_pandas().query("degree > 3")

**DslExecutionError** — Enhanced with runtime context

Raised when query execution fails due to runtime conditions:

.. code-block:: python

    from py3plex.dsl.errors import DslExecutionError
    
    # Example: Missing required metric
    try:
        Q.nodes().where(betweenness__gt=0.1).execute(net)  # Betweenness not computed
    except DslExecutionError as e:
        print(e)
    # Output:
    # DslExecutionError: Cannot filter on 'betweenness' (not computed)
    #
    # 💭 You probably wanted to: Compute betweenness before filtering
    #
    # ❌ Why this failed: The .where() clause references 'betweenness',
    #    but this metric hasn't been computed yet. Autocompute is
    #    disabled for filters to prevent silent expensive operations.
    #
    # ✅ Corrected examples:
    #   1. Q.nodes().compute("betweenness_centrality").where(betweenness__gt=0.1)
    #   2. Q.nodes().where(degree__gt=5).compute("betweenness_centrality")
    #
    # ⚠️  Common pitfall: Some metrics (degree) are cheap and autocomputed.
    #    Expensive metrics (betweenness, closeness) require explicit .compute()

**MultilayerSemanticError** — Multilayer-specific guidance

Raised for common multilayer network semantic issues:

.. code-block:: python

    from py3plex.dsl.errors import MultilayerSemanticError
    
    # Example: Node replica confusion
    try:
        # User expects 100 unique nodes, gets 300 node replicas
        result = Q.nodes().execute(multilayer_net)
        assert result.count == 100  # Fails if network has 3 layers
    except AssertionError:
        raise MultilayerSemanticError(
            "Node count mismatch: Expected 100, got 300",
            semantic_issue="Counting node replicas instead of physical nodes",
            multilayer_context=(
                "In multilayer networks, each physical node appears in multiple "
                "layers as a 'node replica'. Q.nodes() returns ALL replicas, "
                "not unique physical nodes."
            ),
            examples=[
                "To count physical nodes: len(set(n[0] for n in result.items))",
                "To work per-layer: Q.nodes().per_layer().execute(net)",
                "To get single layer: Q.nodes().from_layers(L['social']).execute(net)"
            ]
        )

Example: Before and After
~~~~~~~~~~~~~~~~~~~~~~~~~

**Before** (traditional error):

.. code-block:: text

    AttributeError: 'QueryResult' object has no attribute 'coverage'
    
    # User is confused: What's coverage? Where do I use it?

**After** (pedagogical error):

.. code-block:: text

    DslExecutionError: .coverage() requires active grouping
    
    💭 You probably wanted to: Apply coverage after .per_layer()
    
    ❌ Why this failed: The .coverage() method filters items based
       on their presence across groups. You must create groups first
       with .per_layer() or .group_by().
    
    ✅ Corrected examples:
      1. Q.nodes().per_layer().top_k(5, "degree").end_grouping().coverage(mode="all")
      2. Q.nodes().from_layers(L["*"]).per_layer().compute("degree").coverage(mode="any")
    
    ⚠️  Common pitfall: .coverage() is a post-grouping filter, not a
       pre-grouping filter. It answers "which items appear across groups?"

Using Pedagogical Errors Effectively
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**As a user:**

1. **Read the entire error** — Don't stop at the first line
2. **Try the corrected examples** — They're tested and known to work
3. **Learn the pitfall** — Understand the underlying concept
4. **Check documentation** — Errors reference relevant sections

**As a developer:**

When raising DSL errors, provide rich context:

.. code-block:: python

    from py3plex.dsl.errors import DslExecutionError
    
    # Good: Rich pedagogical error
    raise DslExecutionError(
        f"Cannot filter on '{field}' (not computed)",
        intent=f"Compute {field} before filtering",
        why_failed=(
            f"The .where() clause references '{field}', but this metric "
            f"hasn't been computed yet. Autocompute is disabled for filters."
        ),
        examples=[
            f"Q.nodes().compute('{field}').where({field}__gt=threshold)",
            f"Q.nodes().where(degree__gt=5).compute('{field}')"  # Filter first
        ],
        pitfall=(
            "Some metrics (degree) are cheap and autocomputed. "
            "Expensive metrics require explicit .compute()"
        )
    )

Error Recovery Patterns
~~~~~~~~~~~~~~~~~~~~~~~

**Pattern 1: Inspect-Fix-Retry**

.. code-block:: python

    try:
        result = Q.nodes().where(betweenness__gt=0.1).execute(net)
    except DslExecutionError as e:
        print(e)  # Read pedagogical message
        
        # Apply suggested fix
        result = (
            Q.nodes()
             .compute("betweenness_centrality")
             .where(betweenness__gt=0.1)
             .execute(net)
        )

**Pattern 2: Catch-and-Adapt**

.. code-block:: python

    from py3plex.dsl.errors import MultilayerSemanticError
    
    try:
        # Assume single-layer semantics
        result = Q.nodes().compute("degree").execute(net)
        avg_degree = sum(result.attributes["degree"].values()) / result.count
    except (KeyError, MultilayerSemanticError):
        # Adapt to multilayer semantics
        result = (
            Q.nodes()
             .per_layer()
             .compute("degree")
             .aggregate("mean")  # Per-layer averages
             .execute(net)
        )

**Pattern 3: Defensive Query Building**

.. code-block:: python

    # Check capabilities before building complex queries
    if len(net.get_layers()) > 1:
        # Multilayer network — use layer-aware query
        result = (
            Q.nodes()
             .per_layer()
             .compute("degree")
             .top_k(10, "degree")
             .end_grouping()
             .coverage(mode="any")  # Nodes in any layer
             .execute(net)
        )
    else:
        # Single-layer network — use simple query
        result = (
            Q.nodes()
             .compute("degree")
             .order_by("-degree")
             .limit(10)
             .execute(net)
        )

Summary: Error Handling Philosophy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Traditional approach:**

* Error: "What went wrong"
* User: Googles error message
* Result: Frustrated user, support ticket

**Py3plex pedagogical approach:**

* Error: "What went wrong" + "Why" + "How to fix" + "Learn more"
* User: Reads error, applies fix
* Result: Self-sufficient user, learned a concept

**Key benefits:**

1. **Faster debugging**: Users fix issues without leaving their editor
2. **Better learning**: Errors teach multilayer network concepts
3. **Reduced support**: Common mistakes are explained inline
4. **Higher quality code**: Users learn best practices from error messages

**See also:**

* DSL Builder API (Chapter 9) for query construction patterns
* Advanced Queries (Chapter 10) for error recovery in workflows
* Multilayer Basics (Chapter 2) for core multilayer network concepts

Layer Set Algebra
=================

The Layer Set Algebra feature provides a first-class, composable system for
selecting and manipulating layer sets in multilayer networks. Instead of manually
specifying lists of layers, you can use set-theoretic operations to express
complex layer selections.

Why Layer Set Algebra?
-----------------------

In multilayer network analysis, you often need to:

- Select "all layers except the coupling layer"
- Combine biological layers for aggregate analysis
- Find the intersection of layers where a node appears
- Reuse layer group definitions across multiple queries

The Layer Set Algebra makes these operations expressive, composable, and safe.

Quick Start
-----------

Basic Operations
^^^^^^^^^^^^^^^^

.. code-block:: python

   from py3plex.dsl import LayerSet, L, Q
   
   # Create layer sets
   social = LayerSet("social")
   work = LayerSet("work")
   
   # Union: layers in either social OR work
   both = social | work
   
   # Intersection: layers in both social AND work
   shared = social & work
   
   # Difference: layers in social but NOT in work
   social_only = social - work
   
   # Complement: all layers EXCEPT social
   not_social = ~social

String Expressions
^^^^^^^^^^^^^^^^^^

For convenience, you can write layer expressions as strings:

.. code-block:: python

   # Parse from string
   layers = LayerSet.parse("* - coupling")
   
   # Or use L[...] syntax (auto-detects expressions)
   layers = L["* - coupling"]
   layers = L["(ppi | gene) & disease"]
   layers = L["social | work | hobby"]

Integration with Queries
^^^^^^^^^^^^^^^^^^^^^^^^

Use layer sets in any DSL query:

.. code-block:: python

   # Query nodes from all layers except coupling
   result = (
       Q.nodes()
        .from_layers(L["* - coupling"])
        .compute("degree")
        .execute(network)
   )
   
   # Complex layer selection
   result = (
       Q.nodes()
        .from_layers(L["(social | work) & ~coupling"])
        .where(degree__gt=5)
        .execute(network)
   )

Set Operations
--------------

Union: A | B
^^^^^^^^^^^^

The union operation combines layers from multiple sets.

.. code-block:: python

   # Select nodes from social OR work layers
   layers = L["social | work"]
   # Equivalent to:
   layers = LayerSet("social") | LayerSet("work")

**ASCII Venn Diagram:**

.. code-block:: text

      ┌─────────┐     ┌─────────┐
      │ Social  │     │  Work   │
      │    ┌────┴─────┴────┐    │
      │    │   RESULT      │    │
      └────┴────────────────┴────┘
         A | B = {social, work}

Intersection: A & B
^^^^^^^^^^^^^^^^^^^

The intersection operation selects only layers present in both sets.

.. code-block:: python

   # Nodes that appear in both layer A AND layer B
   layers = L["layerA & layerB"]

**ASCII Venn Diagram:**

.. code-block:: text

      ┌─────────┐     ┌─────────┐
      │    A    │     │    B    │
      │    ┌────┼─────┼────┐    │
      │    │    │ RES │    │    │
      └────┴────┼─────┼────┴────┘
                A & B

Difference: A - B
^^^^^^^^^^^^^^^^^

The difference operation removes layers in B from A.

.. code-block:: python

   # All layers except coupling
   layers = L["* - coupling"]
   
   # Social layers but not bots
   layers = L["social - bots"]

**ASCII Venn Diagram:**

.. code-block:: text

      ┌─────────┐     ┌─────────┐
      │    A    │     │    B    │
      │  ┌──────┼─────┤         │
      │  │ RES  │     │         │
      └──┴──────┼─────┴─────────┘
         A - B = A without B

Complement: ~A
^^^^^^^^^^^^^^

The complement operation returns all layers except those in A.

.. code-block:: python

   # Everything except social layer
   layers = ~LayerSet("social")
   
   # Equivalent to:
   layers = L["* - social"]

**ASCII Venn Diagram:**

.. code-block:: text

      ┌─────────────────────────┐
      │     All Layers (*)      │
      │                         │
      │  ┌───────┐              │
      │  │   A   │    RESULT    │
      │  └───────┘              │
      └─────────────────────────┘
         ~A = * - A

Named Layer Groups
------------------

Define reusable layer groups for cleaner queries:

.. code-block:: python

   from py3plex.dsl import LayerSet, L, Q
   
   # Define a named group
   bio_layers = LayerSet("ppi") | LayerSet("gene") | LayerSet("disease")
   LayerSet.define_group("bio", bio_layers)
   
   # Or use the convenience method
   L.define("core", L["social | work | email"])
   
   # Use the group in queries
   result = Q.nodes().from_layers(LayerSet("bio")).execute(network)
   
   # Groups can be combined with other operations
   result = Q.nodes().from_layers(L["bio & core"]).execute(network)
   
   # List all defined groups
   groups = L.list_groups()
   print(groups)  # {'bio': LayerSet(...), 'core': LayerSet(...)}

Operator Precedence
-------------------

Layer expressions follow standard set theory precedence:

1. **Complement** (~) - highest precedence
2. **Intersection** (&)
3. **Difference** (-)
4. **Union** (|) - lowest precedence

Use parentheses for clarity or to override precedence:

.. code-block:: python

   # Without parentheses: parsed as A & (B | C)
   expr1 = L["A & B | C"]
   
   # With parentheses: explicit grouping
   expr2 = L["(A & B) | C"]
   expr3 = L["A & (B | C)"]

Real-World Examples
-------------------

Example 1: Biological Networks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Analyze protein interactions while excluding coupling layers:

.. code-block:: python

   from py3plex.dsl import Q, L, LayerSet
   
   # Define biological layer groups
   L.define("bio", L["ppi | gene | disease"])
   
   # Find high-degree nodes in biological layers only
   result = (
       Q.nodes()
        .from_layers(LayerSet("bio") - LayerSet("coupling"))
        .where(degree__gt=10)
        .compute("betweenness_centrality")
        .order_by("betweenness_centrality", desc=True)
        .limit(20)
        .execute(network)
   )
   
   print(result.to_pandas())

Example 2: Social Networks
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Compare centrality across different social contexts:

.. code-block:: python

   # Define layer groups for different social contexts
   L.define("online", L["facebook | twitter | linkedin"])
   L.define("offline", L["work | school | hobby"])
   
   # Compute centrality in online layers
   online_centrality = (
       Q.nodes()
        .from_layers(LayerSet("online"))
        .compute("pagerank")
        .execute(network)
   ).to_pandas()
   
   # Compute centrality in offline layers
   offline_centrality = (
       Q.nodes()
        .from_layers(LayerSet("offline"))
        .compute("pagerank")
        .execute(network)
   ).to_pandas()
   
   # Find nodes with high centrality in both contexts
   # (merge and filter the DataFrames)

Example 3: Transportation Networks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Analyze robustness by excluding specific infrastructure:

.. code-block:: python

   # Simulate failure scenarios
   scenarios = [
       ("full_network", L["*"]),
       ("no_air", L["* - air_travel"]),
       ("no_rail", L["* - rail"]),
       ("road_only", L["road"]),
       ("multi_modal", L["road | rail"]),
   ]
   
   results = {}
   for name, layers in scenarios:
       result = (
           Q.nodes()
            .from_layers(layers)
            .compute("betweenness_centrality")
            .execute(network)
       ).to_pandas()
       
       results[name] = {
           "avg_betweenness": result["betweenness_centrality"].mean(),
           "max_betweenness": result["betweenness_centrality"].max(),
           "node_count": len(result),
       }
   
   import pandas as pd
   df_results = pd.DataFrame(results).T
   print(df_results)

Introspection and Debugging
----------------------------

Layer sets provide introspection tools to understand what they represent:

Resolution
^^^^^^^^^^

See which layers a LayerSet resolves to:

.. code-block:: python

   layers = L["* - coupling"]
   
   # Resolve against a network
   resolved = layers.resolve(network)
   print(resolved)  # {'social', 'work', 'hobby'}

Explanation
^^^^^^^^^^^

Get a human-readable explanation of the layer expression:

.. code-block:: python

   layers = L["(ppi | gene) & disease"]
   print(layers.explain())
   
   # Output:
   # LayerSet:
   #   intersection(
   #     union(
   #       layer("ppi"),
   #       layer("gene")
   #     ),
   #     layer("disease")
   #   )

With Network Resolution
^^^^^^^^^^^^^^^^^^^^^^^

Combine explanation with network resolution:

.. code-block:: python

   layers = L["* - coupling"]
   print(layers.explain(network))
   
   # Output:
   # LayerSet:
   #   difference(
   #     all_layers("*"),
   #     layer("coupling")
   #   )
   # → resolved to: {'hobby', 'social', 'work'}

Comparison: Old vs New Syntax
------------------------------

**Old Style (Still Supported):**

.. code-block:: python

   # Manual layer list
   result = Q.nodes().from_layers(L["social"] + L["work"]).execute(network)
   
   # Multiple separate queries
   layers = ["social", "work", "hobby"]
   results = []
   for layer in layers:
       if layer != "coupling":
           result = Q.nodes().from_layers(L[layer]).execute(network)
           results.append(result)

**New Style (Recommended):**

.. code-block:: python

   # Expressive layer algebra
   result = Q.nodes().from_layers(L["social | work"]).execute(network)
   
   # Single query with filtering
   result = (
       Q.nodes()
        .from_layers(L["* - coupling"])
        .execute(network)
   )

Why Layer Set Algebra Matters
------------------------------

For Multilayer Networks
^^^^^^^^^^^^^^^^^^^^^^^

Multilayer networks have a unique challenge: layer selection is a first-class
operation, not an afterthought. Traditional graph analysis tools don't provide
built-in support for layer algebra, forcing users to write imperative code
with loops and conditionals.

Layer Set Algebra brings the following benefits:

1. **Expressiveness**: Complex layer selections become one-liners
2. **Composability**: Combine layer expressions with set operations
3. **Reusability**: Define named groups once, use everywhere
4. **Safety**: Late evaluation with validation at execution time
5. **Maintainability**: Clear, declarative code is easier to understand

Algebraic Properties
^^^^^^^^^^^^^^^^^^^^

Layer Set Algebra follows standard set theory laws:

- **Idempotence**: A | A = A, A & A = A
- **Commutativity**: A | B = B | A, A & B = B & A
- **Associativity**: (A | B) | C = A | (B | C)
- **Distributivity**: A & (B | C) = (A & B) | (A & C)
- **De Morgan's Laws**: ~(A | B) = ~A & ~B, ~(A & B) = ~A | ~B
- **Complement**: A | ~A = *, A & ~A = ∅

These properties enable query optimization and reasoning about layer selections.

API Reference
-------------

LayerSet Class
^^^^^^^^^^^^^^

.. code-block:: python

   class LayerSet:
       """Represents an unevaluated layer expression."""
       
       def __init__(self, name_or_expr: Union[str, LayerExpr])
           """Create from layer name or expression AST."""
       
       def __or__(self, other: LayerSet) -> LayerSet:
           """Union: self | other."""
       
       def __and__(self, other: LayerSet) -> LayerSet:
           """Intersection: self & other."""
       
       def __sub__(self, other: LayerSet) -> LayerSet:
           """Difference: self - other."""
       
       def __invert__(self) -> LayerSet:
           """Complement: ~self."""
       
       def resolve(self, network, *, strict=False, warn_empty=True) -> Set[str]:
           """Resolve expression to actual layer names."""
       
       def explain(self, network=None) -> str:
           """Generate human-readable explanation."""
       
       @staticmethod
       def parse(expr_str: str) -> LayerSet:
           """Parse layer expression from string."""
       
       @staticmethod
       def define_group(name: str, layer_set: LayerSet) -> None:
           """Define a named layer group."""
       
       @staticmethod
       def list_groups() -> Dict[str, LayerSet]:
           """List all defined groups."""
       
       @staticmethod
       def clear_groups() -> None:
           """Clear all defined groups."""

L Proxy
^^^^^^^

The ``L`` proxy provides convenient syntax for creating layer expressions:

.. code-block:: python

   # Simple layer name (backward compatible)
   L["social"]  # Returns LayerExprBuilder
   
   # Expression string (auto-detected)
   L["* - coupling"]  # Returns LayerSet
   L["social | work"]  # Returns LayerSet
   
   # Define named group
   L.define("bio", LayerSet("ppi") | LayerSet("gene"))
   
   # List groups
   groups = L.list_groups()
   
   # Clear groups
   L.clear_groups()

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**1. Empty Layer Set Warning**

.. code-block:: python

   layers = L["nonexistent"]
   result = layers.resolve(network)
   # UserWarning: Layer expression resolved to empty set

**Solution**: Check layer names, use ``warn_empty=False`` to suppress, or use ``strict=True`` to raise an error instead.

**2. Unknown Layer Error**

.. code-block:: python

   layers = L["typo_layer"]
   result = layers.resolve(network, strict=True)
   # UnknownLayerError: Layer 'typo_layer' not found

**Solution**: Verify layer names with ``network.layers`` or ``network.get_layers()``.

**3. Syntax Error in Expression**

.. code-block:: python

   layers = L["social &"]  # Missing right operand
   # DslSyntaxError: Unexpected end of expression

**Solution**: Check expression syntax, ensure all operators have operands.

Best Practices
^^^^^^^^^^^^^^

1. **Use Named Groups** for complex layer sets you'll reuse
2. **Prefer String Expressions** for readability: ``L["* - coupling"]``
3. **Use Complement** instead of listing all other layers: ``~LayerSet("exclude")``
4. **Document Layer Groups** with comments explaining their purpose
5. **Test Layer Resolution** with ``.explain(network)`` before running expensive queries

See Also
--------

- :doc:`../how-to/query_with_dsl` - DSL query basics
- :doc:`../how-to/query_zoo` - Query examples and patterns
- :doc:`dsl_reference` - Complete DSL API reference

.. note::
   Layer Set Algebra is available in py3plex DSL v2.1+. It's fully backward
   compatible with existing layer expressions.

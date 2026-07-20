Multilayer Networks in 2 Minutes
================================

A **multilayer network** represents systems where entities can be connected through multiple types of relationships simultaneously.

The Core Idea
-------------

In the real world, relationships are rarely uniform. Consider a group of researchers:

* They **co-author papers** (collaboration network)
* They **cite each other** (citation network)
* They **attend conferences** together (social network)
* They may **share funding** (grant network)

A single-layer network captures only one of these relationships. A multilayer network keeps every relationship type separate while linking the same entity across layers.

Visual Intuition
----------------

.. code-block:: text

    Single-layer network (e.g., only co-authorship):
    
    Alice --- Bob --- Carol
              |
            David
    
    Multilayer network (co-authorship + citations):
    
    Layer 1 (Co-authorship):
    Alice --- Bob --- Carol
              |
            David
    
    Layer 2 (Citations):
    Alice --> Bob --> Carol
              ↓
            David
    
    Inter-layer connections:
    Alice in Layer 1 ↔ Alice in Layer 2 (same person)

Key Concepts
------------

Keep these quick definitions in mind while you read the rest.

**Layers**  
Each layer represents one relationship type (e.g., friendship, collaboration, family).

**Node-layer pairs**  
Every node is represented per layer. In py3plex, ``('Alice', 'friends')`` and ``('Alice', 'work')`` are distinct node-layer pairs that can be linked. Counts in py3plex statistics refer to these pairs, not just the unique entity names.

**Intra-layer edges**  
Connections within a single layer (e.g., Alice friends with Bob).

**Inter-layer edges**  
Connections between layers, typically tying the same entity across layers (e.g., Alice in the friendship layer ↔ Alice in the collaboration layer). They can also connect different entity types when modeling interactions between layers.

Types of Multilayer Networks
----------------------------

**Multiplex networks**

* Same nodes across all layers
* Different edge types per layer
* Example: Social media (same users, different platforms)

**Heterogeneous networks**

* Different node types in different layers
* Example: Author-Paper-Venue networks

**Temporal networks**

* Layers represent time slices
* Same nodes and edge types, but edges appear/disappear over time
* Example: Communication networks over days/weeks

Why Multilayer Matters
----------------------

**Information is lost when flattening**

If you merge all layers into a single network, you lose critical information:

* Which type of relationship connects two nodes?
* Are communities consistent across layers or layer-specific?
* How do different relationship types interact?

**New properties emerge**

Multilayer networks have properties that don't exist in single-layer networks:

* **Node versatility:** How many layers a node participates in, and whether its role shifts by layer.
* **Layer correlation:** Whether connections in layer A are predictive of connections in layer B.
* **Multilayer communities:** Groups that span multiple relationship types.
* **Multiplexity:** Number of different relationship types between two nodes.

Real-World Impact
-----------------

**Example: Disease spread**

In epidemic modeling, people interact through:

* Household contacts (high transmission rate)
* Workplace contacts (medium rate, large reach)
* Social gatherings (variable)

A single-layer model that averages these interactions will give incorrect predictions. A multilayer model preserves the structure and transmission dynamics of each contact type.

**Example: Social influence**

A person might be influential on Twitter (many followers) but not on LinkedIn (few connections). Flattening these into a single "social network" loses this nuance.

Quick Example in Code
---------------------

.. code-block:: python

    from py3plex.core import multinet
    
    # Create multilayer network
    network = multinet.multi_layer_network()
    
    # Add edges in different layers
    network.add_edges([
        # Friendship layer (source, source_layer, target, target_layer, weight)
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        
        # Collaboration layer
        ['Alice', 'work', 'Carol', 'work', 1],
        ['Carol', 'work', 'David', 'work', 1],
    ], input_type="list")
    
    # Analyze (counts are for node-layer pairs)
    stats = network.basic_stats()
    print(f"Layers: {len(network.get_layers())}")
    print(f"Nodes: {stats['nodes']}")
    print(f"Edges: {stats['edges']}")

**Expected output:**

.. code-block:: text

    Layers: 2
    Nodes: 8  (4 unique entities × 2 layers)
    Edges: 4

When to Use Multilayer Analysis?
---------------------------------

Use multilayer networks when:

*  You have **multiple relationship types** between entities
*  The **type of relationship matters** for your analysis
*  You want to **preserve layer-specific structure**
*  You're studying **cross-layer effects** (e.g., how Twitter activity affects LinkedIn connections)

Stick with single-layer when:

*  All relationships are of the same type
*  Relationship type doesn't affect your analysis
*  You only care about aggregate connectivity

Next Steps
----------

* **Try it yourself:** :doc:`../getting_started/tutorial_10min`
* **Deeper theory:** :doc:`../concepts/multilayer_networks_101`
* **See how py3plex works:** :doc:`../concepts/py3plex_core_model`
* **Start analyzing:** :doc:`../how-to/load_and_build_networks`
